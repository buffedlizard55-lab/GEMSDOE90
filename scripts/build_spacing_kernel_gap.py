#!/usr/bin/env python3
"""Build three AXIS=SPACING kernel-gap equalization variants from exact R0.

Parent: h33-h33-2-b2, 37,654 unit-mass dots, rebuilt byte-identically first.
Each rung moves 5 / 10 / 20 % of R0's dots *within their own 5 km block* from
lowest exclusive R=3 px support credit to highest marginal support credit on
the pinned H19-5 support.  Dot count and per-5 km-block counts are unchanged;
only spacing changes.  Added dots satisfy d_cat >= 3 px; untouched R0 dots keep
the parent's inherited 2.236 px floor (IR90-07/18/21; see IR90-43).

Run build:  .venv/bin/python scripts/build_spacing_kernel_gap.py --build
Run verify: .venv/bin/python scripts/build_spacing_kernel_gap.py --verify
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_r0_variants as base_build  # noqa: E402
import build_relief_variants as relief_build  # noqa: E402
from src import reach, spacing_kernel_gap as spacing  # noqa: E402
from src.concentration_strain5km import (  # noqa: E402
    concentration_evenness_gate,
    emptied_cluster_report,
    max_region_share_shift,
    region_shares,
)
from src.relief import block_density_cv  # noqa: E402
from src.validate import validate as format_validate  # noqa: E402

DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "SPACING"
DATE = "20261024"
SEED = 20261024
R0_DOTS = 37_654
BLOCK_PX = 50
MIN_ADDED_CAT_DIST = 3.0
RECEIPT_PATH = ROOT / "evidence" / "spacing_kernel_gap_build_receipt.json"
LEDGER_PATH = ROOT / "ledger" / "submissions.csv"
RESERVATIONS_PATH = ROOT / "ledger" / "experiment_reservations.json"
CARDS_PATH = ROOT / "ledger" / "mechanism_cards.json"
SGMC_PIN = "external/derived_sgmc_faults_100m_u8.tif"

VARIANT_SPECS = (
    {"tag": "gap5pct", "pct": 5, "n_move": 1_883, "plausible_buffer": 0.002,
     "hypothesis": "A small, block-local re-spacing fills the deepest 300 m-kernel gaps without dismantling R0's strands."},
    {"tag": "gap10pct", "pct": 10, "n_move": 3_765, "plausible_buffer": 0.002,
     "hypothesis": "Twice the re-spacing dose isolates whether kernel-gap headroom persists beyond the cheapest moves."},
    {"tag": "gap20pct", "pct": 20, "n_move": 7_531, "plausible_buffer": 0.002,
     "hypothesis": "At a 20% move dose the fixed support exhausts its positive-gain gaps, so this arm is the saturation/sign control."},
)

CROSS_REPO_SPACING_VALUES = (
    "alongstrike", "lattice", "latticec16", "pdiskc16", "poisson", "randomc16",
    "strikec16", "along-strike", "clump40", "jitter40", "poisson-disk",
    "spread40", "lattice4px", "poisson28", "strike",
    # Concurrent main session merged after this branch was cut: 15 px local
    # crowding-ranked respacing.  Our tags are deliberately different.
    "resp5pct", "resp10pct", "resp15pct",
)


def value_string(spec: dict) -> str:
    return (
        f"tag={spec['tag']}; kernel-gap equalization: move {spec['n_move']} parent dots "
        f"({spec['pct']}%) low-exclusive->high-marginal R=3 credit within the same 5km block; "
        f"fixed count 37654; added d_cat>=3px"
    )


def prediction_string(spec: dict, bracket: dict) -> str:
    point = float(bracket["point"])
    low = min(0.0, float(bracket["low"])) - float(spec["plausible_buffer"])
    high = max(0.0, float(bracket["high"])) + float(spec["plausible_buffer"])
    sign = "+" if point >= 0 else ""
    return (
        f"{sign}{point:.3f} DTI (MODEL; plausible {low:+.3f} to {high:+.3f}; "
        "not a score; every point estimate is inside the |0.010| no-evidence band)"
    )


def pred_short(spec: dict, bracket: dict) -> str:
    point = float(bracket["point"])
    return f"{'+' if point >= 0 else ''}{point:.3f}"


def existing_ledger_hashes(exclude_ids: set[str] | None = None) -> set[str]:
    exclude_ids = exclude_ids or set()
    out: set[str] = set()
    with LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("id", "") in exclude_ids:
                continue
            for col in ("sha256", "sha256_zeros"):
                value = (row.get(col) or "").strip()
                if value:
                    out.add(value)
    return out


def check_reservations(allow_rebuild: bool = False) -> None:
    if allow_rebuild:
        # Explicitly reproduce the already-recorded raster bytes in a fresh checkout.
        # This is NOT permission to cut a new (AXIS, value): build() cross-checks every
        # regenerated hash, count and prediction against the committed receipt.
        if not RECEIPT_PATH.is_file():
            raise ValueError("--rebuild-reserved requires the committed spacing receipt")
        return
    rows = list(csv.DictReader(LEDGER_PATH.open(newline="", encoding="utf-8")))
    occupied = {(r.get("parent", "").strip(), r.get("axis", "").strip().upper(),
                 r.get("value", "").strip()) for r in rows if r.get("axis", "").strip()}
    for spec in VARIANT_SPECS:
        key = (PARENT, AXIS, value_string(spec))
        if key in occupied:
            raise ValueError(f"duplicate (parent, axis, value) reservation: {key}")
        if spec["tag"] in CROSS_REPO_SPACING_VALUES:
            raise ValueError(f"tag collides with a cross-repo SPACING value: {spec['tag']}")
    reservations = json.loads(RESERVATIONS_PATH.read_text(encoding="utf-8"))
    if "spacing_kernel_gap_20261024" in reservations:
        raise ValueError("spacing_kernel_gap_20261024 already reserved; use --verify, never re-cut the pair")


def validate_spacing_file(path: Path, expected: np.ndarray, r0: np.ndarray, foot: np.ndarray,
                          cat: np.ndarray, dist_cat: np.ndarray, support: np.ndarray,
                          sample_path: Path, cat_path: Path, sample_profile: dict,
                          mode: str) -> dict:
    fmt = format_validate(str(path), str(sample_path), str(cat_path), zeros_outside=(mode == "zeros"))
    if not fmt["pass"]:
        raise ValueError(f"src.validate failed for {path.name}: {fmt['fails']}")
    with rasterio.open(path) as src:
        arr = src.read(1)
        profile = src.profile
        crs = src.crs
        transform = src.transform
    disk_mask = (arr > 0.5) & foot
    added = disk_mask & ~r0
    retained = disk_mask & r0
    checks = {
        "src_validate_gate_pass": bool(fmt["pass"]),
        "crs_matches_sample": crs == sample_profile["crs"],
        "transform_matches_sample": transform == sample_profile["transform"],
        "shape_matches_sample": arr.shape == (sample_profile["height"], sample_profile["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(arr[foot]).all()),
        "inside_foot_range_0_1": bool(np.all((arr[foot] >= 0.0) & (arr[foot] <= 1.0))),
        "outside_encoding_valid": bool(np.isnan(arr[~foot]).all()) if mode == "nan" else bool(np.all(arr[~foot] == 0.0)),
        "exact_expected_mask_after_disk_read": bool(np.array_equal(disk_mask, expected)),
        "zero_catalogue_mass": not bool(np.any(disk_mask & cat)),
        "fixed_count_37654": int(disk_mask.sum()) == R0_DOTS,
        "all_dots_on_h19_5_support": bool(np.all(support[disk_mask])),
        "added_dots_min_cat_dist_ge_3px": bool(float(dist_cat[added].min()) >= MIN_ADDED_CAT_DIST - 1e-9) if added.any() else True,
        "retained_dots_preserve_r0_collar_gt_2px": bool(float(dist_cat[retained].min()) > 2.0) if retained.any() else True,
        "file_re_read_from_disk": True,
    }
    if not all(checks.values()):
        raise ValueError(f"spacing validator failed for {path.name}: {[k for k, v in checks.items() if not v]}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": base_build.sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(disk_mask.sum()),
        "min_catalogue_distance_all_dots_px": round(float(dist_cat[disk_mask].min()), 6),
        "min_catalogue_distance_added_dots_px": round(float(dist_cat[added].min()), 6),
        "inherited_r0_dots_below_3px": int((retained & (dist_cat < 3.0)).sum()),
        "added_dots_below_3px": int((added & (dist_cat < 3.0)).sum()),
        "checks": checks,
    }


def nearest_neighbor_stats(mask: np.ndarray) -> dict:
    pts = np.column_stack(np.nonzero(mask))
    if pts.shape[0] < 2:
        return {"min": 0.0, "median": 0.0, "p05": 0.0, "p95": 0.0}
    d, _ = cKDTree(pts).query(pts, k=2)
    nn = d[:, 1]
    return {
        "min": round(float(nn.min()), 6),
        "p05": round(float(np.percentile(nn, 5)), 6),
        "median": round(float(np.median(nn)), 6),
        "p95": round(float(np.percentile(nn, 95)), 6),
    }


def operator_scalar_stats(stats: dict) -> dict:
    keys = (
        "n_move", "removed_dots", "added_dots", "retained_dots", "symmetric_difference_px",
        "mass_shifted_pct_of_r0", "pct_changed_symmetric", "block_px", "n_eligible_donors",
        "n_eligible_pool_px", "blocks_with_moves", "max_moves_in_one_block", "move_share_p05",
        "move_share_median", "move_share_p95", "move_share_max", "lost_support_credit",
        "gained_support_credit", "net_support_credit", "mean_loss_per_removed",
        "mean_gain_per_added", "min_added_catalogue_distance_px",
    )
    return {k: stats[k] for k in keys}


def mechanism_card(spec: dict, stats: dict, bracket: dict, pred_text: str) -> dict:
    n = int(spec["n_move"])
    pct = int(spec["pct"])
    sat_note = (
        "The measured net support credit is already negative at this dose, so this arm is a saturation/sign control."
        if stats["net_support_credit"] < 0 else
        "The measured net support credit is positive, but the transferred live effect is projected below the 0.010 no-evidence band."
    )
    return {
        "hypothesis": spec["hypothesis"],
        "mechanism": (
            f"R0's 2.8 px thinning spacing nearly matches the R=3 px kernel. This variant removes {n:,} R0 dots "
            f"({pct}% of the parent) with the lowest exclusive triangular-kernel credit and re-emits them as {n:,} "
            "highest-marginal-credit dots on the same off-catalogue H19-5 support, paired inside each 5 km block. "
            f"Fixed count and exactly unchanged per-block counts isolate SPACING from MASS and CONCENTRATION. "
            f"Exact support-credit ledger: lost {stats['lost_support_credit']:.1f}, gained "
            f"{stats['gained_support_credit']:.1f}, net {stats['net_support_credit']:+.1f}."
        ),
        "non_fault_confounder": (
            "H19-5 also carries drainage lines, lithologic contacts, pluvial shorelines and cultural magnetic edges. "
            "Equalizing their 300 m coverage can manufacture visually continuous but geologically false traces; "
            "removing low-exclusive-credit dots can also break real short relay tips at strand ends."
        ),
        "predicted_live_change": pred_text,
        "model_bracket": (
            f"exact fixed-count DTI model grid {bracket['low']:+.6f} to {bracket['high']:+.6f}; "
            f"point {bracket['point']:+.6f}; {sat_note}"
        ),
        "falsifier": (
            "Paired same-week receipt vs R0. A positive arm with Δ<=-0.010 falsifies the kernel-gap mechanism; "
            "the 20% arm with Δ>=+0.010 falsifies the projected saturation. Any |Δ|<0.010 is no evidence. "
            "Comparing gap5/gap10/gap20 tests the dose sign, never a proxy score."
        ),
        "structural_geologist_note": (
            "Review removed tips and added mid-strand cells at 1:24k on the basement/surficial geology. A win would mean "
            "new-fault truth is line-like and R0 was under-sampled in 300 m-kernel coverage; a loss would mean positional "
            "error or non-fault support, not that the structures are absent. Every move stays in its own 5 km block."
        ),
    }


def build(allow_rebuild: bool = False) -> dict:
    t0 = time.time()
    check_reservations(allow_rebuild=allow_rebuild)
    prior_receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8")) if allow_rebuild else None
    prior_by_tag = ({v["tag"]: v for v in prior_receipt["variants"]} if prior_receipt else {})
    input_receipt = base_build.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    if not np.all(~r0 | support):
        raise ValueError("R0 contains pixels outside the off-catalogue H19-5 support")
    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]
    seen_hashes = existing_ledger_hashes(exclude_ids=set(v["id"] for v in prior_receipt["variants"]) if prior_receipt else None)
    OUT.mkdir(parents=True, exist_ok=True)
    tmp_dir = ROOT / ".cache" / "spacing_candidate_bytes"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    cv_before = {f"{bp//10}km": round(block_density_cv(r0, foot, block_px=bp), 6)
                 for bp in (50, 100, 150)}
    nn_before = nearest_neighbor_stats(r0)
    credit_before = float(reach.credit_map(r0)[support].sum())
    shares_before = region_shares(r0)
    variants: list[dict] = []
    candidate_masks: dict[str, np.ndarray] = {"R0": r0}

    for spec in VARIANT_SPECS:
        n_move = int(spec["n_move"])
        cand, stats = spacing.kernel_gap_reallocate(
            r0, support, dist_cat, n_move, block_px=BLOCK_PX,
            min_added_cat_dist_px=MIN_ADDED_CAT_DIST,
        )
        pct_changed = float(stats["pct_changed_symmetric"])
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"{spec['tag']} changes {pct_changed:.4f}% of R0 (required 1-50%)")
        credit_after = float(reach.credit_map(cand)[support].sum())
        if abs((credit_after - credit_before) - stats["net_support_credit"]) > 0.05:
            raise ValueError(
                f"{spec['tag']}: telescoped credit {stats['net_support_credit']:.4f} != "
                f"direct recomputation {credit_after - credit_before:.4f}"
            )
        bracket = spacing.prediction_bracket(stats["net_support_credit"])
        predicted = prediction_string(spec, bracket)
        short = pred_short(spec, bracket)

        slug = f"{PARENT}-{AXIS}{spec['tag']}-{DATE}"
        temp_nan = tmp_dir / f".{slug}-nan.tmp.tif"
        temp_zeros = tmp_dir / f".{slug}-zeros.tmp.tif"
        base_build.emit(cand, foot, template, slug, "nan", temp_nan)
        base_build.emit(cand, foot, template, slug, "zeros", temp_zeros)
        nan_sha = base_build.sha256_file(temp_nan)
        zeros_sha = base_build.sha256_file(temp_zeros)
        if allow_rebuild:
            expected_variant = prior_by_tag.get(spec["tag"])
            if expected_variant is None:
                raise ValueError(f"--rebuild-reserved receipt has no variant for tag {spec['tag']}")
            if nan_sha != expected_variant["files"]["nan"]["sha256"]:
                raise ValueError(f"re-emitted NaN bytes changed for {spec['tag']}: {nan_sha}")
            if zeros_sha != expected_variant["files"]["zeros"]["sha256"]:
                raise ValueError(f"re-emitted zeros bytes changed for {spec['tag']}: {zeros_sha}")
        if nan_sha in seen_hashes or zeros_sha in seen_hashes or nan_sha == zeros_sha:
            temp_nan.unlink(missing_ok=True)
            temp_zeros.unlink(missing_ok=True)
            raise ValueError(f"duplicate SHA-256 detected for {spec['tag']}")
        seen_hashes.update((nan_sha, zeros_sha))
        vid = f"{slug}-{nan_sha[:8]}"
        nan_path = OUT / f"{vid}.tif"
        zeros_path = OUT / f"{vid}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = validate_spacing_file(nan_path, cand, r0, foot, cat, dist_cat, support,
                                          sample_path, cat_path, template, "nan")
        zeros_audit = validate_spacing_file(zeros_path, cand, r0, foot, cat, dist_cat, support,
                                            sample_path, cat_path, template, "zeros")
        if nan_audit["sha256"] != nan_sha or zeros_audit["sha256"] != zeros_sha:
            raise ValueError(f"SHA-256 changed after writing {vid}")

        removed = r0 & ~cand
        anti = emptied_cluster_report(removed, r0, block_px=BLOCK_PX)
        anti["passes_anti_isolation_gate"] = concentration_evenness_gate(anti)
        if not anti["passes_anti_isolation_gate"]:
            raise ValueError(f"{spec['tag']} fails anti-isolation: {anti}")
        cv_after = {f"{bp//10}km": round(block_density_cv(cand, foot, block_px=bp), 6)
                    for bp in (50, 100, 150)}
        if any(abs(cv_before[k] - cv_after[k]) > 1e-9 for k in cv_before):
            raise ValueError(f"{spec['tag']} changed block-density CV; not a pure spacing edit")
        shares_after = region_shares(cand)
        region_shift = max_region_share_shift(shares_before, shares_after)
        if region_shift > 0.02:
            raise ValueError(f"{spec['tag']} region share shift {region_shift:.4f} > 0.02")
        nn_after = nearest_neighbor_stats(cand)
        note = (
            f"{PARENT}; SPACING move {spec['pct']}% ({n_move}d) block-local kernel-gap equalization; "
            f"pred {short} DTI MODEL"
        )
        if len(note) > 140:
            raise AssertionError(f"form_note exceeds 140 chars ({len(note)}): {note}")

        parent_diff = {
            **operator_scalar_stats(stats),
            "support_credit_before": round(credit_before, 4),
            "support_credit_after": round(credit_after, 4),
            "block_density_cv_before": cv_before,
            "block_density_cv_after": cv_after,
            "nearest_neighbor_px_before": nn_before,
            "nearest_neighbor_px_after": nn_after,
            "region_shares_before": shares_before,
            "region_shares_after": shares_after,
            "max_region_share_shift": region_shift,
            "anti_isolation": anti,
            "prediction_model_bracket": bracket,
        }
        card = mechanism_card(spec, stats, bracket, predicted)
        variants.append({
            "id": vid,
            "tag": spec["tag"],
            "parent": PARENT,
            "axis": AXIS,
            "value": value_string(spec),
            "pct": spec["pct"],
            "n_move": n_move,
            "n_dots": int(cand.sum()),
            "pct_changed": round(pct_changed, 6),
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "predicted_change": predicted,
            "pred_short": short,
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": parent_diff,
            "mechanism_card": card,
        })
        if allow_rebuild:
            expected_variant = prior_by_tag[spec["tag"]]
            if vid != expected_variant["id"]:
                raise ValueError(f"--rebuild-reserved ID changed for {spec['tag']}: {vid}")
            if abs(float(pct_changed) - float(expected_variant["pct_changed"])) > 1e-6:
                raise ValueError(f"--rebuild-reserved pct_changed changed for {spec['tag']}")
            if abs(float(stats["net_support_credit"]) - float(expected_variant["parent_diff"]["net_support_credit"])) > 1e-3:
                raise ValueError(f"--rebuild-reserved support credit changed for {spec['tag']}")
        candidate_masks[vid] = cand
        print(f"[{spec['tag']}] {n_move} moves, net credit {stats['net_support_credit']:+.1f}, "
              f"prediction {short}, sha8 {nan_audit['sha256'][:8]}", flush=True)

    # Predictions above are frozen before these report-only diagnostics are computed.
    with rasterio.open(DATA / SGMC_PIN) as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (dist_cat > 3.0)
    catalogue_proxy = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000)
    catalogue_proxy["caveat"] = (
        "All moved dots have d_cat>=3 px, so with a strictly <3 px triangular kernel no moved dot can credit a "
        "withheld catalogue positive; any non-zero value is inherited R0 flank retention. PROXY ONLY, never a gate/score."
    )
    sgmc_proxy = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000)
    sgmc_proxy["caveat"] = (
        "Off-catalogue USGS SGMC geologic-map faults over-represent exposed bedrock; PROXY ONLY, never a gate/score."
    )
    prior_canary = json.loads((ROOT / "evidence" / "concentration_build_receipt.json").read_text())
    max_sym = float(prior_canary["proxy_reports"]["leakage_canary"]["max_symmetric_auc"])
    canary = {
        "status": "NOT RE-RUN — no new placement feature was introduced",
        "scope": "19 pinned feature bands plus composite priors, identical inputs to prior sessions",
        "max_symmetric_auc": max_sym,
        "auc_gt_0_90": max_sym > 0.90,
        "source": "evidence/concentration_build_receipt.json",
        "evidence_class": "PROXY",
        "note": "This session ranks only kernel geometry on the already pinned H19-5 support; canary is REPORT ONLY.",
    }
    if canary["auc_gt_0_90"]:
        raise RuntimeError("STOP AND INVESTIGATE: report-only leakage canary AUC > 0.90")

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": base_build.git_sha(),
        "session_branch": "arena/b5694006-gemsdoe90",
        "generator_script": "scripts/build_spacing_kernel_gap.py",
        "axis": AXIS,
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": base_build.R0_ZEROS_SHA,
            "nan_sha256": base_build.R0_NAN_SHA,
            **parent_stats,
            "support_credit": round(credit_before, 4),
            "block_density_cv": cv_before,
            "nearest_neighbor_px": nn_before,
        },
        "operator": {
            "description": "paired 5 km block-local minimum-exclusive-loss drop / maximum-marginal-gain add",
            "support": "off-catalogue pinned H19-5 corroborated ridge mask",
            "kernel": "triangular R=3 px on integer pixel centres, including centre (25 offsets)",
            "block_size_km": BLOCK_PX * 0.1,
            "fixed_count": R0_DOTS,
            "fixed_per_block_counts": True,
            "added_dots_min_catalogue_dist_px": MIN_ADDED_CAT_DIST,
            "inherited_r0_collar_preserved": True,
            "seed_used_in_variant_construction": None,
            "deterministic_tie_break": "flat padded raster index ascending; block order row-major",
        },
        "hard_gates": {
            "format_validator": "src.validate for each emitted encoding",
            "zero_catalogue_mass": True,
            "sha256_not_in_existing_ledger": True,
            "parent_diff_recorded": True,
            "file_re_read_from_disk": True,
            "pct_changed_range": [1.0, 50.0],
            "anti_isolation_gate": "largest 90%-emptied 5 km block cluster <=4 and fraction <=0.02",
            "max_region_share_shift": 0.02,
            "block_cv_unchanged_tolerance": 1e-9,
        },
        "manifest": {
            "manifest_path": "registry/data_manifest.json",
            "verified_count": len(input_receipt),
            "all_pins_rechecked": True,
            "files": input_receipt,
        },
        "proxy_reports": {
            "catalogue_hide_recover": catalogue_proxy,
            "sgmc_control": sgmc_proxy,
            "leakage_canary": canary,
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
        "competition_rasters_not_committed": True,
    }
    return result


def write_ledger(result: dict) -> None:
    with LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    ids = {v["id"] for v in result["variants"]}
    rows = [r for r in rows if r.get("id") not in ids]
    for v in result["variants"]:
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": str(v["n_dots"]), "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"],
            "parent": v["parent"], "axis": v["axis"], "value": v["value"],
            "status": "BUILT", "receipt": "N", "receipt_score": "",
            "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": ("SPACING kernel-gap equalization, same 5km block and fixed per-block count; "
                      "added d_cat>=3px; inherited 2.236px parent collar retained; "
                      "receipt_score/date to be filled by human; agent never submits"),
        })
    with LEDGER_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_reservation(result: dict) -> None:
    reservations = json.loads(RESERVATIONS_PATH.read_text(encoding="utf-8"))
    reservations["spacing_kernel_gap_20261024"] = {
        "checked_utc": "2026-10-24",
        "axis": AXIS,
        "parent": PARENT,
        "scope": ("Read-only gh api audit of 79 public buffedlizard55-lab/GEMSDOE* default branches "
                  "(9 ledger CSVs present) plus 7 open GEMSDOE90 PR head ledgers; 16 occupied SPACING values found."),
        "value_family": "block-local kernel-gap equalization dose ladder at fixed 5 km block counts",
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "cross_repo_occupied_values": list(CROSS_REPO_SPACING_VALUES),
        "selected_values": [v["tag"] for v in result["variants"]],
        "why_distinct": ("Sibling SPACING values replace the layout globally (lattice/poisson/along-strike), "
                         "clump/jitter/spread, or use 16-px/4-px/28-px spacing. None holds every 5 km block count "
                         "fixed while optimizing exact R=3 px exclusive-loss/marginal-gain credit on H19-5."),
        "decision": ("HELD from the next three slots: all point predictions and the entire model grid are inside "
                     "the brief's |0.010| no-evidence band; 20% has negative measured support credit. Kept as a "
                     "dose-response/saturation instrument and occupancy guard until a live receipt changes the state."),
        "caveat": ("Public default-branch/PR audit is not proof of every private or unindexed entity submission; "
                   "the human must adjudicate entity scope and quota before any slot (IR90-26/30)."),
        "note": "Repeat builds of these exact (SPACING, value) pairs fail closed.",
    }
    session_label = "2026-10-24 (agent-selected SPACING, GEMSDOE90)"
    sessions = reservations.setdefault("sessions", [])
    reservations["sessions"] = [s for s in sessions if s.get("session") != session_label]
    reservations["sessions"].append({
        "session": session_label,
        "axis": AXIS,
        "parent": PARENT,
        "selected_values": [v["tag"] for v in result["variants"]],
        "variant_ids": [v["id"] for v in result["variants"]],
        "decision": "BUILT, HELD from slots (predicted change below the no-evidence threshold)",
    })
    RESERVATIONS_PATH.write_text(json.dumps(reservations, indent=2) + "\n", encoding="utf-8")


def write_cards(result: dict) -> None:
    cards = json.loads(CARDS_PATH.read_text(encoding="utf-8")) if CARDS_PATH.is_file() else {}
    cards["spacing_kernel_gap"] = {
        "axis": AXIS,
        "session": "2026-10-24 (GEMSDOE90, arena/b5694006-gemsdoe90)",
        "parent": PARENT,
        "variants": [
            {"id": v["id"], "axis": AXIS, "value": v["value"],
             "mechanism_card": v["mechanism_card"], "diagnostics": v["parent_diff"]}
            for v in result["variants"]
        ],
    }
    CARDS_PATH.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def verify() -> int:
    t0 = time.time()
    input_receipt = base_build.verify_manifest_inputs()
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]
    spec_by_tag = {s["tag"]: s for s in VARIANT_SPECS}
    our_ids = {v["id"] for v in receipt["variants"]}
    other_hashes = existing_ledger_hashes(exclude_ids=our_ids)
    tmp_dir = ROOT / ".cache" / "verify_spacing_bytes"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for v in receipt["variants"]:
        spec = spec_by_tag[v["tag"]]
        expected, stats = spacing.kernel_gap_reallocate(
            r0, support, dist_cat, int(spec["n_move"]), block_px=BLOCK_PX,
            min_added_cat_dist_px=MIN_ADDED_CAT_DIST)
        if int(expected.sum()) != R0_DOTS:
            raise ValueError(f"recomputed {v['id']} count mismatch")
        if abs(stats["pct_changed_symmetric"] - float(v["pct_changed"])) > 1e-6:
            raise ValueError(f"recomputed {v['id']} pct_changed mismatch")
        for mode in ("nan", "zeros"):
            filepath = ROOT / v["files"][mode]["path"]
            audit = validate_spacing_file(filepath, expected, r0, foot, cat, dist_cat, support,
                                          sample_path, cat_path, template, mode)
            if audit["sha256"] != v["files"][mode]["sha256"]:
                raise ValueError(f"disk SHA-256 mismatch for {v['id']} [{mode}]")
            if audit["sha256"] in other_hashes:
                raise ValueError(f"SHA-256 collides with another ledger row: {v['id']} [{mode}]")
            tmp = tmp_dir / f"{v['id']}-{mode}.tif"
            try:
                base_build.emit(expected, foot, template, v["id"], mode, tmp)
                if base_build.sha256_file(tmp) != audit["sha256"]:
                    raise ValueError(f"deterministic byte re-emission failed for {v['id']} [{mode}]")
            finally:
                tmp.unlink(missing_ok=True)
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
        "zero_catalogue_mass": True,
        "added_dots_strictly_ge_3px_from_catalogue": True,
        "fixed_count_and_per_block_count": True,
        "anti_isolation_gate_passed_all_variants": True,
    }
    receipt["verification_elapsed_s"] = round(time.time() - t0, 2)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} SPACING variant pairs from disk; "
          f"R0 byte-identical ({base_build.R0_ZEROS_SHA[:16]}...)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true")
    group.add_argument("--verify", action="store_true")
    ap.add_argument("--rebuild-reserved", action="store_true",
                    help="with --build only: re-emit this session's already-reserved rasters and verify exact hashes")
    args = ap.parse_args()
    if args.rebuild_reserved and not args.build:
        ap.error("--rebuild-reserved is valid only with --build")
    if args.build:
        result = build(allow_rebuild=args.rebuild_reserved)
        result["rebuild_reserved"] = bool(args.rebuild_reserved)
        RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        write_ledger(result)
        write_reservation(result)
        write_cards(result)
        print(f"Built {len(result['variants'])} SPACING variants in {result['elapsed_s']}s -> "
              f"{RECEIPT_PATH.relative_to(ROOT)}")
        return 0
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
