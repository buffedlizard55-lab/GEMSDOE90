"""AXIS=CONCENTRATION core operations: strain-rate structural prior and diagnostics.

Session 2026-10-23e (GEMSDOE90). The ONLY changed axis relative to R0
(`h33-h33-2-b2`, 37,654 unit-mass dots) is the concentration of the fixed
37,654-dot budget onto high- vs low-prior 5 km blocks, at fixed total count.

PRIOR (deliberately label-agnostic, unlike a sibling session's catalogue-density
concentration): the geodetic second invariant of the strain-rate tensor, band 4
`geod_2ndinv` of the pinned `training_features.tif` (a non-negative magnitude,
measured strictly >= 1.2 in-footprint). It is a direct physical proxy for present-day
crustal deformation -> where undiscovered/new faults most likely nucleate or slip.
R0's block density is nearly uncorrelated with it (rank r ~ +0.11) and it is
relief-neutral (r ~ -0.07 to the detrended-elevation tercile index), so this move is
orthogonal to both the physiographic RELIEF axis and the catalogue-density
CONCENTRATION already built in sibling repo GEMSDOE89. Because the prior uses a
supplied geophysical band and NO test label, score, or submission feedback, the edit
is not label probing (Hard Constraint #5); regional mass shifts are REPORTED, and the
only hard spatial gate is anti-isolation (no contiguous emptied hole/strip).

Placement reuses the audited `src.relief.greedy_relief_reallocate`: within the donor
stratum, drop the lowest-exclusive-credit R0 dots; within the recipient stratum, add
the highest-marginal-credit off-catalogue H19-5 ridge pixels (all d_cat >= 3.0 px).
All functions here are pure numpy and operate on pixel-centre coordinates.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

from src.relief import block_density_cv, clean_band_median_fill  # re-export audited helpers

SENTINEL_ABS = 1e30


def strain_prior_field(strain_band: np.ndarray, footprint: np.ndarray,
                       clip_pct: tuple[float, float] = (1.0, 99.0)) -> tuple[np.ndarray, dict]:
    """Clean (median-fill non-finite/sentinel), then winsorise the strain magnitude.

    Returns the in-footprint field (NaN outside) and a small metadata dict. The band
    is a non-negative strain-rate magnitude, so no absolute value is applied; clipping
    only guards against single-pixel outliers dominating a 5 km block mean.
    """
    foot = np.asarray(footprint, dtype=bool)
    cleaned, missing = clean_band_median_fill(strain_band, foot)
    lo, hi = (float(x) for x in np.percentile(cleaned[foot], list(clip_pct)))
    clipped = np.clip(cleaned, lo, hi)
    clipped[~foot] = np.nan
    meta = {
        "band": "Band 4: geod_2ndinv (geodetic second invariant / strain-rate magnitude)",
        "label_agnostic": True,
        "missing_in_foot_filled_px": missing,
        "clip_percentiles": list(clip_pct),
        "clip_values": [round(lo, 6), round(hi, 6)],
    }
    return clipped, meta


def block_grid(footprint: np.ndarray, block_px: int = 50,
               min_foot_frac: float = 0.5) -> list[tuple[int, int, int, int]]:
    """Row-major list of in-play blocks (r0, r1, c0, c1) with >= min_foot_frac footprint."""
    foot = np.asarray(footprint, dtype=bool)
    H, W = foot.shape
    out: list[tuple[int, int, int, int]] = []
    for r0 in range(0, H, block_px):
        r1 = min(H, r0 + block_px)
        for c0 in range(0, W, block_px):
            c1 = min(W, c0 + block_px)
            if foot[r0:r1, c0:c1].sum() >= min_foot_frac * block_px * block_px:
                out.append((r0, r1, c0, c1))
    return out


def block_prior(field: np.ndarray, footprint: np.ndarray,
                blocks: list[tuple[int, int, int, int]]) -> np.ndarray:
    """Mean of `field` over the footprint portion of each block."""
    f = np.asarray(field, dtype=np.float64)
    foot = np.asarray(footprint, dtype=bool)
    return np.array([f[r0:r1, c0:c1][foot[r0:r1, c0:c1]].mean()
                     for (r0, r1, c0, c1) in blocks], dtype=np.float64)


def strata_masks(shape: tuple[int, int], blocks: list[tuple[int, int, int, int]],
                 prior: np.ndarray, pool_frac: float = 0.5,
                 toward: bool = True) -> tuple[np.ndarray, np.ndarray, dict]:
    """Build donor/recipient block masks from the prior ranking.

    `toward=True`: donor = lowest-prior pool_frac blocks, recipient = highest-prior
    pool_frac blocks (concentrate onto high prior). `toward=False` swaps the strata
    (sign control: move mass AWAY from high prior). Ranking is a stable descending
    argsort so ties break by row-major block order (deterministic). With pool_frac
    <= 0.5 the two pools are disjoint.
    """
    if not 0.0 < pool_frac <= 0.5:
        raise ValueError("pool_frac must be in (0, 0.5]")
    prior = np.asarray(prior, dtype=np.float64)
    n = len(blocks)
    if prior.shape[0] != n:
        raise ValueError("prior length != number of blocks")
    k = int(pool_frac * n)
    order = np.argsort(-prior, kind="stable")
    high = order[:k].tolist()
    low = order[-k:].tolist()
    if set(high) & set(low):
        raise ValueError("donor and recipient pools overlap")
    H, W = shape
    donor = np.zeros((H, W), dtype=bool)
    recip = np.zeros((H, W), dtype=bool)
    donor_blocks, recip_blocks = (low, high) if toward else (high, low)
    for i in donor_blocks:
        r0, r1, c0, c1 = blocks[i]
        donor[r0:r1, c0:c1] = True
    for i in recip_blocks:
        r0, r1, c0, c1 = blocks[i]
        recip[r0:r1, c0:c1] = True
    if np.any(donor & recip):
        raise ValueError("donor and recipient masks overlap")
    meta = {
        "pool_frac": pool_frac,
        "direction": "toward_high_prior" if toward else "away_from_high_prior",
        "n_blocks": n,
        "n_donor_blocks": k,
        "n_recipient_blocks": k,
        "prior_min": round(float(prior.min()), 6),
        "prior_max": round(float(prior.max()), 6),
    }
    return donor, recip, meta


def region_shares(mask: np.ndarray) -> dict:
    """Fraction of dots in the N half and the four quadrants (report-only diagnostic)."""
    m = np.asarray(mask, dtype=bool)
    n = float(m.sum())
    H, W = m.shape
    if n <= 0:
        raise ValueError("empty mask")
    return {
        "north": round(float(m[: H // 2, :].sum()) / n, 6),
        "south": round(float(m[H // 2:, :].sum()) / n, 6),
        "q_NW": round(float(m[: H // 2, : W // 2].sum()) / n, 6),
        "q_NE": round(float(m[: H // 2, W // 2:].sum()) / n, 6),
        "q_SW": round(float(m[H // 2:, : W // 2].sum()) / n, 6),
        "q_SE": round(float(m[H // 2:, W // 2:].sum()) / n, 6),
    }


def max_region_share_shift(shares_before: dict, shares_after: dict) -> float:
    """Largest absolute change across the 5 reported region fractions (N + 4 quadrants)."""
    keys = ("north", "q_NW", "q_NE", "q_SW", "q_SE")
    return round(max(abs(shares_after[k] - shares_before[k]) for k in keys), 6)


def density_prior_rank_corr(mask: np.ndarray, footprint: np.ndarray,
                            blocks: list[tuple[int, int, int, int]],
                            prior: np.ndarray) -> float:
    """Spearman correlation between per-block dot density and the block prior."""
    foot = np.asarray(footprint, dtype=bool)
    m = np.asarray(mask, dtype=bool)
    dens = np.array([m[r0:r1, c0:c1].sum() / foot[r0:r1, c0:c1].sum()
                     for (r0, r1, c0, c1) in blocks], dtype=np.float64)
    return float(np.corrcoef(rankdata(dens), rankdata(np.asarray(prior, float)))[0, 1])


def emptied_cluster_report(removed_mask: np.ndarray, parent_mask: np.ndarray,
                           block_px: int = 50, dot_threshold: int = 5,
                           share_threshold: float = 0.9) -> dict:
    """Anti-isolation statistic: are removals forming a contiguous regional hole?

    Mirrors the MASS region-evenness instrument (scripts/build_mass_high_dose.py) but
    reports only the two clauses that matter for a targeted CONCENTRATION edit: the
    largest 8-connected cluster of >=90%-emptied blocks, and the fraction of
    well-populated (>=20 dot) blocks that are >=90% emptied. The 'p05 uniform-share'
    clause of the MASS gate is intentionally NOT used: a concentration edit is
    *supposed* to remove dots only from donor blocks, so uniform removal would be a
    contradiction, not a safety property.
    """
    parent = np.asarray(parent_mask, dtype=bool)
    removed = np.asarray(removed_mask, dtype=bool)
    H, W = parent.shape
    gy, gx = H // block_px + 2, W // block_px + 2
    ys, xs = np.nonzero(parent)
    yr, xr = np.nonzero(removed)
    tot = np.zeros((gy, gx), dtype=np.float64)
    rem = np.zeros_like(tot)
    np.add.at(tot, (ys // block_px, xs // block_px), 1)
    np.add.at(rem, (yr // block_px, xr // block_px), 1)
    share = np.divide(rem, tot, out=np.zeros_like(rem), where=tot > 0)
    blown = (tot >= dot_threshold) & (share >= share_threshold)
    lab, n_clusters = ndi.label(blown, structure=np.ones((3, 3), np.uint8))
    sizes = np.bincount(lab.ravel())[1:] if n_clusters else np.zeros(0, dtype=int)
    well = share[tot >= 20]
    return {
        "block_px": block_px,
        "blocks_with_20plus_dots": int((tot >= 20).sum()),
        "fraction_blocks_90pct_emptied": round(float((well >= share_threshold).mean()), 6) if well.size else 0.0,
        "largest_emptied_cluster_blocks": int(sizes.max()) if sizes.size else 0,
        "removed_share_max": round(float(share.max()), 6) if share.size else 0.0,
    }


def concentration_evenness_gate(report: dict, max_cluster: int = 4,
                                max_frac_emptied: float = 0.02) -> bool:
    """Anti-isolation gate (Hard Constraint #5) for a CONCENTRATION edit."""
    return (report["largest_emptied_cluster_blocks"] <= max_cluster
            and report["fraction_blocks_90pct_emptied"] <= max_frac_emptied)
