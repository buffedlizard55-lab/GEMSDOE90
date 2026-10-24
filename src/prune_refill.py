"""Credit-aware fixed-count refill for AXIS = PRUNE.

Why this module exists
----------------------
Every recorded PRUNE candidate deletes the R0 dots inside a catalogue collar and then
restores the *exact* parent dot count by refilling from the pinned H19-5 support. The
inherited refill policy is the lineage's recovered 8-connected FIFO-BFS thinning order --
a traversal tie-break, not a metric. Measured on the recorded files (IR90-12): 98.7-99.5 %
of refill dots land within 3 px of a dot that was already retained (median 1.00 px), i.e.
they add the `0.2*(S-M)` penalty while supplying almost no fresh kernel credit, and the
replacement sits a median 845-888 px from the dot it replaces.

This module replaces that ordering with the metric's own marginal rule, evaluated
truth-free on the same H19-5 proxy support the parent lineage uses:

    marginal credit of a new unit dot at q  =
        sum_{offsets} max(0, k(offset) * support[q+offset] - credit[q+offset])
        + max(0, support[q] - credit[q])            (the dot's own pixel)

where `credit` is the current best kernel credit at each pixel from the dots already
placed (assumption A2: T = sum over truth of the best dot's credit) and `support` is the
H19-5 proxy truth. The greedy picks the pool pixel with the largest marginal credit, adds
it, and updates the credit field exactly inside the kernel -- so later picks see the
updated map. Ties break on flat raster index, so the result is deterministic.

Nothing here reads a competition score, a leaderboard or a test label. The catalogue is
used only as a hard exclusion (the caller builds the pool), never to rank.

All functions are pure numpy and operate on pixel-centre coordinates.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

R_DEFAULT = 3.0  # triangular kernel radius, brief s2


def kernel_offsets(radius: float = R_DEFAULT) -> tuple[np.ndarray, np.ndarray]:
    """Integer offsets strictly inside the kernel disk and their credit 1 - d/R.

    Excludes (0, 0); a candidate's own pixel credit is handled separately.
    """
    r = int(math.ceil(radius))
    offs, credits = [], []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dy, dx)
            if 0.0 < d < radius:
                offs.append((dy, dx))
                credits.append(1.0 - d / radius)
    return np.asarray(offs, dtype=np.int64), np.asarray(credits, dtype=np.float64)


def support_credit(dots: np.ndarray, support: np.ndarray, radius: float = R_DEFAULT) -> np.ndarray:
    """Best kernel credit at every pixel from `dots`, counted only on `support`.

    Assumption A1/A2: credit at a pixel is `max(0, 1 - d/radius)` with d the Euclidean
    distance to the nearest dot; pixels outside `support` are forced to zero so that the
    refill is scored against the H19-5 proxy truth only.
    """
    dots = np.asarray(dots, dtype=bool)
    support = np.asarray(support, dtype=bool)
    if not dots.any():
        return np.zeros(support.shape, dtype=np.float32)
    d = ndi.distance_transform_edt(~dots)
    k = np.maximum(0.0, 1.0 - d / radius).astype(np.float32)
    return np.where(support, k, np.float32(0.0))


def marginal_gain_field(
    pool: np.ndarray,
    credit: np.ndarray,
    support: np.ndarray,
    radius: float = R_DEFAULT,
) -> np.ndarray:
    """Marginal kernel credit a new unit dot at each pool pixel would supply.

    Exact first-order dT on the proxy truth set, vectorised over the whole array. Zero
    outside `pool`.
    """
    offs, credits = kernel_offsets(radius)
    pad = int(math.ceil(radius))
    pool = np.asarray(pool, dtype=bool)
    credit = np.asarray(credit, dtype=np.float32)
    support = np.asarray(support, dtype=bool)
    h, w = credit.shape
    c = np.pad(credit, pad, mode="constant", constant_values=0.0)
    s = np.pad(support.astype(np.float32), pad, mode="constant", constant_values=0.0)
    gain = np.zeros((h, w), dtype=np.float32)
    for (dy, dx), k in zip(offs, credits):
        sup = s[pad + dy: pad + dy + h, pad + dx: pad + dx + w]
        cred = c[pad + dy: pad + dy + h, pad + dx: pad + dx + w]
        gain += np.maximum(0.0, np.float32(k) * sup - cred)
    gain += np.maximum(0.0, s[pad:pad + h, pad:pad + w] - credit)
    gain[~pool] = 0.0
    return gain


def credit_aware_refill(
    pool: np.ndarray,
    kept: np.ndarray,
    support: np.ndarray,
    n_refill: int,
    radius: float = R_DEFAULT,
) -> np.ndarray:
    """Greedy max-marginal-credit selection of `n_refill` pool pixels.

    `pool` is the caller's eligible refill mask (H19-5 support, outside the collar, not a
    catalogue pixel, not already kept). `kept` are the dots that survive the collar.
    `support` is the H19-5 proxy truth. Returns a boolean mask of the chosen pixels.

    Deterministic: ties break on flat raster index (np.argmax returns the first maximum).
    """
    pool = np.asarray(pool, dtype=bool) & ~np.asarray(kept, dtype=bool)
    support = np.asarray(support, dtype=bool)
    h, w = pool.shape
    if n_refill <= 0:
        return np.zeros((h, w), dtype=bool)
    if int(pool.sum()) < n_refill:
        raise ValueError(f"refill pool has {int(pool.sum())} pixels, need {n_refill}")

    offs, credits = kernel_offsets(radius)
    pad = int(math.ceil(radius))
    credit = support_credit(kept, support, radius)
    gain = marginal_gain_field(pool, credit, support, radius)

    c = np.pad(credit, pad, mode="constant", constant_values=0.0)
    s = np.pad(support.astype(np.float32), pad, mode="constant", constant_values=0.0)
    cand = np.argwhere(pool)
    selected = np.zeros((h, w), dtype=bool)
    total = gain.copy()

    for _ in range(n_refill):
        if cand.size == 0:
            break
        vals = total[cand[:, 0], cand[:, 1]]
        i = int(np.argmax(vals))
        qy, qx = int(cand[i, 0]), int(cand[i, 1])
        selected[qy, qx] = True

        # Exact local credit update: the new dot raises the best credit inside its disk.
        for (dy, dx), k in zip(offs, credits):
            yy, xx = qy + dy, qx + dx
            if 0 <= yy < h and 0 <= xx < w and s[yy + pad, xx + pad] > 0.0 \
                    and c[yy + pad, xx + pad] < k:
                c[yy + pad, xx + pad] = k
        if s[qy + pad, qx + pad] > 0.0:
            c[qy + pad, qx + pad] = 1.0
        credit[qy, qx] = s[qy, qx]

        # Only pool pixels within 2R can have their marginal credit changed.
        d2 = (cand[:, 0] - qy) ** 2 + (cand[:, 1] - qx) ** 2
        close = np.flatnonzero(d2 <= (2.0 * radius) ** 2 + 1e-9)
        keep = np.ones(cand.shape[0], dtype=bool)
        keep[i] = False
        for j in close.tolist():
            if not keep[j]:
                continue
            ay, ax = int(cand[j, 0]), int(cand[j, 1])
            g = 0.0
            for (dy, dx), k in zip(offs, credits):
                sup = s[ay + pad + dy, ax + pad + dx]
                if sup > 0.0:
                    cc = c[ay + pad + dy, ax + pad + dx]
                    if cc < k:
                        g += k - cc
            own = max(0.0, float(s[ay + pad, ax + pad]) - float(c[ay + pad, ax + pad]))
            total[ay, ax] = g + own
        cand = cand[keep]

    if int(selected.sum()) != n_refill:
        raise AssertionError(f"credit-aware refill selected {int(selected.sum())} != {n_refill}")
    return selected
