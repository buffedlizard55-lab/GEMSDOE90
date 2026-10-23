"""AXIS=RELIEF core operations: physiographic relief terciles and DTI marginal reallocation.

Relief index uses BOTH competition-supplied detrended-elevation bands in
`training_features.tif`:
  - Band 12 (`det_elev`): detrended elevation (m), capturing structural horst/graben level.
  - Band 19 (`det_elev_slope`): detrended elevation slope (deg), smoothed with a footprint-
    normalized Gaussian kernel (sigma = 30 px = 3.0 km) so local 100 m fault scarps on flat
    basin floors stay classified in the Basin landform rather than misclassified as Piedmont.

Within-tercile removal/addition uses exact max-plus triangular-kernel (R = 3 px) marginal
coverage on the off-catalogue H19-5 ridge support (`h19_5 & foot & ~cat`), which is strictly
order-isomorphic to `src.dti.marginal_gain` for unit-mass dots lying on the support (`dM = 1`)
and avoids the North-to-South row-scan bias of `fifo_bfs_visit_rank`.
"""
from __future__ import annotations

import heapq
import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

from src.dti import R_PX

SENTINEL_ABS = 1e30


def clean_band_median_fill(band: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, int]:
    """Replace non-finite or sentinel (|x| >= 1e30) values inside footprint with finite median."""
    arr = np.asarray(band, dtype=np.float64)
    foot = np.asarray(footprint, dtype=bool)
    valid = foot & np.isfinite(arr) & (np.abs(arr) < SENTINEL_ABS)
    if not valid.any():
        raise ValueError("band has zero finite in-footprint pixels")
    missing_in_foot = int(foot.sum() - valid.sum())
    med = float(np.median(arr[valid]))
    filled = np.where(valid, arr, med)
    filled[~foot] = np.nan
    return filled, missing_in_foot


def landform_relief_index(
    det_elev: np.ndarray,
    det_elev_slope: np.ndarray,
    footprint: np.ndarray,
    elev_weight: float = 0.85,
    slope_weight: float = 0.15,
    slope_sigma_px: float = 30.0,
) -> tuple[np.ndarray, dict]:
    """Compute composite in-footprint relief index in [0, 1] from det_elev and det_elev_slope."""
    if abs((elev_weight + slope_weight) - 1.0) > 1e-9 or elev_weight < 0 or slope_weight < 0:
        raise ValueError("elev_weight and slope_weight must be non-negative and sum to 1.0")
    foot = np.asarray(footprint, dtype=bool)
    n_foot = int(foot.sum())
    if n_foot < 3:
        raise ValueError("footprint must contain at least 3 pixels for terciles")

    e_clean, miss_elev = clean_band_median_fill(det_elev, foot)
    s_clean, miss_slope = clean_band_median_fill(det_elev_slope, foot)

    w = foot.astype(np.float64)
    s_zero = np.where(foot, s_clean, 0.0)
    if slope_sigma_px > 0:
        denom = np.maximum(ndi.gaussian_filter(w, sigma=slope_sigma_px, mode="nearest"), 1e-9)
        s_landform = ndi.gaussian_filter(s_zero, sigma=slope_sigma_px, mode="nearest") / denom
    else:
        s_landform = s_zero

    pct_elev = np.zeros(foot.shape, dtype=np.float64)
    pct_slope = np.zeros(foot.shape, dtype=np.float64)
    pct_elev[foot] = rankdata(e_clean[foot], method="average") / float(n_foot)
    pct_slope[foot] = rankdata(s_landform[foot], method="average") / float(n_foot)

    idx = np.full(foot.shape, np.nan, dtype=np.float64)
    idx[foot] = elev_weight * pct_elev[foot] + slope_weight * pct_slope[foot]
    meta = {
        "elev_weight": elev_weight,
        "slope_weight": slope_weight,
        "slope_sigma_px": slope_sigma_px,
        "slope_sigma_km": round(slope_sigma_px * 0.1, 3),
        "missing_det_elev_filled_px": miss_elev,
        "missing_det_elev_slope_filled_px": miss_slope,
    }
    return idx, meta


def relief_terciles(relief_idx: np.ndarray, footprint: np.ndarray) -> tuple[dict[str, np.ndarray], tuple[float, float]]:
    """Partition footprint into Basin (T1), Piedmont (T2), and Range-front (T3) terciles."""
    foot = np.asarray(footprint, dtype=bool)
    vals = np.asarray(relief_idx, dtype=np.float64)[foot]
    if not np.isfinite(vals).all():
        raise ValueError("relief_idx contains non-finite values inside footprint")
    q1, q2 = (float(x) for x in np.quantile(vals, [1.0 / 3.0, 2.0 / 3.0]))
    terciles = {
        "basin": foot & (relief_idx <= q1),
        "piedmont": foot & (relief_idx > q1) & (relief_idx <= q2),
        "range_front": foot & (relief_idx > q2),
    }
    return terciles, (q1, q2)


