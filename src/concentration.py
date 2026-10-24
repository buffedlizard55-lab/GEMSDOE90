"""AXIS=CONCENTRATION: 15 km active-deformation / edge block prior.

The prior is built ONLY from the pinned competition feature raster
`training_features.tif`. It deliberately excludes temperature, wells, vents and
geothermal-site layers: the metric scores fault pixels, not heat. Four bands
enter with equal weight after an in-footprint percentile transform of their
absolute value:

  * band  3: `tmi_hg`                -- magnetic horizontal gradient
  * band  4: `geod_2ndinv`           -- geodetic strain-rate second invariant
  * band  7: `geod_shearrate`        -- geodetic shear rate
  * band 18: `iso_grav_anom_hg`      -- isostatic-gravity horizontal gradient

A block score is the mean composite rank of its in-footprint pixels. 15 km
(150 px) is selected because the exact R0 rebuild has block-density CV
0.5103 at that scale with `min_foot_frac=0.5`, inside the session brief's
reported 0.51-0.59 band. The prior is a regional structural-interaction
prior, not a label-probing instrument: it never reads the hidden/public test
truth and only the public, pinned feature values set the block ranking.

The reallocation operator itself is imported from `src.relief`: it drops dots
by minimum exclusive R=3 px kernel credit and adds dots by maximum marginal
credit on H19-5 support, with all additions at d_cat >= 3 px. Only the donor
and recipient block masks differ from the RELIEF axis.
"""
from __future__ import annotations

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

from src.relief import SENTINEL_ABS, block_density_cv, greedy_relief_reallocate

PRIOR_BANDS = (3, 4, 7, 18)
PRIOR_BAND_NAMES = (
    "tmi_hg",
    "geod_2ndinv",
    "geod_shearrate",
    "iso_grav_anom_hg",
)
BLOCK_PX = 150
BLOCK_KM = 15.0
MIN_FOOT_FRAC = 0.5
TAIL_FRAC = 0.35


