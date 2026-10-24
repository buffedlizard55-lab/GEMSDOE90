#!/usr/bin/env python3
"""Execute the frozen 3-experiment Lane H90 pipeline end-to-end (memory-streaming):
1. Verify pinned inputs & construct shared gems57 hide-and-recover segment holdout.
2. Extract/mmap 36 static multi-physics features (zero prior submission rasters read).
3. Run Protocol Rule #4 single-feature leakage canary (require symmetric AUC <= 0.90).
4. Evaluate Frozen Experiments 1, 2, 3 + leak-free baselines (C0, C1) + fold-fair R0 ref
   via shared vendor/gems57/evaluate_holdout.py (gems57-pooled-hide-v2, 20 km block CI).
5. Audit pre-placement surface & final dots uniqueness against 20 registry/sibling rasters
   and 118+ ledger SHA-256 digests (Protocol Rule #1).
6. Package validated unique GeoTIFF + single-TIFF ZIP via vendor/gems57/submission_writer.py.
7. Run self-contained automated validation gate & emit Protocol Rule #5 JSON Run Card.
"""

from __future__ import annotations

import gc
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.auto_validator import (  # noqa: E402
    audit_surface_and_dots_uniqueness,
    build_registry_index,
    run_automated_submission_gate,
)
from src.h90_emitter import (  # noqa: E402
    celf_submodular_emit,
    greedy_spacing_emit,
    random_isolated_emit,
)
from src.h90_features import extract_static_features_fp  # noqa: E402
from src.h90_models import (  # noqa: E402
    build_classical_ridge_surface,
    build_exp1_unsupervised_surface,
    fit_predict_exp2_and_exp3,
    predict_exp3_cell_surface_crop,
    run_leakage_canary,
)
from vendor.gems57 import evaluate_holdout, holdout, metric, submission_writer  # noqa: E402
from vendor.gems57.grid import load_grid  # noqa: E402

TARGET_TOTAL_DOTS = 38_000


def _eval_crop(
    p_crop: np.ndarray,
    cell: holdout.Cell,
    vis_crop: np.ndarray,
    hid_crop: np.ndarray,
    valid_crop: np.ndarray,
    global_shape: tuple[int, int],
) -> tuple[np.ndarray, dict]:
    sy, sx = cell.bbox
    fold_dict = {
        "region": cell.active | vis_crop,
        "visible": vis_crop,
        "masked_known": vis_crop,
        "truth": hid_crop,
    }
    res, terms = evaluate_holdout.evaluate(
        p_crop.astype(np.float32, copy=False),
        fold_dict,
        valid_crop,
        block_side=200,
        origin=(sy.start, sx.start),
        global_shape=global_shape,
    )
    sc_check = holdout.score_cell(cell, p_crop > 0.5)
    np.testing.assert_allclose(res["dti"], sc_check["dti"], rtol=1e-6, atol=1e-6)
    return terms, {
        "dti": round(float(res["dti"]), 6),
        "tpw": round(float(res["tpw"]), 3),
        "fpw": round(float(res["fpw"]), 3),
        "fnw": round(float(res["fnw"]), 3),
        "n_truth": int(res["n_truth"]),
        "n_emitted": int(res["n_emitted"]),
    }