def _kernel_offsets(r_px: int = R_PX) -> list[tuple[int, int, float]]:
    out: list[tuple[int, int, float]] = []
    for dy in range(-r_px, r_px + 1):
        for dx in range(-r_px, r_px + 1):
            d = float(np.hypot(dy, dx))
            kv = max(0.0, 1.0 - d / float(r_px))
            if kv > 0.0:
                out.append((dy, dx, kv))
    return out


def greedy_relief_reallocate(
    parent_mask: np.ndarray,
    support_mask: np.ndarray,
    donor_mask: np.ndarray,
    recipient_mask: np.ndarray,
    dist_cat: np.ndarray,
    n_shift: int,
    min_added_cat_dist_px: float = 3.0,
) -> tuple[np.ndarray, dict]:
    """Shift `n_shift` unit-mass dots from `donor_mask` to `recipient_mask` at fixed count.

    - Drops `n_shift` dots from `parent_mask & donor_mask` greedily minimizing lost R=3 px
      triangular-kernel credit on `support_mask` (tie-broken deterministically by row, col).
    - Adds `n_shift` dots from `support_mask & recipient_mask & ~active & (dist_cat >= min_added_cat_dist_px)`
      greedily maximizing gained R=3 px triangular-kernel credit on `support_mask`.
    """
    r0 = np.asarray(parent_mask, dtype=bool)
    sup = np.asarray(support_mask, dtype=bool)
    donor = np.asarray(donor_mask, dtype=bool)
    recip = np.asarray(recipient_mask, dtype=bool)
    dcat = np.asarray(dist_cat, dtype=np.float64)

    if r0.shape != sup.shape or r0.shape != donor.shape or r0.shape != recip.shape or r0.shape != dcat.shape:
        raise ValueError("all masks and distance arrays must share identical shape")
    if np.any(donor & recip):
        raise ValueError("donor_mask and recipient_mask must be disjoint")
    if n_shift <= 0:
        raise ValueError("n_shift must be positive")

    donor_dots = int((r0 & donor).sum())
    if donor_dots < n_shift:
        raise ValueError(f"donor tercile has {donor_dots} parent dots, fewer than n_shift={n_shift}")

    H, W = r0.shape
    pad = R_PX
    hp, wp = H + 2 * pad, W + 2 * pad

    active = np.zeros((hp, wp), dtype=bool)
    active[pad : pad + H, pad : pad + W] = r0
    sup_p = np.zeros((hp, wp), dtype=bool)
    sup_p[pad : pad + H, pad : pad + W] = sup

    offsets = _kernel_offsets(R_PX)
    off_dy = np.array([o[0] for o in offsets], dtype=np.int32)
    off_dx = np.array([o[1] for o in offsets], dtype=np.int32)
    off_k = np.array([o[2] for o in offsets], dtype=np.float64)
    off_flat = off_dy * wp + off_dx
    n_off = len(off_flat)

    active_flat = active.ravel()
    sup_flat = sup_p.ravel()
    cover_flat = np.zeros(hp * wp, dtype=np.float64)
    second_flat = np.zeros(hp * wp, dtype=np.float64)
    owner_flat = np.full(hp * wp, -1, dtype=np.int32)

    ys, xs = np.nonzero(active)
    for idx in (ys * wp + xs).tolist():
        nbrs = idx + off_flat
        for j in range(n_off):
            nb = nbrs[j]
            if not sup_flat[nb]:
                continue
            kv = off_k[j]
            if kv > cover_flat[nb]:
                second_flat[nb] = cover_flat[nb]
                cover_flat[nb] = kv
                owner_flat[nb] = idx
            elif kv > second_flat[nb]:
                second_flat[nb] = kv

    def excl_loss(idx: int) -> float:
        loss = 0.0
        for j in range(n_off):
            nb = idx + off_flat[j]
            if owner_flat[nb] == idx:
                loss += cover_flat[nb] - second_flat[nb]
        return round(loss, 9)

    dys, dxs = np.nonzero(r0 & donor)
    drop_heap = [
        (excl_loss((y + pad) * wp + (x + pad)), y, x, (y + pad) * wp + (x + pad))
        for y, x in zip(dys.tolist(), dxs.tolist())
    ]
    heapq.heapify(drop_heap)

    removed = 0
    lost_support_credit = 0.0
    while removed < n_shift:
        loss, y, x, idx = heapq.heappop(drop_heap)
        if not active_flat[idx]:
            continue
        cur_loss = excl_loss(idx)
        if cur_loss > loss + 1e-12:
            heapq.heappush(drop_heap, (cur_loss, y, x, idx))
            continue
        active_flat[idx] = False
        lost_support_credit += cur_loss
        removed += 1
        for j in range(n_off):
            nb = idx + off_flat[j]
            if not sup_flat[nb]:
                continue
            c1, c2, own = 0.0, 0.0, -1
            for k2 in range(n_off):
                src = nb - off_flat[k2]
                if active_flat[src]:
                    kv = off_k[k2]
                    if kv > c1:
                        c2 = c1
                        c1 = kv
                        own = src
                    elif kv > c2:
                        c2 = kv
            cover_flat[nb] = c1
            second_flat[nb] = c2
            owner_flat[nb] = own

    cur_unpadded = active[pad : pad + H, pad : pad + W]
    elig = sup & recip & ~cur_unpadded & (dcat >= min_added_cat_dist_px)
    eys, exs = np.nonzero(elig)
    if len(eys) < n_shift:
        raise ValueError(
            f"recipient tercile has only {len(eys)} eligible support pixels (dist_cat>={min_added_cat_dist_px}) "
            f"for n_shift={n_shift}"
        )

    def marg_gain(idx: int) -> float:
        gain = 0.0
        for j in range(n_off):
            nb = idx + off_flat[j]
            if sup_flat[nb]:
                diff = off_k[j] - cover_flat[nb]
                if diff > 0.0:
                    gain += diff
        return round(gain, 9)

    add_heap = [
        (-marg_gain((y + pad) * wp + (x + pad)), y, x, (y + pad) * wp + (x + pad))
        for y, x in zip(eys.tolist(), exs.tolist())
    ]
    heapq.heapify(add_heap)

    added = 0
    gained_support_credit = 0.0
    while added < n_shift:
        neg_g, y, x, idx = heapq.heappop(add_heap)
        g = -neg_g
        cur_g = marg_gain(idx)
        if cur_g < g - 1e-12:
            heapq.heappush(add_heap, (-cur_g, y, x, idx))
            continue
        active_flat[idx] = True
        gained_support_credit += cur_g
        added += 1
        for j in range(n_off):
            nb = idx + off_flat[j]
            if not sup_flat[nb]:
                continue
            kv = off_k[j]
            if kv > cover_flat[nb]:
                second_flat[nb] = cover_flat[nb]
                cover_flat[nb] = kv
                owner_flat[nb] = idx
            elif kv > second_flat[nb]:
                second_flat[nb] = kv

    out = active[pad : pad + H, pad : pad + W].copy()
    if int(out.sum()) != int(r0.sum()):
        raise AssertionError(f"fixed-count invariant violated: {int(out.sum())} != {int(r0.sum())}")
    stats = {
        "n_shift": int(n_shift),
        "removed_dots": int((r0 & ~out).sum()),
        "added_dots": int((out & ~r0).sum()),
        "retained_dots": int((out & r0).sum()),
        "symmetric_difference_px": int((out ^ r0).sum()),
        "mass_shifted_pct_of_r0": 100.0 * float(n_shift) / float(r0.sum()),
        "pct_changed_symmetric": 100.0 * float((out ^ r0).sum()) / float(r0.sum()),
        "lost_support_credit": round(lost_support_credit, 4),
        "gained_support_credit": round(gained_support_credit, 4),
        "eligible_recipient_pool_px": int(len(eys)),
    }
    return out, stats


def block_density_cv(mask: np.ndarray, footprint: np.ndarray, block_px: int = 100, min_foot_frac: float = 0.5) -> float:
    """Coefficient of variation of dot density (dots per footprint pixel) over km-scale blocks."""
    m = np.asarray(mask, dtype=bool) & np.asarray(footprint, dtype=bool)
    foot = np.asarray(footprint, dtype=bool)
    H, W = m.shape
    densities = []
    min_px = max(1, int(np.ceil(min_foot_frac * block_px * block_px)))
    for r0 in range(0, H, block_px):
        r1 = min(H, r0 + block_px)
        for c0 in range(0, W, block_px):
            c1 = min(W, c0 + block_px)
            f_cnt = int(foot[r0:r1, c0:c1].sum())
            if f_cnt >= min_px:
                densities.append(float(m[r0:r1, c0:c1].sum()) / float(f_cnt))
    if not densities:
        return 0.0
    arr = np.asarray(densities, dtype=np.float64)
    mean = float(arr.mean())
    return float(arr.std(ddof=0) / mean) if mean > 0 else 0.0
