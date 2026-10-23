"""MASS axis, ADD direction: coverage infill at fixed geography.

Why this module exists
----------------------
The brief's algebra is DTI = T / (0.2T + 0.2(S - M) + 0.8|G|). Two marginal terms
price a single unit-mass dot:

    delete a dot:   dDTI ~= +0.2 * (1 - c_j) / D          (c_j = dot's own credit)
    add a dot:      dDTI ~= +[dT - DTI * (0.2 dT + 0.2 (1 - dM))] / D

The deletion ceiling is 0.2/D. The addition ceiling is 1/D when the new dot lands
on a truth pixel (dT = 1, dM = 1), i.e. five times higher, and it is paid every
time a currently uncredited stretch of the corroborated ridge support is covered.
The entity's whole recorded climb is deletion-side (121k field -> 44.1k dots ->
37.7k dots), so the add direction is the half of the axis with no live receipt.

What this module does NOT do
----------------------------
* It never looks at a competition score, a leaderboard, or a test label.
* It never uses the catalogue to *choose* where to add; the catalogue is only a
  hard exclusion (>= 3 px), per Hard Constraint #4 and the repo's
  `no_new_mass_within_3px` convention.
* It does not use the parent's FIFO-BFS traversal order. IR90-20 measured that
  order to be geographic (the rank head is a northern grid strip), which makes
  rank-dose additions a Hard-Constraint-#5 patterned file.

The ranking is the metric's own marginal credit, evaluated on the H19-5
corroborated-ridge support as a *truth proxy* (the same proxy the parent's dots
were thinned from). Because the kernel is radial and monotone in distance,
credit from a dot set is exactly `max(0, 1 - d_min/R)` with `d_min` the Euclidean
distance to the nearest dot, so an exact credit map is one distance transform.

All functions are pure numpy and operate on pixel-centre coordinates.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi

R_DEFAULT = 3.0


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


def credit_map(dots: np.ndarray, radius: float = R_DEFAULT) -> np.ndarray:
    """Exact metric credit at every pixel from a boolean dot mask (assumption A2)."""
    dots = np.asarray(dots, dtype=bool)
    if not dots.any():
        return np.zeros(dots.shape, dtype=np.float32)
    d = ndi.distance_transform_edt(~dots)
    return np.maximum(0.0, 1.0 - d / radius).astype(np.float32)


def gain_field(pool: np.ndarray, credit: np.ndarray, radius: float = R_DEFAULT) -> np.ndarray:
    """Marginal kernel credit a new unit dot at q would supply over the proxy truth set.

        gain(q) = sum_offset max(0, k_offset - credit[q + offset])

    i.e. the exact first-order dT on the proxy truth set (which is every pixel,
    because the caller restricts `pool` to proxy-truth cells and the shifted
    credit lookup uses the whole map). Zero outside `pool`.
    """
    offs, credits = kernel_offsets(radius)
    pad = int(math.ceil(radius))
    c = np.pad(np.asarray(credit, dtype=np.float32), pad, mode="constant", constant_values=0.0)
    h, w = credit.shape
    gain = np.zeros((h, w), dtype=np.float32)
    for (dy, dx), k in zip(offs, credits):
        shifted = c[pad + dy: pad + dy + h, pad + dx: pad + dx + w]
        gain += np.maximum(0.0, np.float32(k) - shifted)
    gain[~np.asarray(pool, dtype=bool)] = 0.0
    return gain


def block_index(shape: tuple[int, int], block_px: int) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """Row-major block ids for every pixel of `shape`."""
    h, w = shape
    by = np.arange(h) // block_px
    bx = np.arange(w) // block_px
    bid = by[:, None] * (int(bx.max()) + 1) + bx[None, :]
    return bid, np.arange(int(bid.max()) + 1), (int(by.max()) + 1, int(bx.max()) + 1)


def proportional_quotas(weights: np.ndarray, n_total: int) -> np.ndarray:
    """Largest-remainder apportionment of `n_total` over `weights` (exact sum)."""
    w = np.asarray(weights, dtype=np.float64)
    if w.sum() <= 0:
        raise ValueError("weights sum to zero")
    if n_total > w.sum():
        raise ValueError(f"n_total={n_total} exceeds available weight slots {w.sum():.0f}")
    exact = w * (n_total / w.sum())
    base = np.floor(exact).astype(np.int64)
    rem = n_total - int(base.sum())
    if rem > 0:
        order = np.lexsort((np.arange(len(w)), -(exact - base)))
        base[order[:rem]] += 1
    return base


def infill_select(
    pool: np.ndarray,
    dots: np.ndarray,
    n_total: int,
    block_px: int = 50,
    radius: float = R_DEFAULT,
    max_per_block: int | None = None,
) -> dict:
    """Greedy coverage infill with per-block quotas proportional to parent dots.

    Deterministic: within a block, ties break on flat raster index; quota
    remainders break on block id. Competition between new dots is handled
    exactly (the local credit map is updated after every selection, and the
    gains of pool cells within the kernel are recomputed).
    """
    pool = np.asarray(pool, dtype=bool) & ~np.asarray(dots, dtype=bool)
    dots = np.asarray(dots, dtype=bool)
    bid, block_ids, grid = block_index(dots.shape, block_px)
    r0_counts = np.bincount(bid[dots], minlength=len(block_ids))
    pool_counts = np.bincount(bid[pool], minlength=len(block_ids))
    active = np.flatnonzero(r0_counts > 0)
    if n_total > int(pool_counts[active].sum()):
        raise ValueError(
            f"requested {n_total} additions but only {int(pool_counts[active].sum())} "
            "eligible pool cells sit in blocks that already hold parent dots"
        )

    quota = np.zeros(len(block_ids), dtype=np.int64)
    quota[active] = proportional_quotas(r0_counts[active], n_total)
    cap = pool_counts if max_per_block is None else np.minimum(pool_counts, max_per_block)
    # Water-fill: move quota out of blocks that cannot host it into blocks with spare pool.
    for _ in range(len(block_ids)):
        over = np.clip(quota - cap, 0, None)
        if over.sum() == 0:
            break
        quota -= over
        spare = active[cap[active] - quota[active] > 0]
        if spare.size == 0:
            raise ValueError("cannot place requested additions under the block caps")
        quota[spare] += proportional_quotas(
            (cap[spare] - quota[spare]).astype(np.float64), int(over.sum())
        )

    credit = credit_map(dots, radius)
    selected = np.zeros(dots.shape, dtype=bool)
    add_gain: list[float] = []
    offs, credits = kernel_offsets(radius)
    pad = int(math.ceil(radius))
    h, w = dots.shape
    padded = np.pad(credit, pad, mode="constant", constant_values=0.0)

    def local_gain(qy: int, qx: int, cred_pad: np.ndarray) -> float:
        # credit at q + offset lives at (qy + pad + dy, qx + pad + dx)
        total = 0.0
        for (dy, dx), k in zip(offs, credits.tolist()):
            c = cred_pad[qy + pad + dy, qx + pad + dx]
            if c < k:
                total += k - c
        return total

    for blk in active[quota[active] > 0]:
        by, bx = divmod(int(blk), int(grid[1]))
        y0, y1 = by * block_px, min(h, (by + 1) * block_px)
        x0, x1 = bx * block_px, min(w, (bx + 1) * block_px)
        # Halo of R so a cell's neighbourhood (and the credit there) is complete.
        py0, py1 = max(0, y0 - pad), min(h, y1 + pad)
        px0, px1 = max(0, x0 - pad), min(w, x1 + pad)
        cand = np.argwhere(pool[py0:py1, px0:px1])
        if cand.size == 0:
            continue
        cand[:, 0] += py0
        cand[:, 1] += px0
        # The halo is for credit lookup only: a block may never place outside itself.
        inside = (cand[:, 0] >= y0) & (cand[:, 0] < y1) & (cand[:, 1] >= x0) & (cand[:, 1] < x1)
        cand = cand[inside]
        if cand.shape[0] == 0:
            continue
        gains = np.array([local_gain(int(a), int(b), padded) for a, b in cand], dtype=np.float64)
        want = int(quota[blk])
        for _ in range(want):
            if cand.shape[0] == 0:
                break
            order = np.lexsort((cand[:, 0] * w + cand[:, 1], -gains))
            pick = int(order[0])
            qy, qx = int(cand[pick, 0]), int(cand[pick, 1])
            value = float(gains[pick])
            if not np.isfinite(value):
                break
            selected[qy, qx] = True
            add_gain.append(max(0.0, value) + 1.0)  # +1.0: the dot's own pixel credit
            # Exact local credit update.
            for (dy, dx), k in zip(offs, credits.tolist()):
                yy, xx = qy + dy, qx + dx
                if 0 <= yy < h and 0 <= xx < w and padded[yy + pad, xx + pad] < k:
                    padded[yy + pad, xx + pad] = k
            padded[qy + pad, qx + pad] = 1.0
            # Drop the picked cell and refresh gains within the kernel.
            keep = np.ones(cand.shape[0], dtype=bool)
            keep[pick] = False
            cand, gains = cand[keep], gains[keep]
            if cand.shape[0]:
                close = (np.abs(cand[:, 0] - qy) < int(math.ceil(radius))) & (
                    np.abs(cand[:, 1] - qx) < int(math.ceil(radius))
                )
                idx = np.flatnonzero(close)
                for a in idx.tolist():
                    gains[a] = local_gain(int(cand[a, 0]), int(cand[a, 1]), padded)

    if int(selected.sum()) != n_total:
        raise AssertionError(f"selected {int(selected.sum())} additions != requested {n_total}")
    return {
        "selected": selected,
        "gains": np.asarray(add_gain, dtype=np.float64),
        "quota": quota,
        "block_counts_parent": r0_counts,
        "block_counts_add": np.bincount(bid[selected], minlength=len(block_ids)),
        "block_grid": grid,
        "block_px": block_px,
    }


def density_cv(counts: np.ndarray, occupied_only: bool = True) -> float:
    """Coefficient of variation of per-block dot counts (brief's 0.51-0.59 reference band)."""
    c = np.asarray(counts, dtype=np.float64)
    c = c[c > 0] if occupied_only else c
    if c.size == 0 or c.mean() == 0:
        return float("nan")
    return float(c.std() / c.mean())


def largest_contiguous(mask: np.ndarray) -> int:
    """Size (in blocks) of the largest 8-connected run of True cells."""
    lab, n = ndi.label(np.asarray(mask, dtype=bool), structure=np.ones((3, 3), dtype=np.uint8))
    if n == 0:
        return 0
    return int(np.bincount(lab.ravel())[1:].max())


def truth_free_add_delta(
    gain_sum: float,
    n_add: int,
    n_parent: int,
    dti: float,
    support_px: int,
    truth_px: float,
    alpha: float = 0.2,
) -> float:
    """First-order MODEL dDTI for the addition set (never a score).

    `gain_sum` is measured on the H19-5 support proxy, so it is scaled by the
    fraction of that support that is truth, f = min(1, truth_px / support_px).
    D = alpha * n_parent + (1 - alpha) * truth_px is the parent's denominator
    evaluated at the claimed DTI (wasted mass folded into the parent term).
    """
    f = min(1.0, truth_px / max(1, support_px))
    D = alpha * n_parent + (1.0 - alpha) * truth_px
    dT = f * gain_sum
    dM = f * n_add  # each added dot sits on a proxy-truth pixel: expected max-kernel = f
    num = dT - dti * (alpha * dT + alpha * (n_add - dM))
    return float(num / D)
