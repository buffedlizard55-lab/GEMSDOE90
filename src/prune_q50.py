"""Strike-aligned PRUNE with 5 km block-stratified marginal-kernel refill (q50).

Fixes the two compounding defects of global FIFO-BFS refill in prior PRUNE builds:
1. IR90-35 / IR90-20 northern-strip concentration: global ``fifo_bfs_visit_rank(h19)``
   places 100% of fixed-count PRUNE refills into the northernmost 2.7%-7.1% of grid rows
   (``y <= 101..264`` of ``H = 3730``), starving 87%-97% of dense 5 km blocks and failing
   ``mass_add.addition_evenness_gate`` on all 9 prior BUILT PRUNE variants.
2. IR90-12 kernel-shadow dilution + sub-3 px refill leak: FIFO rank-head cells sit at
   median 1.00 px from retained northern dots (97.9%-99.5% within 3 px) and allow new
   refill dots down to ``d_cat = 2.236 px``.

Here, collar removal uses the exact strike-aligned ellipse ``(across_px, along_px)`` with
isotropic fallback where catalogue structure-tensor coherence ``< 0.35``, while fixed-count
refill uses ``reach.infill_select`` (5 km block quotas + within-block greedy exact ``R=3 px``
marginal kernel credit on ``H19-5``) restricted to ``d_cat >= 3.0 px`` and outside the collar.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage as ndi

from src import dti, mass_add, reach


def unmapped_support_mask(
    footprint: np.ndarray,
    support: np.ndarray,
    catalogue: np.ndarray,
    field: Any,
    across_px: float,
    along_px: float,
    collar_membership_fn: Any,
) -> np.ndarray:
    """Return off-catalogue support pixels lying outside the strike-aligned collar."""
    base = np.asarray(footprint, dtype=bool) & np.asarray(support, dtype=bool) & ~np.asarray(catalogue, dtype=bool)
    near_y, near_x = np.nonzero(base & (field.dist <= float(across_px) + 1e-9))
    out = base.copy()
    if near_y.size > 0:
        inside, _ = collar_membership_fn(near_y, near_x, field, across_px=across_px, along_px=along_px)
        out[near_y[inside], near_x[inside]] = False
    return out


def q50_refill_pool(
    footprint: np.ndarray,
    support: np.ndarray,
    catalogue: np.ndarray,
    retained: np.ndarray,
    field: Any,
    across_px: float,
    along_px: float,
    collar_membership_fn: Any,
    min_cat_dist_px: float = 3.0,
) -> np.ndarray:
    """Eligible H19-5 refill pool: outside collar, not already retained, and d_cat >= min_cat_dist_px."""
    if min_cat_dist_px < 3.0:
        raise ValueError(f"min_cat_dist_px={min_cat_dist_px} must be >= 3.0 px for newly added refill dots")
    supp_out = unmapped_support_mask(
        footprint, support, catalogue, field, across_px, along_px, collar_membership_fn
    )
    pool = supp_out & ~np.asarray(retained, dtype=bool) & (field.dist >= float(min_cat_dist_px))
    return pool


def q50_prune_and_refill(
    parent: np.ndarray,
    footprint: np.ndarray,
    support: np.ndarray,
    catalogue: np.ndarray,
    field: Any,
    across_px: float,
    along_px: float,
    collar_membership_fn: Any,
    block_px: int = 50,
    min_cat_dist_px: float = 3.0,
    radius_px: float = 3.0,
) -> dict[str, Any]:
    """Prune parent dots in strike-aligned collar and refill to fixed count via 5 km marginal kernel credit."""
    parent_b = np.asarray(parent, dtype=bool)
    rows, cols = np.nonzero(parent_b)
    inside_parent, collar_diag = collar_membership_fn(
        rows, cols, field, across_px=across_px, along_px=along_px
    )
    collar_mask = np.zeros_like(parent_b)
    collar_mask[rows[inside_parent], cols[inside_parent]] = True
    retained = parent_b & ~collar_mask
    n_removed = int(collar_mask.sum())
    if n_removed <= 0:
        raise ValueError("Strike-aligned collar removed 0 dots; expected 1-50% parent diff")

    supp_unmapped = unmapped_support_mask(
        footprint, support, catalogue, field, across_px, along_px, collar_membership_fn
    )
    pool = supp_unmapped & ~retained & (field.dist >= float(min_cat_dist_px))
    if int(pool.sum()) < n_removed:
        raise ValueError(f"Eligible q50 refill pool ({int(pool.sum())}) smaller than n_removed ({n_removed})")

    infill = reach.infill_select(
        pool=pool,
        dots=retained,
        n_total=n_removed,
        block_px=block_px,
        radius=radius_px,
    )
    refill = np.asarray(infill["selected"], dtype=bool)
    candidate = retained | refill

    n_parent = int(parent_b.sum())
    n_cand = int(candidate.sum())
    if n_cand != n_parent:
        raise AssertionError(f"Fixed-count invariant violated: {n_cand} != {n_parent}")
    if np.any(retained & refill):
        raise AssertionError("Refill overlaps retained parent dots")
    if np.any(candidate & np.asarray(catalogue, dtype=bool)):
        raise AssertionError("Candidate places mass on catalogue pixels")
    if float(field.dist[refill].min()) < float(min_cat_dist_px) - 1e-6:
        raise AssertionError("Refill placed a newly added dot below min_cat_dist_px")

    return {
        "candidate": candidate,
        "retained": retained,
        "collar_mask": collar_mask,
        "refill": refill,
        "pool": pool,
        "support_unmapped": supp_unmapped,
        "collar_diagnostics": collar_diag,
        "infill": infill,
        "n_parent": n_parent,
        "n_removed": n_removed,
        "n_added": int(refill.sum()),
        "n_candidate": n_cand,
    }


def refill_Audit_stats(
    refill: np.ndarray,
    retained: np.ndarray,
    parent: np.ndarray,
    field_dist: np.ndarray,
    block_px: int = 50,
) -> dict[str, Any]:
    """Spatial evenness, northern-strip concentration, and kernel-shadow diagnostics for a refill mask."""
    ref_b = np.asarray(refill, dtype=bool)
    ret_b = np.asarray(retained, dtype=bool)
    par_b = np.asarray(parent, dtype=bool)
    n_ref = int(ref_b.sum())
    if n_ref == 0:
        raise ValueError("Refill mask is empty")

    ry, rx = np.nonzero(ref_b)
    d_kept = ndi.distance_transform_edt(~ret_b)[ref_b]
    d_cat_ref = field_dist[ref_b]
    d_cat_fin = field_dist[ret_b | ref_b]

    add_rep = mass_add.addition_report(ref_b, par_b, block_px=block_px)
    evenness_pass = bool(mass_add.addition_evenness_gate(add_rep))

    h = ref_b.shape[0]
    north_half_parent = float(par_b[: h // 2, :].sum()) / float(par_b.sum())
    cand_b = ret_b | ref_b
    north_half_cand = float(cand_b[: h // 2, :].sum()) / float(cand_b.sum())

    return {
        "n_refill": n_ref,
        "refill_bbox_y": [int(ry.min()), int(ry.max())],
        "refill_bbox_x": [int(rx.min()), int(rx.max())],
        "refill_y_median_px": float(np.median(ry)),
        "refill_y_p95_px": float(np.percentile(ry, 95)),
        "refill_row_span_fraction": float((int(ry.max()) - int(ry.min()) + 1) / float(h)),
        "refill_fraction_in_north_strip_y_le_264": float(np.mean(ry <= 264)),
        "north_half_dot_share_parent": north_half_parent,
        "north_half_dot_share_candidate": north_half_cand,
        "north_half_dot_share_shift": float(north_half_cand - north_half_parent),
        "refill_to_retained_min_px": float(d_kept.min()),
        "refill_to_retained_median_px": float(np.median(d_kept)),
        "refill_to_retained_mean_px": float(d_kept.mean()),
        "refill_within_3px_of_retained_count": int(np.sum(d_kept < 3.0)),
        "refill_within_3px_of_retained_fraction": float(np.mean(d_kept < 3.0)),
        "min_catalogue_distance_of_refill_px": float(d_cat_ref.min()),
        "median_catalogue_distance_of_refill_px": float(np.median(d_cat_ref)),
        "refill_dots_below_3px_catalogue": int(np.sum(d_cat_ref < 3.0)),
        "min_catalogue_distance_of_final_set_px": float(d_cat_fin.min()),
        "final_dots_below_3px_inherited_only": int(np.sum(d_cat_fin < 3.0)),
        "addition_evenness_report": add_rep,
        "passes_addition_evenness_gate": evenness_pass,
    }


def support_credit_comparison(
    parent: np.ndarray,
    retained: np.ndarray,
    cand_q50: np.ndarray,
    cand_fifo: np.ndarray,
    support_offcat: np.ndarray,
    support_unmapped: np.ndarray,
) -> dict[str, Any]:
    """Compare exact R=3 px kernel coverage T on full off-catalogue H19-5 and outside-collar H19-5."""
    T0_all, _, _ = dti.components_from_arrays(parent.astype(np.float32), support_offcat)
    Tk_all, _, _ = dti.components_from_arrays(retained.astype(np.float32), support_offcat)
    Tq_all, _, _ = dti.components_from_arrays(cand_q50.astype(np.float32), support_offcat)
    Tf_all, _, _ = dti.components_from_arrays(cand_fifo.astype(np.float32), support_offcat)

    T0_unm, _, _ = dti.components_from_arrays(parent.astype(np.float32), support_unmapped)
    Tk_unm, _, _ = dti.components_from_arrays(retained.astype(np.float32), support_unmapped)
    Tq_unm, _, _ = dti.components_from_arrays(cand_q50.astype(np.float32), support_unmapped)
    Tf_unm, _, _ = dti.components_from_arrays(cand_fifo.astype(np.float32), support_unmapped)

    n_rem = int(parent.sum()) - int(retained.sum())
    q50_rec_all = float(Tq_all - Tk_all)
    fifo_rec_all = float(Tf_all - Tk_all)
    q50_rec_unm = float(Tq_unm - Tk_unm)
    fifo_rec_unm = float(Tf_unm - Tk_unm)

    return {
        "off_catalogue_h19_support_px": int(support_offcat.sum()),
        "outside_collar_h19_support_px": int(support_unmapped.sum()),
        "r0_T_all_offcat": float(T0_all),
        "retained_T_all_offcat": float(Tk_all),
        "fifo_T_all_offcat": float(Tf_all),
        "q50_T_all_offcat": float(Tq_all),
        "fifo_refill_recovered_T_all_offcat": fifo_rec_all,
        "q50_refill_recovered_T_all_offcat": q50_rec_all,
        "q50_vs_fifo_recovered_T_ratio": float(q50_rec_all / fifo_rec_all) if fifo_rec_all > 0 else None,
        "fifo_mean_recovered_T_per_dot": float(fifo_rec_all / n_rem) if n_rem > 0 else 0.0,
        "q50_mean_recovered_T_per_dot": float(q50_rec_all / n_rem) if n_rem > 0 else 0.0,
        "r0_T_outside_collar": float(T0_unm),
        "retained_T_outside_collar": float(Tk_unm),
        "fifo_T_outside_collar": float(Tf_unm),
        "q50_T_outside_collar": float(Tq_unm),
        "fifo_net_delta_T_outside_collar_vs_r0": float(Tf_unm - T0_unm),
        "q50_net_delta_T_outside_collar_vs_r0": float(Tq_unm - T0_unm),
        "fifo_refill_recovered_T_outside_collar": fifo_rec_unm,
        "q50_refill_recovered_T_outside_collar": q50_rec_unm,
    }