def _rank_abs_band(band: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Return in-footprint percentile ranks of |band|, median-filling sentinels."""
    foot = np.asarray(footprint, dtype=bool)
    arr = np.asarray(band, dtype=np.float64)
    vals = np.abs(arr[foot])
    valid = np.isfinite(vals) & (vals < SENTINEL_ABS)
    if not valid.any():
        raise ValueError("prior band has no finite in-footprint values")
    filled = np.where(valid, vals, float(np.median(vals[valid])))
    ranks = rankdata(filled, method="average") / float(len(filled) + 1)
    out = np.zeros(foot.shape, dtype=np.float64)
    out[foot] = ranks
    return out


def structural_prior(
    feature_path: str,
    footprint: np.ndarray,
    block_px: int = BLOCK_PX,
    min_foot_frac: float = MIN_FOOT_FRAC,
    tail_frac: float = TAIL_FRAC,
    bands: tuple[int, ...] = PRIOR_BANDS,
) -> dict:
    """Compute the block structural prior and donor/recipient block id arrays."""
    foot = np.asarray(footprint, dtype=bool)
    if not 0 < tail_frac < 0.5:
        raise ValueError("tail_frac must lie in (0, 0.5)")
    if block_px <= 0 or not 0 < min_foot_frac <= 1:
        raise ValueError("invalid block_px or min_foot_frac")

    composite = np.zeros(foot.shape, dtype=np.float64)
    band_meta = []
    with rasterio.open(feature_path) as ds:
        descriptions = list(ds.descriptions)
        for b in bands:
            raw = ds.read(b)
            name = (descriptions[b - 1] or f"band_{b}").split(" - ")[0].strip()
            composite += _rank_abs_band(raw, foot)
            band_meta.append({"band": int(b), "name": name})
    composite /= float(len(bands))
    composite[~foot] = np.nan

    H, W = foot.shape
    n_by = (H + block_px - 1) // block_px
    n_bx = (W + block_px - 1) // block_px
    block_id = np.full((H, W), -1, dtype=np.int32)
    scores: list[float] = []
    foot_counts: list[int] = []
    block_boxes: list[tuple[int, int, int, int]] = []
    bid = 0
    for bi in range(n_by):
        for bj in range(n_bx):
            y0, y1 = bi * block_px, min(H, (bi + 1) * block_px)
            x0, x1 = bj * block_px, min(W, (bj + 1) * block_px)
            f = foot[y0:y1, x0:x1]
            n_f = int(f.sum())
            min_px = max(1, int(np.ceil(min_foot_frac * f.size)))
            if n_f < min_px:
                continue
            block_id[y0:y1, x0:x1] = bid
            scores.append(float(np.mean(composite[y0:y1, x0:x1][f])))
            foot_counts.append(n_f)
            block_boxes.append((y0, y1, x0, x1))
            bid += 1
    if bid < 8:
        raise ValueError(f"only {bid} eligible blocks; cannot form prior tails")

    score_arr = np.asarray(scores, dtype=np.float64)
    low_cut, high_cut = (float(x) for x in np.quantile(score_arr, [tail_frac, 1.0 - tail_frac]))
    donor_ids = np.flatnonzero(score_arr <= low_cut)
    recipient_ids = np.flatnonzero(score_arr >= high_cut)
    if not len(donor_ids) or not len(recipient_ids):
        raise ValueError("empty donor or recipient block tail")

    donor_mask = np.isin(block_id, donor_ids)
    recipient_mask = np.isin(block_id, recipient_ids)
    if np.any(donor_mask & recipient_mask):
        raise AssertionError("donor and recipient tail blocks overlap")

    meta = {
        "block_px": int(block_px),
        "block_km": round(block_px * 0.1, 3),
        "min_footprint_fraction": float(min_foot_frac),
        "tail_fraction": float(tail_frac),
        "bands": band_meta,
        "weighting": "equal arithmetic mean of absolute-value in-footprint percentile ranks",
        "aggregation": "mean composite rank over each eligible block's in-footprint pixels",
        "n_blocks_total": int(bid),
        "n_donor_blocks": int(len(donor_ids)),
        "n_recipient_blocks": int(len(recipient_ids)),
        "low_prior_cut": round(low_cut, 8),
        "high_prior_cut": round(high_cut, 8),
        "score_min": round(float(score_arr.min()), 8),
        "score_median": round(float(np.median(score_arr)), 8),
        "score_max": round(float(score_arr.max()), 8),
    }
    return {
        "composite": composite,
        "block_id": block_id,
        "scores": score_arr,
        "foot_counts": np.asarray(foot_counts, dtype=np.int64),
        "boxes": block_boxes,
        "donor_ids": donor_ids,
        "recipient_ids": recipient_ids,
        "donor_mask": donor_mask,
        "recipient_mask": recipient_mask,
        "meta": meta,
    }


def reallocate_to_high_prior(
    parent_mask: np.ndarray,
    support_mask: np.ndarray,
    dist_cat: np.ndarray,
    prior: dict,
    n_shift: int,
    min_added_cat_dist_px: float = 3.0,
) -> tuple[np.ndarray, dict]:
    """Move n_shift dots from low- to high-prior blocks at fixed count."""
    r0 = np.asarray(parent_mask, dtype=bool)
    # Restrict donor dots to R0's >=3 px collar so CONCENTRATION is not silently
    # confounded with PRUNE; untouched R0 dots at 2..3 px remain on the parent.
    donor = np.asarray(prior["donor_mask"], dtype=bool) & (np.asarray(dist_cat) >= 3.0)
    recipient = np.asarray(prior["recipient_mask"], dtype=bool)
    out, stats = greedy_relief_reallocate(
        parent_mask=r0,
        support_mask=np.asarray(support_mask, dtype=bool),
        donor_mask=donor,
        recipient_mask=recipient,
        dist_cat=np.asarray(dist_cat, dtype=np.float64),
        n_shift=int(n_shift),
        min_added_cat_dist_px=float(min_added_cat_dist_px),
    )
    added = out & ~r0
    removed = r0 & ~out
    if not np.all(prior["donor_mask"][removed]):
        raise AssertionError("a removed dot lies outside the declared low-prior blocks")
    if not np.all(prior["recipient_mask"][added]):
        raise AssertionError("an added dot lies outside the declared high-prior blocks")
    if float(dist_cat[added].min()) < min_added_cat_dist_px:
        raise AssertionError("an added dot violates the 3 px catalogue collar")
    stats = dict(stats)
    stats["min_added_catalogue_distance_px"] = round(float(dist_cat[added].min()), 6)
    stats["added_dots_below_3px"] = int((added & (dist_cat < 3.0)).sum())
    return out, stats


def region_evenness_report(
    parent_mask: np.ndarray,
    candidate_mask: np.ndarray,
    prior: dict,
    nominal_shift_frac: float,
    near_empty_threshold: float = 0.90,
) -> dict:
    """Fail-closed geographic guard: no contiguous low-prior hole may be emptied."""
    r0 = np.asarray(parent_mask, dtype=bool)
    cand = np.asarray(candidate_mask, dtype=bool)
    bid = prior["block_id"]
    scores = prior["scores"]
    donor_set = set(int(x) for x in prior["donor_ids"])
    recipient_set = set(int(x) for x in prior["recipient_ids"])

    removed_share: dict[int, float] = {}
    added_share: dict[int, float] = {}
    for k, (y0, y1, x0, x1) in enumerate(prior["boxes"]):
        before = int(r0[y0:y1, x0:x1].sum())
        after = int(cand[y0:y1, x0:x1].sum())
        if k in donor_set and before:
            removed_share[k] = (before - after) / float(before)
        if k in recipient_set and before:
            added_share[k] = (after - before) / float(before)

    bp = int(prior["meta"]["block_px"])
    n_by = max(box[0] for box in prior["boxes"]) // bp + 1
    n_bx = max(box[2] for box in prior["boxes"]) // bp + 1
    near_empty = np.zeros((n_by, n_bx), dtype=bool)
    for k, share in removed_share.items():
        y0, _y1, x0, _x1 = prior["boxes"][k]
        if share >= near_empty_threshold:
            near_empty[y0 // bp, x0 // bp] = True
    _lab, n_clusters = ndi.label(near_empty, structure=np.ones((3, 3), dtype=np.uint8))
    sizes = np.bincount(_lab.ravel())[1:] if n_clusters else np.zeros(0, dtype=int)
    rem = np.asarray(list(removed_share.values()), dtype=np.float64)
    add = np.asarray(list(added_share.values()), dtype=np.float64)
    report = {
        "block_px": int(prior["meta"]["block_px"]),
        "near_empty_threshold": float(near_empty_threshold),
        "donor_blocks_with_parent_dots": int(len(rem)),
        "recipient_blocks_with_parent_dots": int(len(add)),
        "donor_removed_share_mean": round(float(rem.mean()), 6),
        "donor_removed_share_p05": round(float(np.percentile(rem, 5)), 6),
        "donor_removed_share_p95": round(float(np.percentile(rem, 95)), 6),
        "donor_removed_share_max": round(float(rem.max()), 6),
        "recipient_added_share_mean": round(float(add.mean()), 6),
        "recipient_added_share_max": round(float(add.max()), 6),
        "fraction_donor_blocks_near_emptied": round(float((rem >= near_empty_threshold).mean()), 6),
        "largest_near_emptied_cluster_blocks": int(sizes.max()) if sizes.size else 0,
        "nominal_shift_fraction": round(float(nominal_shift_frac), 6),
        "donor_block_prior_mean": round(float(scores[prior["donor_ids"]].mean()), 6),
        "recipient_block_prior_mean": round(float(scores[prior["recipient_ids"]].mean()), 6),
    }
    # A low-prior tail is expected to lose more than average, but no 15 km block
    # may be erased and no contiguous >=90%-empty cluster may form.
    checks = {
        "no_donor_block_90pct_emptied": report["fraction_donor_blocks_near_emptied"] == 0.0,
        "largest_near_emptied_cluster_le_4_blocks": report["largest_near_emptied_cluster_blocks"] <= 4,
        "p05_donor_removal_share_at_least_quarter_dose": (
            report["donor_removed_share_p05"] >= 0.25 * report["nominal_shift_fraction"]
        ),
        "recipient_prior_strictly_higher": (
            report["recipient_block_prior_mean"] > report["donor_block_prior_mean"]
        ),
    }
    report["checks"] = checks
    report["pass"] = all(checks.values())
    return report


def density_cv(mask: np.ndarray, footprint: np.ndarray, block_px: int = BLOCK_PX,
               min_foot_frac: float = MIN_FOOT_FRAC) -> float:
    """CV of dots per footprint pixel over exactly the prior's 15 km block grid."""
    return float(block_density_cv(mask, footprint, block_px=block_px, min_foot_frac=min_foot_frac))
