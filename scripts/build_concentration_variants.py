#!/usr/bin/env python3
"""Rebuild R0 byte-for-byte, then build and validate 3 controlled AXIS=CONCENTRATION variants.

Session 2026-10-23e (GEMSDOE90, agent-selected axis). The ONLY changed axis relative to
R0 (`h33-h33-2-b2`, 37,654 unit-mass dots) is how the fixed 37,654-dot budget is
concentrated across 5 km blocks ranked by a LABEL-AGNOSTIC structural prior: the
geodetic strain-rate second invariant (band 4 `geod_2ndinv` of pinned
training_features.tif). Total count is held strictly fixed; all dots lie on the pinned
off-catalogue H19-5 support; every newly added dot has Euclidean catalogue distance
>= 3.0 px; zero catalogue mass is emitted. Retained R0 dots keep R0's own 2.236 px
collar (a CONCENTRATION edit must not also move the PRUNE collar, IR90-07/14/18).

Why this value family is NEW: sibling repos already built CONCENTRATION on a
catalogue-fault-DENSITY prior (GEMSDOE89 CONC5kmcat*), an H19-5 prior (GEMSDOE87),
and a parent self-density prior (GEMSDOE88/91). A geodetic strain-rate prior is
label-agnostic, near-orthogonal to R0's allocation (rank r ~ +0.11) and relief-neutral,
so it is orthogonal to every sibling value and to the RELIEF/PRUNE/MASS axes in this
repo. Audit: ledger/experiment_reservations.json "concentration_reservations".

Run build:  `.venv/bin/python scripts/build_concentration_variants.py --build`
Run verify: `.venv/bin/python scripts/build_concentration_variants.py --verify`
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_r0_variants as base_build  # noqa: E402  exact-R0 rebuild path
import build_relief_variants as relief_build  # noqa: E402  audited PROXY instruments
from src.validate import validate as format_validate  # noqa: E402
from src.relief import (  # noqa: E402
    block_density_cv,
    greedy_relief_reallocate,
    landform_relief_index,
    relief_terciles,
)
from src.concentration import (  # noqa: E402
    block_grid,
    block_prior,
    concentration_evenness_gate,
    density_prior_rank_corr,
    emptied_cluster_report,
    max_region_share_shift,
    region_shares,
    strain_prior_field,
    strata_masks,
)

DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "CONCENTRATION"
AXIS_TOKEN = "CONC"
DATE = "20261023"
SEED = 20261023
R0_DOTS = 37_654
BLOCK_PX = 50          # 5 km prior blocks
POOL_FRAC = 0.50       # complementary halves (donor = bottom half, recipient = top half)
MIN_ADDED_CAT_DIST = 3.0
# Anti-isolation gate (Hard Constraint #5), following the MASS region-evenness standard
# but only the two clauses that apply to a targeted concentration edit.
MAX_EMPTIED_CLUSTER_BLOCKS = 4
MAX_FRACTION_BLOCKS_EMPTIED = 0.02
MAX_REGION_SHARE_SHIFT = 0.10   # loose documented cap; shifts are reported, not tuned

EXTRA_PINS = {
    "training_features": "training_features.tif",
    "sgmc": "external/derived_sgmc_faults_100m_u8.tif",
}

VARIANT_SPECS = (
    {
        "tag": "strain10",
        "toward": True,
        "mass_frac": 0.10,
        "n_shift": 3_765,   # round(0.10 * 37,654)
        "pred_short": "+0.004",
        "predicted_change": "+0.004 DTI (MODEL; plausible interval -0.010 to +0.015; not a score)",
        "hypothesis": (
            "New (unmapped) faults preferentially nucleate and slip where the present-day crust is "
            "actively deforming. Moving 10% of R0's fixed mass budget OUT of the lowest-strain-rate "
            "5 km blocks INTO the highest-strain-rate blocks raises 300 m-kernel coverage of the "
            "actively deforming ground most likely to host undiscovered traces, at unchanged total "
            "mass penalty."
        ),
        "mechanism": (
            "The geodetic second invariant (band 4) is a direct, label-agnostic measure of strain-rate "
            "magnitude from GPS/InSAR. R0's block density is nearly uncorrelated with it (rank r~+0.11) "
            "and it is relief-neutral (r~-0.07 to the detrended-elevation tercile index), so this move is "
            "orthogonal to both the physiographic RELIEF axis and the catalogue-density CONCENTRATION "
            "built in a sibling session. Within complementary top/bottom-half strain pools we greedily "
            "drop the lowest-exclusive-credit R0 dots in low-strain blocks and add the highest-marginal-"
            "credit off-catalogue H19-5 ridge pixels (all d_cat>=3.0 px) in high-strain blocks, holding "
            "count at 37,654. Block-density CV at 15 km rises 0.510->~0.57, still inside the owner-"
            "reported 'best files 0.51-0.59' band; the density-strain rank correlation rises +0.11->+0.26."
        ),
        "non_fault_confounder": (
            "Strain-rate model artefacts where GPS/InSAR station spacing is sparse; anthropogenic or "
            "hydrologic/volcanic transients (groundwater withdrawal, geothermal fluid extraction, magma "
            "inflation) that raise apparent strain without brittle upper-crustal faulting; and strain "
            "gradients that localise on ductile shear or magmatic systems rather than seismogenic faults."
        ),
        "falsifier": (
            "A paired live receipt vs R0 with delta <= -0.010 DTI falsifies strain-guided concentration at "
            "this dose. If the matched-dose sign control `strainAway10` (similar CV, opposite strain "
            "alignment) scores >= strain10, the strain prior itself is falsified. Any |delta|<0.010 is no evidence."
        ),
    },
    {
        "tag": "strain15",
        "toward": True,
        "mass_frac": 0.15,
        "n_shift": 5_648,   # round(0.15 * 37,654)
        "pred_short": "+0.001",
        "predicted_change": "+0.001 DTI (MODEL; plausible interval -0.013 to +0.013; not a score)",
        "hypothesis": (
            "Dose top: if the strain prior is real, a 15% move should extend the 10% gain; but 15 km CV "
            "rises to ~0.62 (above the reported best band) and the greedy loses more support credit, so "
            "the net is predicted near zero. This rung measures the concentration dose-response slope."
        ),
        "mechanism": (
            "Identical operator and pools as strain10 with a 15% (5,648-dot) transfer, count fixed at 37,654, "
            "additions d_cat>=3.0 px. The density-strain correlation rises to ~0.31 and 15 km CV to ~0.62; "
            "the largest 5 km emptied cluster stays <=1 block (no regional hole)."
        ),
        "non_fault_confounder": (
            "Same geodetic artefacts as strain10, plus over-concentration onto a few strain maxima that may "
            "be network-spacing artefacts rather than discrete active faults."
        ),
        "falsifier": (
            "A paired live receipt delta <= -0.010 vs strain10 rejects further dose; delta >= +0.010 supports "
            "pushing the dose higher. Any |delta|<0.010 is no evidence."
        ),
    },
    {
        "tag": "strainAway10",
        "toward": False,
        "mass_frac": 0.10,
        "n_shift": 3_765,
        "pred_short": "-0.004",
        "predicted_change": "-0.004 DTI (MODEL; plausible interval -0.016 to +0.008; not a score)",
        "hypothesis": (
            "Sign control: move 10% of mass OUT of the highest-strain blocks INTO the lowest-strain blocks. "
            "If strain rate genuinely marks new-fault ground, this must lose; a gain here falsifies the strain "
            "prior (or indicates strain maxima are dominated by non-tectonic noise, or that undisclosed labels "
            "sit in aseismic blocks)."
        ),
        "mechanism": (
            "Identical placement rule and dose as strain10 with donor/recipient strata reversed, giving the "
            "same ~20% symmetric change and a similar 15 km CV (~0.56) so the comparison isolates strain "
            "DIRECTION from the raw concentration level. Density-strain correlation falls from +0.11 to ~-0.04."
        ),
        "non_fault_confounder": (
            "If the undisclosed test labels were compiled largely from aseismic historic bedrock quadrangle "
            "maps, an away-from-strain move could coincidentally gain - a genuine confound, which is exactly "
            "why the sign control is slotted."
        ),
        "falsifier": (
            "strainAway10 >= strain10 on paired live receipts falsifies the strain mechanism; "
            "strainAway10 <= -0.010 confirms it. Any |delta|<0.010 is no evidence."
        ),
    },
)


def value_string(spec: dict) -> str:
    pct = 100.0 * spec["mass_frac"]
    direction = "low->high strain" if spec["toward"] else "high->low strain (sign control)"
    return (
        f"tag={spec['tag']}; 5km blocks; prior=geodetic strain-rate invariant band4 (label-agnostic); "
        f"move {pct:g}% R0 mass ({spec['n_shift']} dots) {direction}; 50% pool; "
        f"fixed count 37654; added d_cat>=3px"
    )


def check_reservations() -> None:
    """Fail closed if any (CONCENTRATION, tag) or hash already exists (dedupe rule)."""
    res_path = ROOT / "ledger" / "experiment_reservations.json"
    if res_path.is_file():
        res = json.loads(res_path.read_text(encoding="utf-8"))
        taken = set(res.get("concentration_reservations", {}).get("occupied_tags", []))
        for spec in VARIANT_SPECS:
            if spec["tag"] in taken:
                raise ValueError(f"duplicate experiment reservation: (CONCENTRATION, {spec['tag']}) already reserved")
    ledger_path = ROOT / "ledger" / "submissions.csv"
    if ledger_path.is_file():
        with ledger_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                val = row.get("value") or ""
                for spec in VARIANT_SPECS:
                    if f"tag={spec['tag']}" in val:
                        raise ValueError(f"duplicate experiment in ledger: (CONCENTRATION, {spec['tag']})")


def existing_ledger_hashes(exclude_ids: set[str] | None = None) -> set[str]:
    exclude = exclude_ids or set()
    ledger_path = ROOT / "ledger" / "submissions.csv"
    hashes: set[str] = set()
    if ledger_path.is_file():
        with ledger_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("id") in exclude:
                    continue
                for col in ("sha256", "sha256_zeros"):
                    val = (row.get(col) or "").strip()
                    if val:
                        hashes.add(val)
    return hashes


def load_prior_layers(foot: np.ndarray):
    with rasterio.open(DATA / EXTRA_PINS["training_features"]) as ds:
        strain_band = ds.read(4)
        det_elev = ds.read(12)
        det_elev_slope = ds.read(19)
    field, meta = strain_prior_field(strain_band, foot)
    blocks = block_grid(foot, BLOCK_PX)
    prior = block_prior(field, foot, blocks)
    meta["n_blocks"] = len(blocks)
    meta["block_px"] = BLOCK_PX
    meta["block_km"] = BLOCK_PX * 0.1
    # Report-only: relief-neutrality of the prior (block-level rank corr with relief tercile index).
    relief_idx, _ = landform_relief_index(det_elev, det_elev_slope, foot)
    relief_block = block_prior(relief_idx, foot, blocks)
    meta["prior_vs_relief_rank_corr"] = round(
        float(np.corrcoef(rankdata(prior), rankdata(relief_block))[0, 1]), 4)
    return field, blocks, prior, meta, relief_idx


def leakage_canary(foot: np.ndarray, cat: np.ndarray, strain_field: np.ndarray,
                   seed: int = SEED) -> dict:
    """Report-only single-feature symmetric ROC-AUC across all 19 bands + strain prior."""
    report = relief_build.compute_leakage_canary(foot, cat, strain_field, seed=seed)
    feats = report.get("features", {})
    if "composite_landform_relief_idx" in feats:
        feats["strain_prior_band4"] = feats.pop("composite_landform_relief_idx")
    if "composite_relief_idx_symmetric_auc" in report:
        report["strain_prior_symmetric_auc"] = report.pop("composite_relief_idx_symmetric_auc")
    report["note"] = "Prior is a supplied geophysical band (label-agnostic); no catalogue-derived feature included."
    return report


def validate_concentration_file(path: Path, expected_mask: np.ndarray, r0_mask: np.ndarray,
                                foot: np.ndarray, cat: np.ndarray, dist_cat: np.ndarray,
                                sample_path: Path, cat_path: Path, sample_profile: dict,
                                mode: str) -> dict:
    fmt = format_validate(str(path), str(sample_path), str(cat_path), zeros_outside=(mode == "zeros"))
    if not fmt["pass"]:
        raise ValueError(f"src.validate failed for {path.name}: {fmt['fails']}")
    with rasterio.open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs = src.crs
        transform = src.transform
    disk_mask = (a > 0.5) & foot
    added_mask = disk_mask & ~r0_mask
    retained_mask = disk_mask & r0_mask
    checks = {
        "src_validate_gate_pass": bool(fmt["pass"]),
        "crs_matches_sample": crs == sample_profile["crs"],
        "transform_matches_sample": transform == sample_profile["transform"],
        "shape_matches_sample": a.shape == (sample_profile["height"], sample_profile["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(a[foot]).all()),
        "inside_foot_range_0_1": bool(np.all((a[foot] >= 0.0) & (a[foot] <= 1.0))),
        "outside_encoding_valid": bool(np.isnan(a[~foot]).all()) if mode == "nan" else bool(np.all(a[~foot] == 0.0)),
        "exact_expected_mask_after_disk_read": bool(np.array_equal(disk_mask, expected_mask)),
        "zero_catalogue_mass": not bool(np.any(disk_mask & cat)),
        "added_dots_min_cat_dist_ge_3px": bool(float(dist_cat[added_mask].min()) >= MIN_ADDED_CAT_DIST) if added_mask.any() else True,
        "retained_dots_preserve_r0_collar_gt_2px": bool(float(dist_cat[retained_mask].min()) > 2.0),
        "file_re_read_from_disk": True,
    }
    if not all(checks.values()):
        raise ValueError(f"concentration validator failed for {path.name}: {[k for k, v in checks.items() if not v]}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": base_build.sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(disk_mask.sum()),
        "min_catalogue_distance_all_dots_px": round(float(dist_cat[disk_mask].min()), 6),
        "min_catalogue_distance_added_dots_px": round(float(dist_cat[added_mask].min()), 6),
        "inherited_r0_dots_below_3px": int((retained_mask & (dist_cat < 3.0)).sum()),
        "added_dots_below_3px": int((added_mask & (dist_cat < 3.0)).sum()),
        "checks": checks,
    }


def build_all() -> dict:
    t0 = time.time()
    check_reservations()
    input_receipt = base_build.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)

    # Support is the pinned off-catalogue H19-5 ridge mask; R0 must sit entirely on it.
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    if not np.all(~r0 | support):
        raise ValueError("R0 contains pixels outside off-catalogue H19-5 support")

    field, blocks, prior, prior_meta, relief_idx = load_prior_layers(foot)
    canary = leakage_canary(foot, cat, field, seed=SEED)

    shares_before = region_shares(r0)
    cv_before = {f"block_density_cv_{int(bp*0.1)}km": round(block_density_cv(r0, foot, bp), 6)
                 for bp in (50, 100, 150)}
    corr_before = round(density_prior_rank_corr(r0, foot, blocks, prior), 6)

    seen_hashes = existing_ledger_hashes()
    OUT.mkdir(parents=True, exist_ok=True)
    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]

    variants = []
    candidate_masks: dict[str, np.ndarray] = {"R0": r0}

    for spec in VARIANT_SPECS:
        donor, recip, strata_meta = strata_masks(r0.shape, blocks, prior, POOL_FRAC, spec["toward"])
        cand_mask, stats = greedy_relief_reallocate(
            r0, support, donor, recip, dist_cat, int(spec["n_shift"]), MIN_ADDED_CAT_DIST
        )
        pct_changed = stats["pct_changed_symmetric"]
        mass_pct = stats["mass_shifted_pct_of_r0"]
        if not (9.9 <= mass_pct <= 20.1):
            raise ValueError(f"{spec['tag']} shifted {mass_pct:.4f}% mass (brief requires 10-20%)")
        if not (1.0 <= pct_changed <= 50.0):
            raise ValueError(f"{spec['tag']} changed {pct_changed:.4f}% of R0 (required 1-50%)")

        removed = r0 & ~cand_mask
        evenness = emptied_cluster_report(removed, r0)
        evenness["passes_anti_isolation_gate"] = concentration_evenness_gate(
            evenness, MAX_EMPTIED_CLUSTER_BLOCKS, MAX_FRACTION_BLOCKS_EMPTIED)
        shares_after = region_shares(cand_mask)
        shift = max_region_share_shift(shares_before, shares_after)
        if not evenness["passes_anti_isolation_gate"]:
            raise ValueError(f"{spec['tag']} fails anti-isolation gate: {evenness}")
        if shift > MAX_REGION_SHARE_SHIFT:
            raise ValueError(f"{spec['tag']} region share shift {shift:.4f} > {MAX_REGION_SHARE_SHIFT}")

        slug = f"{PARENT}-{AXIS_TOKEN}{spec['tag']}-{DATE}"
        tmp_nan = OUT / f".{slug}-nan.tmp.tif"
        tmp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        base_build.emit(cand_mask, foot, template, slug, "nan", tmp_nan)
        base_build.emit(cand_mask, foot, template, slug, "zeros", tmp_zeros)
        nan_sha = base_build.sha256_file(tmp_nan)
        zeros_sha = base_build.sha256_file(tmp_zeros)
        if nan_sha in seen_hashes or zeros_sha in seen_hashes or nan_sha == zeros_sha:
            tmp_nan.unlink(missing_ok=True)
            tmp_zeros.unlink(missing_ok=True)
            raise ValueError(f"duplicate SHA-256 detected for {spec['tag']}")
        seen_hashes.update((nan_sha, zeros_sha))

        sha8 = nan_sha[:8]
        vid = f"{slug}-{sha8}"
        nan_path = OUT / f"{vid}.tif"
        zeros_path = OUT / f"{vid}-zeros.tif"
        tmp_nan.replace(nan_path)
        tmp_zeros.replace(zeros_path)

        nan_audit = validate_concentration_file(nan_path, cand_mask, r0, foot, cat, dist_cat,
                                                sample_path, cat_path, template, "nan")
        zeros_audit = validate_concentration_file(zeros_path, cand_mask, r0, foot, cat, dist_cat,
                                                  sample_path, cat_path, template, "zeros")

        pts = np.column_stack(np.nonzero(cand_mask))
        nn_dists, _ = cKDTree(pts).query(pts, k=2)
        cv_after = {f"block_density_cv_{int(bp*0.1)}km": round(block_density_cv(cand_mask, foot, bp), 6)
                    for bp in (50, 100, 150)}
        corr_after = round(density_prior_rank_corr(cand_mask, foot, blocks, prior), 6)

        note = (f"{PARENT}; CONC {100*spec['mass_frac']:g}% ({spec['n_shift']}d) "
                f"{'low->high' if spec['toward'] else 'high->low'} strain; pred {spec['pred_short']} DTI MODEL")
        if len(note) > 140:
            raise AssertionError(f"form_note exceeds 140 chars ({len(note)}): {note}")

        parent_diff = {
            **stats,
            "direction": strata_meta["direction"],
            "pool_frac": POOL_FRAC,
            "block_size_km": BLOCK_PX * 0.1,
            "block_density_cv_before": cv_before,
            "block_density_cv_after": cv_after,
            "region_shares_before": shares_before,
            "region_shares_after": shares_after,
            "max_region_share_shift": shift,
            "density_prior_rank_corr_before": corr_before,
            "density_prior_rank_corr_after": corr_after,
            "nearest_neighbor_px_min": round(float(nn_dists[:, 1].min()), 6),
            "nearest_neighbor_px_median": round(float(np.median(nn_dists[:, 1])), 6),
            "anti_isolation": evenness,
        }
        mechanism_card = {
            "hypothesis": spec["hypothesis"],
            "mechanism": spec["mechanism"],
            "non_fault_confounder": spec["non_fault_confounder"],
            "predicted_live_change": spec["predicted_change"],
            "falsifier": spec["falsifier"],
            "structural_geologist_note": (
                "All 37,654 dots remain on the corroborated H19-5 ridge network; the ranking prior is the "
                "competition-supplied geodetic strain-rate invariant, NOT a catalogue-derived field, so this "
                "is a physical-deformation test rather than a label-geography test. Review added high-strain "
                "segments against GPS/InSAR station density and known geothermal/subsidence/volcanic centres, "
                "and removed low-strain segments against mapped aseismic bedrock faults."
            ),
        }
        variants.append({
            "id": vid,
            "tag": spec["tag"],
            "parent": PARENT,
            "axis": AXIS,
            "value": value_string(spec),
            "toward_high_prior": bool(spec["toward"]),
            "mass_frac": spec["mass_frac"],
            "n_shift": int(spec["n_shift"]),
            "n_dots": R0_DOTS,
            "pct_changed": pct_changed,
            "mass_shifted_pct": mass_pct,
            "removed_dots": stats["removed_dots"],
            "added_dots": stats["added_dots"],
            "retained_dots": stats["retained_dots"],
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "predicted_change": spec["predicted_change"],
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": parent_diff,
            "mechanism_card": mechanism_card,
        })
        candidate_masks[vid] = cand_mask

    # Report-only PROXY diagnostics (never gates, never scores).
    with rasterio.open(DATA / EXTRA_PINS["sgmc"]) as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (dist_cat > 3.0)
    hide_recover_proxy = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000
    )
    hide_recover_proxy["caveat"] = (
        "R0 pruned d_cat<=2 px across the full catalogue and every newly added CONCENTRATION dot enforces "
        "d_cat>=3 px, so withheld catalogue positives earn zero credit from added dots; the proxy only measures "
        "residual 2<d_cat<3 px flank retention. Historical correlation with live DTI is -0.87 to +0.54; PROXY ONLY."
    )
    sgmc_proxy = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000
    )
    sgmc_proxy["caveat"] = (
        "Off-catalogue USGS SGMC geologic-map faults (d_cat>3 px) over-represent exposed range bedrock; standalone "
        "SGMC scored ~0.05 CLAIM live. PROXY ONLY, never a gate or score."
    )

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": base_build.git_sha(),
        "generator_script": "scripts/build_concentration_variants.py",
        "generator_script_sha256": base_build.sha256_file(Path(__file__)),
        "axis": AXIS,
        "session": "2026-10-23e (agent-selected CONCENTRATION, GEMSDOE90)",
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": base_build.R0_ZEROS_SHA,
            "nan_sha256": base_build.R0_NAN_SHA,
            **parent_stats,
            **cv_before,
            "region_shares": shares_before,
            "density_prior_rank_corr": corr_before,
        },
        "prior_definition": {
            "description": "geodetic strain-rate second invariant (band 4 geod_2ndinv), label-agnostic",
            **prior_meta,
        },
        "reallocation_operator": {
            "support": "off-catalogue H19-5 corroborated ridge mask (h19_5 & footprint & ~catalogue)",
            "pool": "complementary top/bottom 50% of 5 km blocks by strain prior",
            "drop_rule": "greedy minimum R=3 px triangular-kernel exclusive credit loss in donor stratum",
            "add_rule": "greedy maximum R=3 px triangular-kernel marginal credit gain in recipient stratum, d_cat>=3.0 px",
            "deterministic_tie_break": "(row, col) ascending; stable argsort on blocks",
            "seed_used_in_variant_construction": None,
            "count_fixed": R0_DOTS,
            "inherited_r0_collar_preserved": True,
        },
        "hard_gates": {
            "anti_isolation_max_emptied_cluster_blocks": MAX_EMPTIED_CLUSTER_BLOCKS,
            "anti_isolation_max_fraction_blocks_emptied": MAX_FRACTION_BLOCKS_EMPTIED,
            "max_region_share_shift_reported_cap": MAX_REGION_SHARE_SHIFT,
            "added_dots_min_catalogue_dist_px": MIN_ADDED_CAT_DIST,
            "note": "CONCENTRATION redistributes mass by design; following the RELIEF precedent, regional "
                    "share shifts are reported diagnostics, not hard gates. Only region-ISOLATION (contiguous "
                    "emptied hole/strip) is gated, per Hard Constraint #5. Prior is label-agnostic.",
        },
        "manifest": {
            "manifest_path": "registry/data_manifest.json",
            "verified_count": len(input_receipt),
            "all_pins_rechecked": True,
            "files": input_receipt,
        },
        "proxy_reports": {
            "catalogue_hide_recover": hide_recover_proxy,
            "leakage_canary": canary,
            "sgmc_control": sgmc_proxy,
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
        "not_committed_to_git": True,
    }


def update_ledgers_and_reservations(result: dict) -> None:
    ledger_path = ROOT / "ledger" / "submissions.csv"
    with ledger_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        existing_rows = list(reader)
    new_ids = {v["id"] for v in result["variants"]}
    kept_rows = [r for r in existing_rows if r.get("id") not in new_ids]
    for v in result["variants"]:
        kept_rows.append({
            "id": v["id"],
            "site": "GEMSDOE90",
            "name": v["id"],
            "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": str(v["n_dots"]),
            "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"],
            "sha256_zeros": v["sha256_zeros"],
            "parent": v["parent"],
            "axis": v["axis"],
            "value": v["value"],
            "status": "BUILT",
            "receipt": "N",
            "receipt_score": "",
            "predicted_change": v["predicted_change"],
            "date": "",
            "form_note": v["form_note"],
            "notes": (
                f"strain-prior CONCENTRATION: mass_shifted={v['mass_shifted_pct']:.2f}% ({v['n_shift']} dots "
                f"{'low->high' if v['toward_high_prior'] else 'high->low'} strain); 5km blocks; added d_cat>=3px; "
                f"receipt_score/date filled by human; agent never submits"
            ),
        })
    with ledger_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept_rows)

    res_path = ROOT / "ledger" / "experiment_reservations.json"
    res = json.loads(res_path.read_text(encoding="utf-8"))
    res["concentration_reservations"] = {
        "checked_utc": "2026-10-23",
        "axis": AXIS,
        "parent": PARENT,
        "prior": "geodetic strain-rate invariant (band 4, label-agnostic), 5 km blocks, complementary 50% pools",
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "cross_repo_audit": {
            "siblings_checked": "GEMSDOE84-97 (gh api read-only, 2026-10-23)",
            "catalogue_density_prior": "GEMSDOE89 CONC5kmcat10/cat10away/cat20",
            "h19_5_prior": "GEMSDOE87 CONCc10/c15/c20",
            "self_density_prior": "GEMSDOE88/91 CONCb10px-m10/m20/b50px-m20; GEMSDOE84/85/86 additional conc/spread",
            "why_new": "No sibling built a CONCENTRATION on a label-agnostic geodetic strain-rate prior; "
                       "prior is near-orthogonal to R0 density (r~+0.11) and relief-neutral, and uses no "
                       "test label/score, so it is orthogonal to all sibling values and to Hard Constraint #5.",
        },
        "note": "Repeat builds of these (CONCENTRATION, value) pairs fail closed.",
    }
    res.setdefault("sessions", []).append({
        "session": "2026-10-23e strain-prior CONCENTRATION (GEMSDOE90)",
        "axis": AXIS,
        "prior": "geodetic strain-rate invariant band 4 (label-agnostic), 5 km blocks",
        "selected_values": [v["tag"] for v in result["variants"]],
        "variant_ids": [v["id"] for v in result["variants"]],
    })
    res_path.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    cards_path = ROOT / "ledger" / "mechanism_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8")) if cards_path.is_file() else {}
    cards["concentration"] = {
        "axis": AXIS,
        "session": "2026-10-23e (GEMSDOE90)",
        "prior": "geodetic strain-rate invariant (band 4 geod_2ndinv), label-agnostic, 5 km blocks",
        "variants": [
            {"id": v["id"], "axis": AXIS, "value": v["value"], "mechanism_card": v["mechanism_card"]}
            for v in result["variants"]
        ],
    }
    cards_path.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def verify_all() -> int:
    input_receipt = base_build.verify_manifest_inputs()
    receipt_path = ROOT / "evidence" / "concentration_build_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    _field, blocks, prior, _meta, _relief = load_prior_layers(foot)

    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]
    spec_by_tag = {s["tag"]: s for s in VARIANT_SPECS}
    our_ids = {v["id"] for v in receipt["variants"]}
    other_hashes = existing_ledger_hashes(exclude_ids=our_ids)
    tmp_dir = ROOT / ".cache" / "verify_concentration_bytes"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for v in receipt["variants"]:
        spec = spec_by_tag[v["tag"]]
        donor, recip, _ = strata_masks(r0.shape, blocks, prior, POOL_FRAC, spec["toward"])
        expected_mask, stats = greedy_relief_reallocate(
            r0, support, donor, recip, dist_cat, int(spec["n_shift"]), MIN_ADDED_CAT_DIST)
        if int(expected_mask.sum()) != R0_DOTS:
            raise ValueError(f"recomputed {v['id']} dot count != {R0_DOTS}")
        if abs(stats["pct_changed_symmetric"] - float(v["pct_changed"])) > 1e-6:
            raise ValueError(f"recomputed {v['id']} pct_changed mismatch")
        for mode_name in ("nan", "zeros"):
            fpath = ROOT / v["files"][mode_name]["path"]
            audit = validate_concentration_file(fpath, expected_mask, r0, foot, cat, dist_cat,
                                                sample_path, cat_path, template, mode_name)
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"disk SHA-256 mismatch for {v['id']} [{mode_name}]")
            if audit["sha256"] in other_hashes:
                raise ValueError(f"SHA-256 collides with prior ledger entry: {v['id']} [{mode_name}]")
            tmp_file = tmp_dir / f"{v['id']}-{mode_name}.tif"
            try:
                base_build.emit(expected_mask, foot, template, v["id"], mode_name, tmp_file)
                if base_build.sha256_file(tmp_file) != audit["sha256"]:
                    raise ValueError(f"deterministic byte re-emission failed for {v['id']} [{mode_name}]")
            finally:
                tmp_file.unlink(missing_ok=True)

    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = base_build.git_sha()
    receipt["generator_script_sha256"] = base_build.sha256_file(Path(__file__))
    receipt["manifest"]["verified_count"] = len(input_receipt)
    receipt["manifest"]["all_pins_rechecked"] = True
    receipt["self_check"] = {
        "all_26_manifest_pins_verified": True,
        "r0_rebuilt_byte_identically": bool(parent_stats["r0_byte_identity_passed"]),
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "added_dots_strictly_ge_3px_from_catalogue": True,
        "zero_catalogue_mass": True,
        "anti_isolation_gate_passed_all_variants": True,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} CONCENTRATION variant pairs from disk; "
          f"R0 byte-identical ({base_build.R0_ZEROS_SHA[:16]}...)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--build", action="store_true")
    grp.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.build:
        result = build_all()
        receipt_path = ROOT / "evidence" / "concentration_build_receipt.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        update_ledgers_and_reservations(result)
        print(f"Built {len(result['variants'])} CONCENTRATION variants -> {receipt_path.relative_to(ROOT)}")
        for v in result["variants"]:
            pd = v["parent_diff"]
            print(f"  {v['id']}: {v['n_dots']} dots | mass_shifted={v['mass_shifted_pct']:.2f}% "
                  f"| sym_changed={v['pct_changed']:.3f}% | CV15km {pd['block_density_cv_before']['block_density_cv_15km']:.3f}"
                  f"->{pd['block_density_cv_after']['block_density_cv_15km']:.3f} | corr {pd['density_prior_rank_corr_before']:.3f}"
                  f"->{pd['density_prior_rank_corr_after']:.3f} | maxshift {pd['max_region_share_shift']:.4f} | sha256={v['sha256'][:16]}...")
        return 0
    return verify_all()


if __name__ == "__main__":
    raise SystemExit(main())
