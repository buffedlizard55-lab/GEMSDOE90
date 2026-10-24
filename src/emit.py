"""DTI-optimal dot emission.

The official metric is  DTI = T / (0.2 T + 0.2 (S - M) + 0.8 |G|)  with
T = sum_g max_x p(x) k(d(x,g)).  Three consequences drive this emitter:

1. **Unit mass is optimal.**  Scaling every prediction by gamma scales T, S and
   M but not the constant 0.8|G|, so DTI increases monotonically in gamma:
   emit p = 1 where you emit at all, p = 0 elsewhere (bang-bang).
2. **T is a max, not a sum** — overlapping dots waste credit, so placement is a
   maximum-coverage problem (monotone submodular ⇒ greedy is within 1-1/e).
3. **A dot pays only above a break-even.**  d(DTI)/d(dot) > 0 iff its marginal
   coverage credit exceeds 0.2 theta/(1-0.2 theta) (1 - m).  At theta = 0.28 that
   is 0.059 credit — so the budget is *endogenous*, not a style choice, and the
   spacing adapts: dense where the hidden-fault density is high, absent where it
   is not.

`greedy_emit` therefore returns the whole selection order plus the exact
cumulative (T, M) curve, and the caller picks the budget at the curve's maximum.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import convolve

R_PX = 3.0


def kernel_offsets() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    off = [(dy, dx) for dy in range(-3, 4) for dx in range(-3, 4)
           if 1.0 - np.hypot(dy, dx) / R_PX > 0]
    dy = np.array([o[0] for o in off], dtype="int32")
    dx = np.array([o[1] for o in off], dtype="int32")
    kv = np.array([1.0 - np.hypot(a, b) / R_PX for a, b in off], dtype="float64")
    return dy, dx, kv


def kernel_patch() -> np.ndarray:
    yy, xx = np.mgrid[-3:4, -3:4]
    return np.maximum(0.0, 1.0 - np.hypot(yy, xx) / R_PX).astype("float32")


@dataclass
class Emission:
    rows: np.ndarray
    cols: np.ndarray
    gain: np.ndarray          # marginal coverage credit of each dot, in order
    m: np.ndarray             # per-dot matched-kernel expectation (1 - exp(-u))
    cum_T: np.ndarray
    cum_M: np.ndarray
    n_considered: int
    min_pool_gain: float      # smallest initial gain kept in the pool


def greedy_emit(pi: np.ndarray, candidates: np.ndarray, n_max: int,
                pool_size: int = 700_000, forbid_within: np.ndarray | None = None,
                overlap_cap: float | None = None) -> Emission:
    """Greedy maximum-coverage emission against the expected hidden-fault field.

    pi            float32 raster: expected hidden-fault density per pixel
    candidates    bool raster: pixels allowed to carry a dot
    n_max         maximum number of dots to select
    pool_size     keep this many best-initial-gain candidates (gains only shrink
                  under greedy, so a candidate outside the pool can never be
                  selected while the pool's floor is below the stopping gain —
                  the floor is returned for verification)
    forbid_within bool raster of 'already covered by a registry raster' pixels,
                  used only for the lane/overlap quota
    overlap_cap   maximum share of emitted dots allowed to fall on
                  `forbid_within` (duplicate-lane guard)
    """
    pi = np.asarray(pi, dtype="float32")
    cand = np.asarray(candidates, dtype=bool)
    h, w = pi.shape
    u = convolve(pi, kernel_patch(), mode="constant", cval=0.0)  # = sum_x pi k
    flat_idx = np.flatnonzero(cand.ravel())
    gains0 = u.ravel()[flat_idx]
    if flat_idx.size > pool_size:
        keep = np.argpartition(gains0, -pool_size)[-pool_size:]
        flat_idx, gains0 = flat_idx[keep], gains0[keep]
    min_pool_gain = float(gains0.min()) if gains0.size else 0.0

    heap = [(-float(g), int(i)) for g, i in zip(gains0, flat_idx)]
    heapq.heapify(heap)

    cov = np.zeros(pi.shape, dtype="float32")
    dy, dx, kv = kernel_offsets()
    pif = pi
    taken = np.zeros(h * w, dtype=bool)
    ov = forbid_within if forbid_within is not None else None

    rows, cols, gl, ml = [], [], [], []
    n_ov = 0
    while heap and len(rows) < n_max:
        neg, idx = heapq.heappop(heap)
        if taken[idx]:
            continue
        r, c = divmod(idx, w)
        rr = r + dy
        cc = c + dx
        ok = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
        rr, cc, kk = rr[ok], cc[ok], kv[ok]
        add = kk - cov[rr, cc]
        np.maximum(add, 0.0, out=add)
        g = float((pif[rr, cc] * add).sum())
        if heap and g < -heap[0][0] - 1e-12:
            heapq.heappush(heap, (-g, idx))
            continue
        if overlap_cap is not None and ov is not None and ov[r, c]:
            if n_ov + 1 > overlap_cap * (len(rows) + 1):
                taken[idx] = True          # drop: would breach the lane quota
                continue
            n_ov += 1
        cov[rr, cc] = np.maximum(cov[rr, cc], kk)
        taken[idx] = True
        rows.append(r)
        cols.append(c)
        gl.append(g)
        ml.append(1.0 - float(np.exp(-u[r, c])))

    gain = np.array(gl)
    m = np.array(ml)
    return Emission(rows=np.array(rows, dtype="int32"), cols=np.array(cols, dtype="int32"),
                    gain=gain, m=m, cum_T=np.cumsum(gain), cum_M=np.cumsum(m),
                    n_considered=int(flat_idx.size), min_pool_gain=min_pool_gain)


def dti_curve(em: Emission, n_truth: float) -> np.ndarray:
    """Predicted DTI after the first n dots, for n = 1..len(em.rows)."""
    n = np.arange(1, em.cum_T.size + 1, dtype="float64")
    den = 0.2 * em.cum_T + 0.2 * (n - em.cum_M) + 0.8 * n_truth
    return em.cum_T / np.maximum(den, 1e-12)


def dots_to_raster(em: Emission, shape: tuple[int, int], n: int) -> np.ndarray:
    out = np.zeros(shape, dtype="float32")
    out[em.rows[:n], em.cols[:n]] = 1.0
    return out