def main() -> int:
    t0 = time.time()
    cache_dir = ROOT / ".cache" / "gems_data"
    manifest_path = ROOT / "registry" / "data_manifest.json"
    evidence_dir = ROOT / "evidence"
    downloads_dir = ROOT / "docs" / "downloads"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    print("[1/7] Loading verified grid...", flush=True)
    grid = load_grid(cache_dir)
    fp = grid.footprint
    cat = grid.catalogue
    H, W = fp.shape
    print(f"      Grid {grid.shape}, footprint={int(fp.sum())}, catalogue={int(cat.sum())}", flush=True)

    print("[2/7] Loading / extracting 36 localized static multi-physics features...", flush=True)
    t_feat = time.time()
    feat_cache = cache_dir / "h90_static_features_fp_v1.npy"
    if not feat_cache.is_file():
        X_built = extract_static_features_fp(cache_dir, fp)
        np.save(feat_cache, X_built)
        del X_built
        gc.collect()
    X_fp = np.load(feat_cache, mmap_mode="r")
    print(f"      Mapped X_fp shape={X_fp.shape} in {time.time() - t_feat:.1f}s", flush=True)

    print("[3/7] Running Protocol Rule #4 single-feature holdout leakage canary...", flush=True)
    canary_path = evidence_dir / "h90_leakage_canary.json"
    ctx_canary = holdout.build_holdout(grid, seeds=(20,), modes=("all",))
    canary_report = run_leakage_canary(X_fp, ctx_canary, auc_limit=0.90)
    del ctx_canary
    gc.collect()
    canary_path.write_text(json.dumps(canary_report, indent=2) + "\n", encoding="utf-8")
    print(
        f"      Canary PASS: {canary_report['features_tested']} features tested, "
        f"max symmetric AUC = {canary_report['max_symmetric_auc']:.4f} "
        f"({canary_report['max_symmetric_auc_feature']}) <= 0.90",
        flush=True,
    )

    print("[4/7] Fitting & predicting frozen 3-experiment ablation ladder (Exp 1, Exp 2, Exp 3)...", flush=True)
    t_mod = time.time()
    surf_c1 = build_classical_ridge_surface(X_fp, fp)
    surf_exp1 = build_exp1_unsupervised_surface(X_fp, fp)
    sup_out = fit_predict_exp2_and_exp3(X_fp, fp, cat, cache_dir=cache_dir, seed=90701)
    print(f"      Models fitted and predicted in {time.time() - t_mod:.1f}s", flush=True)

    ctx = holdout.build_holdout(grid, seeds=(20, 21), modes=("all", "detached"))
    for cell in ctx.cells:
        hid = ctx.hidden_by_cell[cell.key]
        for r in range(4):
            if r != cell.fold and (hid & sup_out["eroded_quad_2d"][r]).any():
                raise AssertionError(f"Leakage violation: {cell.key} overlaps training quadrant {r}")

    with rasterio.open(
        cache_dir / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    ) as ds_d28:
        d28_bool = np.isfinite(ds_d28.read(1)) & (ds_d28.read(1) > 0.5) & fp

    quad_dots = {}
    rem = TARGET_TOTAL_DOTS
    for q in range(4):
        if q < 3:
            qd = int(round(TARGET_TOTAL_DOTS * float(((ctx.quad == q) & fp).sum()) / float(fp.sum())))
            quad_dots[q] = qd
            rem -= qd
        else:
            quad_dots[q] = rem

    arms = (
        "c0_random_isolated",
        "c1_classical_ridge",
        "exp1_unsupervised_mpst",
        "exp2_nested_loqo_blind_worm",
        "exp3_dual_coulomb_mpst",
        "ref_fair_r0_vis_b2",
    )
    terms_all: dict[str, np.ndarray] = {}
    terms_det: dict[str, np.ndarray] = {}
    terms_d20: dict[str, np.ndarray] = {}
    per_cell_all: dict[str, dict] = {a: {} for a in arms}
    per_cell_det: dict[str, dict] = {a: {} for a in arms}

    print("[5/7] Streaming fold-fair dot emission & scoring pooled HOLDOUT-DTI (16 cells)...", flush=True)
    t_emit = time.time()
    s2_oof_2d = sup_out["exp2_oof_surface_2d"]

    for idx_c, cell in enumerate(ctx.cells):
        q = cell.fold
        sy, sx = cell.bbox
        q_crop = (ctx.quad[sy, sx] == q) & fp[sy, sx]
        vis_crop = ctx.visible(cell.key)[sy, sx]
        hid_crop = ctx.hidden_by_cell[cell.key][sy, sx]
        valid_crop = fp[sy, sx]

        s3_crop, d_vis_crop = predict_exp3_cell_surface_crop(cell, ctx, sup_out)
        elig_crop = q_crop & (d_vis_crop > 2.0)
        q_budget = quad_dots[q]

        arm_crops = {
            "c0_random_isolated": random_isolated_emit(elig_crop, target_dots=q_budget, seed=9000 + 31 * cell.seed + q),
            "c1_classical_ridge": greedy_spacing_emit(surf_c1[sy, sx], elig_crop, target_dots=q_budget, min_spacing_px=2.8),
            "exp1_unsupervised_mpst": celf_submodular_emit(surf_exp1[sy, sx], elig_crop, target_dots=q_budget),
            "exp2_nested_loqo_blind_worm": celf_submodular_emit(s2_oof_2d[sy, sx], elig_crop, target_dots=q_budget),
            "exp3_dual_coulomb_mpst": celf_submodular_emit(s3_crop, elig_crop, target_dots=q_budget),
            "ref_fair_r0_vis_b2": np.where(d28_bool[sy, sx] & elig_crop, 1.0, 0.0).astype(np.float32),
        }

        for arm, p_crop in arm_crops.items():
            t_arr, c_stats = _eval_crop(p_crop, cell, vis_crop, hid_crop, valid_crop, (H, W))
            if cell.mode == "all":
                terms_all[arm] = t_arr if arm not in terms_all else (terms_all[arm] + t_arr)
                per_cell_all[arm][cell.key] = c_stats
                if cell.seed == 20:
                    terms_d20[arm] = t_arr.copy() if arm not in terms_d20 else (terms_d20[arm] + t_arr)
            else:
                terms_det[arm] = t_arr if arm not in terms_det else (terms_det[arm] + t_arr)
                per_cell_det[arm][cell.key] = c_stats
        del arm_crops, s3_crop, d_vis_crop
        print(f"        Scored cell {idx_c + 1:2d}/16 ({cell.key})", flush=True)

    exp_keys = ("exp1_unsupervised_mpst", "exp2_nested_loqo_blind_worm", "exp3_dual_coulomb_mpst")
    raw_dtis = {k: float(evaluate_holdout.from_terms(terms_all[k].sum(axis=0))) for k in exp_keys}
    best_exp_key = max(exp_keys, key=lambda k: raw_dtis[k])

    summary_all = evaluate_holdout.pooled_summary(terms_all, draws=1000, seed=90801, candidate=best_exp_key)
    summary_det = evaluate_holdout.pooled_summary(terms_det, draws=1000, seed=90802, candidate=best_exp_key)
    summary_d20 = evaluate_holdout.pooled_summary(terms_d20, draws=1000, seed=90803, candidate=best_exp_key)

    print(f"      Emission & holdout evaluation completed in {time.time() - t_emit:.1f}s", flush=True)
    print("      --- Pooled HOLDOUT-DTI (gems57-pooled-hide-v2, seeds 20+21) ---", flush=True)
    for arm in arms:
        sa = summary_all["scores"][arm]
        sd = summary_det["scores"][arm]
        print(
            f"        {arm:28s} | mode=all: {sa['dti']:.5f} [{sa['ci95'][0]:.5f}, {sa['ci95'][1]:.5f}] (n={sa['withheld_positive_pixels']}) "
            f"| mode=detached: {sd['dti']:.5f} [{sd['ci95'][0]:.5f}, {sd['ci95'][1]:.5f}] (n={sd['withheld_positive_pixels']})",
            flush=True,
        )
    print(f"      Selected best experiment from {len(exp_keys)}-experiment budget: {best_exp_key}", flush=True)

    d_cat_full = sup_out["d_cat_full_2d"]
    elig_prod = fp & (d_cat_full > 2.0)
    if best_exp_key == "exp1_unsupervised_mpst":
        prod_surface = np.where(elig_prod, surf_exp1, 0.0).astype(np.float32)
    elif best_exp_key == "exp2_nested_loqo_blind_worm":
        prod_surface = np.where(elig_prod, sup_out["exp2_prod_surface_2d"], 0.0).astype(np.float32)
    else:
        prod_surface = np.where(elig_prod, sup_out["exp3_prod_surface_2d"], 0.0).astype(np.float32)

    prod_dots = celf_submodular_emit(prod_surface, elig_prod, target_dots=TARGET_TOTAL_DOTS)

    sgmc_diag = None
    sgmc_path = cache_dir / "external" / "derived_sgmc_faults_100m_u8.tif"
    if sgmc_path.is_file():
        with rasterio.open(sgmc_path) as sg:
            sgmc_truth = (sg.read(1) > 0) & fp & (d_cat_full >= 5.0)
        d_sg = metric.dti_binary(prod_dots > 0.5, sgmc_truth, valid=fp, known=cat)
        with rasterio.open(cache_dir / "parent" / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as r0s:
            r0_dots = (r0s.read(1) > 0.5) & fp
        d_sg_r0 = metric.dti_binary(r0_dots, sgmc_truth, valid=fp, known=cat)
        sgmc_diag = {
            "evidence_class": "DIAGNOSTIC-OFFCATALOGUE-SGMC-PROXY (NOT A COMPETITION SCORE)",
            "sgmc_offcatalogue_pixels_d_ge_5px": int(sgmc_truth.sum()),
            "candidate_dti": round(float(d_sg["dti"]), 6),
            "r0_h33_b2_dti": round(float(d_sg_r0["dti"]), 6),
            "caveat": (
                "USGS SGMC is a 1:500k state bedrock compilation, not the expert-interpreted "
                "GeoDAWN competition test set (IR90-42)."
            ),
        }

    holdout_payload = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": evaluate_holdout.VERSION,
        "experiments_run_count": 3,
        "experiment_budget_max": 3,
        "selected_candidate": best_exp_key,
        "comparator_provenance_note": (
            "c0_random_isolated, c1_classical_ridge, exp1_unsupervised_mpst, exp2_nested_loqo_blind_worm, "
            "and exp3_dual_coulomb_mpst are 100% leak-free out-of-quadrant evaluations. "
            "ref_fair_r0_vis_b2 (D2.8 dotted H19-5 masked by fold-visible d_vis > 2 px, matching GEMSDOE76's "
            "fair-H33 control) is included as the strongest incumbent reference benchmark; note that its parent "
            "H19-5 surface was originally trained on full quadrants in 19GEMSDOE where adjacent segments inside "
            "each quadrant were visible."
        ),
        "pooled_all_2seed": summary_all,
        "pooled_detached_2seed": summary_det,
        "pooled_all_draw20_single_partition": summary_d20,
        "per_cell_all": per_cell_all,
        "per_cell_detached": per_cell_det,
        "diagnostic_sgmc_offcatalogue": sgmc_diag,
    }
    (evidence_dir / "h90_holdout_evaluation.json").write_text(
        json.dumps(holdout_payload, indent=2) + "\n", encoding="utf-8"
    )

    print("[6/7] Running Protocol Rule #1 registry uniqueness gate & packaging GeoTIFF + ZIP...", flush=True)
    registry_records = build_registry_index(manifest_path, cache_dir)
    pre_uniq = audit_surface_and_dots_uniqueness(
        prod_surface,
        prod_dots,
        fp,
        cache_dir / "sample_submission.tif",
        registry_records,
        ROOT / "ledger" / "submissions.csv",
    )
    if not pre_uniq["passed"]:
        raise RuntimeError(f"Parallel-Run Uniqueness Gate failed: {json.dumps(pre_uniq, indent=2)}")

    decoded_short = hashlib.sha256(np.ascontiguousarray(prod_dots).tobytes()).hexdigest()[:8]
    stem = f"gemsdoe90-h90-cc-mpst-submod38k-20261024-{decoded_short}-zeros"
    tif_out = downloads_dir / f"{stem}.tif"
    zip_out = downloads_dir / f"{stem}.zip"
    json_out = downloads_dir / f"{stem}.json"
    for p_old in (tif_out, zip_out, json_out):
        p_old.unlink(missing_ok=True)

    cand_all_dti = summary_all["scores"][best_exp_key]["dti"]
    cand_det_dti = summary_det["scores"][best_exp_key]["dti"]
    sub_name = f"GEMSDOE90-H90-CC-MPST-{decoded_short.upper()}"
    sub_note = (
        f"GEMSDOE90 H90 CC-MPST+Coulomb+Submod300 | {int((prod_dots > 0).sum())} dots B>2 "
        f"| HOLDOUT-DTI all={cand_all_dti:.4f} det={cand_det_dti:.4f}"
    )
    assert len(sub_note) <= 140, f"Note exceeds 140 chars ({len(sub_note)}): {sub_note}"

    writer_receipt = submission_writer.write_submission(
        tif_out,
        prod_dots,
        cache_dir / "sample_submission.tif",
        fp,
        note=sub_note,
        name=sub_name,
        catalogue=cat,
        metadata={
            "experiment": best_exp_key,
            "evaluator_version": evaluate_holdout.VERSION,
            "holdout_dti_all": round(cand_all_dti, 6),
            "holdout_dti_detached": round(cand_det_dti, 6),
        },
    )
    for p_written in (tif_out, zip_out, json_out):
        if p_written.exists():
            p_written.chmod(0o644)

    final_uniq = audit_surface_and_dots_uniqueness(
        prod_surface,
        prod_dots,
        fp,
        cache_dir / "sample_submission.tif",
        registry_records,
        ROOT / "ledger" / "submissions.csv",
        candidate_tif_sha256=writer_receipt["sha256"],
        exclude_ledger_ids={stem},
    )
    (evidence_dir / "h90_uniqueness_audit.json").write_text(
        json.dumps(final_uniq, indent=2) + "\n", encoding="utf-8"
    )

    print("[7/7] Running self-contained automated validation gate & writing Run Card JSON...", flush=True)
    gate_report = run_automated_submission_gate(
        tif_path=tif_out,
        zip_path=zip_out,
        sample_path=cache_dir / "sample_submission.tif",
        catalogue_path=cache_dir / "existing_faults.tif",
        footprint=fp,
        catalogue=cat,
        submission_name=sub_name,
        submission_note=sub_note,
        canary_report=canary_report,
        uniqueness_report=final_uniq,
        holdout_summary_all=summary_all,
        holdout_summary_detached=summary_det,
        candidate_arm_key=best_exp_key,
        strict_raise=True,
    )
    (evidence_dir / "h90_automated_gate.json").write_text(
        json.dumps(gate_report, indent=2) + "\n", encoding="utf-8"
    )

    run_card = {
        "protocol": "PARALLEL-RUN-PROTOCOL-v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lane_repo": "buffedlizard55-lab/GEMSDOE90",
        "branch": "arena/783b0fc5-gemsdoe90",
        "experiments_used": 3,
        "experiment_budget_limit": 3,
        "elapsed_seconds": round(time.time() - t0, 2),
        "hypothesis": (
            "H90-1 (CC-MPST-Submod300): Concealment-conditioned multi-physics odd-step polarity, "
            "upward-continued shallow hydrothermal demagnetization + potassic/MT alteration trough, "
            "nested pairwise-LOQO 2D steerable worm persistence, and strictly fold-visible Coulomb "
            "forward fault-tip wing-crack & en-echelon relay transfer with exact 25-offset R=300 m "
            "CELF submodular dot allocation on d(catalogue) > 2.0 px."
        ),
        "mechanism": (
            "Separates dipping fault contacts (anti-symmetric cross-strike step in RTP magnetics, "
            "isostatic gravity, and detrended elevation/1m LiDAR) from symmetric dikes/channels, pairs "
            "TMI_up150-vs-RTP vertical attenuation with K/ThK alteration and MT conductivity to detect "
            "hydrothermally demagnetized geothermal conduits beneath basin fill, sharpens traces via "
            "800 m & 1.8 km steerable worms + Coulomb tip/relay cones, and eliminates 300 m kernel "
            "FP redundancy via exact CELF lazy-greedy submodular optimization."
        ),
        "named_non_fault_mimic": (
            "Pleistocene Lake Lahontan paleoshoreline beach ridges (in 1 m LiDAR / radiometrics) and "
            "remanently reverse-magnetized Tertiary ash-flow tuff cooling margins / paleochannels "
            "(producing shallow magnetic lows and odd magnetic steps without brittle slip)."
        ),
        "leakage_canary": {
            "features_tested": canary_report["features_tested"],
            "max_symmetric_auc": canary_report["max_symmetric_auc"],
            "max_symmetric_auc_feature": canary_report["max_symmetric_auc_feature"],
            "auc_limit": canary_report["auc_limit"],
            "passed": canary_report["all_passed"],
        },
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": evaluate_holdout.VERSION,
            "primary_all_segments_2seed": summary_all["scores"][best_exp_key],
            "conservative_detached_segments_2seed": summary_det["scores"][best_exp_key],
            "primary_draw20_single_partition": summary_d20["scores"][best_exp_key],
            "all_arms_primary_all": summary_all["scores"],
            "all_arms_detached": summary_det["scores"],
            "paired_differences_vs_candidate_all": summary_all["paired_differences"],
            "paired_differences_vs_candidate_detached": summary_det["paired_differences"],
        },
        "registry_correlation_and_overlap": {
            "rasters_checked": final_uniq["rasters_checked"],
            "ledger_hashes_checked": final_uniq["ledger_hashes_checked"],
            "pre_placement_surface_max_abs_spearman": final_uniq["pre_placement_surface"]["max_abs_spearman_rho"],
            "pre_placement_surface_nearest": final_uniq["pre_placement_surface"]["nearest_submission"],
            "final_dots_max_abs_spearman": final_uniq["final_dots"]["max_abs_spearman_rho"],
            "final_dots_max_mutual_3px_overlap": final_uniq["final_dots"]["max_mutual_3px_overlap"],
            "final_dots_max_non_lattice_forward_3px_overlap": final_uniq["final_dots"][
                "max_non_lattice_forward_3px_overlap"
            ],
            "final_dots_nearest_non_lattice": final_uniq["final_dots"][
                "nearest_non_lattice_forward_submission"
            ],
            "vs_incumbent_r0_h33_b2": final_uniq["final_dots"]["vs_incumbent_r0_h33_b2"],
            "passed": final_uniq["passed"],
        },
        "raster_sha256": writer_receipt["sha256"],
        "zip_sha256": writer_receipt["zip_sha256"],
        "validator_output": {
            "all_technical_checks_passed": gate_report["technical_portal_ready"],
            "no_nan_inside_footprint": gate_report["technical_checks"]["all_12279160_cells_finite"],
            "no_nan_anywhere_in_12279160_cells": gate_report["technical_checks"]["all_12279160_cells_finite"],
            "values_in_0_1": gate_report["technical_checks"]["values_strictly_in_0_1"],
            "crs_shape_transform_match": (
                gate_report["technical_checks"]["crs_epsg_32611"]
                and gate_report["technical_checks"]["shape_3730x3292"]
                and gate_report["technical_checks"]["transform_exact_match"]
            ),
            "zero_on_catalogue": gate_report["technical_checks"]["zero_positive_on_catalogue"],
            "zero_outside_footprint": gate_report["technical_checks"]["zero_positive_outside_footprint"],
            "nodata_tag": gate_report["file"]["nodata"],
            "min": gate_report["file"]["min"],
            "max": gate_report["file"]["max"],
            "emitted_dots": gate_report["file"]["emitted_dots"],
            "tif_file": f"docs/downloads/{tif_out.name}",
            "zip_file": f"docs/downloads/{zip_out.name}",
            "tif_bytes": gate_report["file"]["tif_bytes"],
            "zip_bytes": gate_report["file"]["zip_bytes"],
        },
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_chars": len(sub_note),
        "verdict": gate_report["verdict"],
        "automated_ui_badge": gate_report["ui_badge"],
        "automated_ui_guidance": gate_report["ui_guidance"],
    }

    run_card_path = evidence_dir / "h90_run_card.json"
    run_card_path.write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(run_card_path, downloads_dir / "h90_run_card.json")

    print("=" * 78, flush=True)
    print(f"FINAL VERDICT: {run_card['verdict'].upper()} | {gate_report['ui_badge']}", flush=True)
    print(f"GeoTIFF:       docs/downloads/{tif_out.name} ({gate_report['file']['tif_bytes']} B)", flush=True)
    print(f"SHA-256:       {run_card['raster_sha256']}", flush=True)
    print(f"Submit Name:   {sub_name}", flush=True)
    print(f"Submit Note:   {sub_note} ({len(sub_note)}/140 chars)", flush=True)
    print(f"Elapsed:       {run_card['elapsed_seconds']}s", flush=True)
    print("=" * 78, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
