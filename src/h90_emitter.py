"""Exact 25-offset R=300 m (3.0 px) CELF lazy-greedy submodular dot allocator
and leak-free baseline emitters for Lane H90.
"""

from __future__ import annotations

import heapq

import numpy as np
from scipy import ndimage as ndi

# Exact positive support of DrivenData's 300 m triangular kernel on a 100 m grid:
# k(d) = max(1 - d / 3.0, 0). Every cell in [-2..2] x [-2..2] has hypot <= sqrt(8) < 3.0,
# while any |dy| >= 3 or |dx| >= 3 has k(d) == 0.0.
_YY, _XX = np.mgrid[-2:3, -2:3].astype(np.float32)
KERNEL_5X5: np.ndarray = np.maximum(0.0, 1.0 - np.hypot(_YY, _XX) / 3.0).astype(np.float32)


def celf_submodular_emit(
    prob_2d: np.ndarray,
    eligible_2d: np.ndarray,
    *,
    target_dots: int,
    min_spacing_px: float = 2.05,
    min_marginal_gain: float = 1e-7,
    pool_multiplier: int = 7,
) -> np.ndarray:
    """Select up to ``target_dots`` unit binary dots maximizing expected 300 m kernel TP coverage.

    Uses Minoux (1978) / Leskovec et al. (2007) CELF lazy-greedy evaluation on the
    monotone submodular objective:
        F(S) = sum_{g} prob_2d[g] * max_{x in S} k(d(x, g))
    subject to ``x in eligible_2d`` and pairwise spacing ``>= min_spacing_px``.
    """
    prob = np.where(np.isfinite(prob_2d) & (prob_2d > 0.0), prob_2d, 0.0).astype(np.float32)
    elig = np.asarray(eligible_2d, dtype=bool)
    H, W = prob.shape
    out = np.zeros((H, W), dtype=np.float32)
    if target_dots <= 0 or not elig.any() or not (prob > 0).any():
        return out

    init_gain = ndi.correlate(prob, KERNEL_5X5, mode="constant", cval=0.0)
    cand_flat = np.flatnonzero(elig & (init_gain > min_marginal_gain))
    if cand_flat.size == 0:
        return out

    pool_cap = max(int(target_dots) * int(pool_multiplier), 60_000)
    if cand_flat.size > pool_cap:
        gains_cand = init_gain.ravel()[cand_flat]
        part = np.argpartition(gains_cand, -pool_cap)[-pool_cap:]
        cand_flat = cand_flat[part]

    gains_init = init_gain.ravel()[cand_flat]
    # Tie-break deterministically by flat pixel index
    heap: list[tuple[float, int]] = [(-float(g), int(idx)) for g, idx in zip(gains_init.tolist(), cand_flat.tolist())]
    heapq.heapify(heap)

    p_pad = np.pad(prob, 2, mode="constant", constant_values=0.0)
    c_pad = np.zeros((H + 4, W + 4), dtype=np.float32)
    blocked = np.zeros((H, W), dtype=bool)

    r_blk = int(np.floor(min_spacing_px))
    by, bx = np.mgrid[-r_blk : r_blk + 1, -r_blk : r_blk + 1]
    blk_mask = (by * by + bx * bx) < (min_spacing_px * min_spacing_px)
    blk_dy = by[blk_mask].tolist()
    blk_dx = bx[blk_mask].tolist()

    selected = 0
    while heap and selected < target_dots:
        neg_g, flat_idx = heapq.heappop(heap)
        r = flat_idx // W
        c = flat_idx % W
        if blocked[r, c]:
            continue

        # Recompute exact marginal gain against current 300 m kernel coverage
        p_win = p_pad[r : r + 5, c : c + 5]
        c_win = c_pad[r : r + 5, c : c + 5]
        diff = KERNEL_5X5 - c_win
        gain = float(np.sum(p_win * np.where(diff > 0.0, diff, 0.0)))
        if gain <= min_marginal_gain:
            continue

        # Skip any already-blocked entries sitting at the top before comparing
        while heap and blocked[heap[0][1] // W, heap[0][1] % W]:
            heapq.heappop(heap)

        next_upper = -heap[0][0] if heap else -1.0
        if gain >= next_upper - 1e-12:
            out[r, c] = 1.0
            np.maximum(c_win, KERNEL_5X5, out=c_win)
            selected += 1
            for dy, dx in zip(blk_dy, blk_dx):
                nr, nc = r + dy, c + dx
                if 0 <= nr < H and 0 <= nc < W:
                    blocked[nr, nc] = True
        else:
            heapq.heappush(heap, (-gain, flat_idx))

    return out


def greedy_spacing_emit(
    score_2d: np.ndarray,
    eligible_2d: np.ndarray,
    *,
    target_dots: int,
    min_spacing_px: float = 2.8,
) -> np.ndarray:
    """Classical rank-ordered greedy disk NMS emitter (used for Comparator C1)."""
    elig = np.asarray(eligible_2d, dtype=bool) & np.isfinite(score_2d)
    H, W = score_2d.shape
    out = np.zeros((H, W), dtype=np.float32)
    if target_dots <= 0 or not elig.any():
        return out

    cand_flat = np.flatnonzero(elig)
    pool_cap = min(cand_flat.size, max(target_dots * 8, 80_000))
    vals = score_2d.ravel()[cand_flat]
    if cand_flat.size > pool_cap:
        part = np.argpartition(vals, -pool_cap)[-pool_cap:]
        cand_flat = cand_flat[part]
        vals = vals[part]
    order = cand_flat[np.argsort(-vals, kind="mergesort")]

    blocked = np.zeros((H, W), dtype=bool)
    r_blk = int(np.ceil(min_spacing_px))
    by, bx = np.mgrid[-r_blk : r_blk + 1, -r_blk : r_blk + 1]
    blk_mask = (by * by + bx * bx) <= (min_spacing_px * min_spacing_px)
    blk_dy = by[blk_mask].tolist()
    blk_dx = bx[blk_mask].tolist()

    selected = 0
    for flat_idx in order.tolist():
        if selected >= target_dots:
            break
        r = flat_idx // W
        c = flat_idx % W
        if blocked[r, c]:
            continue
        out[r, c] = 1.0
        selected += 1
        for dy, dx in zip(blk_dy, blk_dx):
            nr, nc = r + dy, c + dx
            if 0 <= nr < H and 0 <= nc < W:
                blocked[nr, nc] = True
    return out


def random_isolated_emit(
    eligible_2d: np.ndarray,
    *,
    target_dots: int,
    min_spacing_px: float = 2.05,
    seed: int = 9001,
) -> np.ndarray:
    """Count-matched uniform random off-catalogue isolated dot baseline (Comparator C0)."""
    rng = np.random.default_rng(seed)
    noise = np.zeros(eligible_2d.shape, dtype=np.float32)
    elig = np.asarray(eligible_2d, dtype=bool)
    noise[elig] = rng.random(int(elig.sum()), dtype=np.float32)
    return greedy_spacing_emit(noise, elig, target_dots=target_dots, min_spacing_px=min_spacing_px)
