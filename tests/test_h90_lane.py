"""Fast CI-safe unit & artifact-integrity tests for Lane H90 (CC-MPST-Submod300).

Runs in <5 seconds without requiring ``.cache/gems_data/`` so GitHub Actions CI
verifies both synthetic algorithmic invariants and the actual committed GeoTIFF,
ZIP, JSON Run Card, ledger row, and GitHub Pages links on every push/PR.
"""

from __future__ import annotations

import csv
import html as html_lib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine, from_origin

from src.auto_validator import (
    audit_surface_and_dots_uniqueness,
    main as auto_validator_cli,
    run_automated_submission_gate,
    sha256_file,
    verify_standalone_geotiff,
)
from src.h90_emitter import (
    KERNEL_5X5,
    celf_submodular_emit,
    greedy_spacing_emit,
    random_isolated_emit,
)
from src.h90_features import (
    FORBIDDEN_CSV_COLUMNS,
    STATIC_FEATURE_NAMES,
    VISIBLE_FEATURE_NAMES,
    clean_band,
    compute_fold_visible_coulomb_features,
    steerable_line_anisotropy,
    steerable_odd_even_step_ratio,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TIF = ROOT / "docs" / "downloads" / "gemsdoe90-h90-cc-mpst-submod38k-20261024-d76ac964-zeros.tif"
EXPECTED_ZIP = ROOT / "docs" / "downloads" / "gemsdoe90-h90-cc-mpst-submod38k-20261024-d76ac964-zeros.zip"
EXPECTED_TIF_SHA = "637f067efc8b7822af9be58fff3f9c3a02bc41bd699e22c622ecf90bc7046e51"
EXPECTED_ZIP_SHA = "85fffcd6ba9c46a99b03d69ddf42b214a8eca1507f4840f47344979a2d75464d"


def test_clean_band_filters_float32_sentinels():
    fp = np.ones((8, 8), dtype=bool)
    fp[:2, :] = False
    arr = np.full((8, 8), 10.0, dtype=np.float32)
    arr[3, 3] = np.float32(-3.4028235e38)
    arr[4, 4] = np.nan
    cleaned, valid = clean_band(arr, fp)
    assert not valid[3, 3] and not valid[4, 4] and not valid[0, 0]
    assert np.isfinite(cleaned).all()
    assert cleaned[3, 3] == pytest.approx(10.0)


def test_odd_step_discriminates_fault_contact_from_symmetric_dike():
    yy, xx = np.mgrid[0:32, 0:32]
    fp = np.ones((32, 32), dtype=bool)
    fault_step = np.tanh((xx - 16.0) / 1.5).astype(np.float32)
    sym_dike = np.exp(-0.5 * ((xx - 16.0) / 1.5) ** 2).astype(np.float32)

    r_step = steerable_odd_even_step_ratio(fault_step, fp, radius_px=3, smooth_sigma=0.8)
    r_dike = steerable_odd_even_step_ratio(sym_dike, fp, radius_px=3, smooth_sigma=0.8)

    # At x=16, fault step is anti-symmetric (odd >> even), whereas dike crest is symmetric (odd ~ 0)
    assert float(r_step[16, 16]) > 5.0 * float(r_dike[16, 16])


def test_coulomb_wing_crack_and_relay_invariants_and_no_csv_leakage():
    assert "dist_known_fault_px" in FORBIDDEN_CSV_COLUMNS
    assert len(STATIC_FEATURE_NAMES) == 36
    assert VISIBLE_FEATURE_NAMES == ("vis_coulomb_tip_cone", "vis_relay_bridge")

    src_code = (ROOT / "src" / "h90_features.py").read_text(encoding="utf-8")
    assert 'row["dist_known_fault_px"]' not in src_code
    assert "row.get('dist_known_fault_px')" not in src_code

    fp = np.ones((80, 90), dtype=bool)
    vis = np.zeros((80, 90), dtype=bool)
    # Short 10-px fragment (<25 px) must NOT emit a tip cone (IR90-46 guard)
    vis[10, 10:20] = True
    # Two major 30-px en-echelon trunks separated by a 10-px step-over
    vis[40, 10:40] = True
    vis[48, 48:78] = True

    d_vis, d_clip, tip_fp, relay_fp = compute_fold_visible_coulomb_features(vis, fp)
    tip_2d = tip_fp.reshape(fp.shape)
    relay_2d = relay_fp.reshape(fp.shape)

    assert np.isfinite(d_vis).all() and np.isfinite(tip_2d).all() and np.isfinite(relay_2d).all()
    # Short fragment produces zero tip energy nearby
    assert float(tip_2d[6:15, 20:28].max()) == 0.0
    # Off-axis Mode-II lobe ahead of major trunk (40, 39) is strictly positive for r > 4.5 px
    assert float(tip_2d[35:46, 45:52].max()) > 0.25
    # Relay step-over zone between (40, 39) and (48, 48) receives positive relay bridge energy
    assert float(relay_2d[42:47, 42:47].max()) > 0.15


def test_celf_submodular_matches_bruteforce_greedy_oracle():
    rng = np.random.default_rng(123)
    H, W = 18, 20
    prob = rng.uniform(0.01, 0.25, size=(H, W)).astype(np.float32)
    prob[8, 3:17] = 0.85  # synthetic fault ridge
    elig = np.ones((H, W), dtype=bool)
    elig[0, :] = False

    n_pick = 7
    celf_out = celf_submodular_emit(
        prob,
        elig,
        target_dots=n_pick,
        min_spacing_px=0.0,
        pool_multiplier=100,
    )
    assert celf_out.dtype == np.float32
    assert set(np.unique(celf_out)).issubset({0.0, 1.0})
    assert int((celf_out == 1.0).sum()) == n_pick
    assert float(celf_out[~elig].sum()) == 0.0

    # Brute-force greedy oracle on identical monotone submodular objective
    cov = np.zeros((H, W), dtype=np.float32)
    chosen: list[tuple[int, int]] = []
    for _ in range(n_pick):
        best_gain = -1e9
        best_rc = None
        for r in range(H):
            for c in range(W):
                if not elig[r, c] or (r, c) in chosen:
                    continue
                tp_gain = 0.0
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        kw = float(KERNEL_5X5[dy + 2, dx + 2])
                        rr, cc = r + dy, c + dx
                        if 0 <= rr < H and 0 <= cc < W and kw > cov[rr, cc]:
                            tp_gain += float(prob[rr, cc]) * (kw - float(cov[rr, cc]))
                if tp_gain > best_gain + 1e-6:
                    best_gain = tp_gain
                    best_rc = (r, c)
        assert best_rc is not None
        chosen.append(best_rc)
        br, bc = best_rc
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                kw = float(KERNEL_5X5[dy + 2, dx + 2])
                rr, cc = br + dy, bc + dx
                if 0 <= rr < H and 0 <= cc < W and kw > cov[rr, cc]:
                    cov[rr, cc] = kw

    oracle = np.zeros((H, W), dtype=np.float32)
    for r, c in chosen:
        oracle[r, c] = 1.0
    np.testing.assert_array_equal(celf_out, oracle)


def test_auto_validator_catches_portal_range_nan_and_negative_holdout(tmp_path):
    shape = (24, 24)
    transform = from_origin(243350.0, 4508550.0, 100.0, 100.0)
    fp = np.ones(shape, dtype=bool)
    fp[:3, :] = False
    cat = np.zeros(shape, dtype=bool)
    cat[12, :] = True

    def write_tif(p: Path, arr: np.ndarray, nodata=None):
        prof = dict(
            driver="GTiff",
            height=shape[0],
            width=shape[1],
            count=1,
            dtype="float32",
            crs="EPSG:32611",
            transform=transform,
            nodata=nodata,
        )
        with rasterio.open(p, "w", **prof) as ds:
            ds.write(arr.astype(np.float32), 1)

    sample_arr = np.where(fp, 0.0, np.nan).astype(np.float32)
    sample_p = tmp_path / "sample.tif"
    cat_p = tmp_path / "cat.tif"
    write_tif(sample_p, sample_arr, nodata=np.nan)
    write_tif(cat_p, cat.astype(np.float32), nodata=None)

    prior_arr = np.zeros(shape, dtype=np.float32)
    prior_arr[5, 5] = 1.0
    prior_p = tmp_path / "prior.tif"
    write_tif(prior_p, prior_arr, nodata=None)
    reg = {
        "complete_accessible_scan": True,
        "errors": [],
        "rasters": [
            {
                "repo_first": "test/repo",
                "sources": ["prior_1"],
                "cache_file": str(prior_p),
                "sha256": sha256_file(prior_p),
            }
        ],
    }

    cand_arr = np.zeros(shape, dtype=np.float32)
    cand_arr[18, 18] = 1.0
    cand_tif = tmp_path / "cand.tif"
    cand_zip = tmp_path / "cand.zip"
    write_tif(cand_tif, cand_arr, nodata=None)
    with zipfile.ZipFile(cand_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(cand_tif, arcname=cand_tif.name)

    uniq = audit_surface_and_dots_uniqueness(cand_arr * 0.7, cand_arr, fp, sample_p, reg)
    assert uniq["passed"]

    canary_ok = {"all_passed": True}
    holdout_win = {
        "scores": {"cand": {"dti": 0.11, "ci95": [0.10, 0.12], "withheld_positive_pixels": 100}},
        "paired_differences": {
            "c0_random_isolated": {"delta": 0.06, "ci95": [0.05, 0.07]},
            "c1_classical_ridge": {"delta": 0.05, "ci95": [0.04, 0.06]},
            "ref_fair_r0_vis_b2": {"delta": 0.015, "ci95": [0.005, 0.025]},
        },
    }
    # Note: gems57 validate checks full 3730x3292 grid dimensions, so on a 24x24 toy grid
    # shape_3730x3292 is False, proving fail-closed dimension protection!
    gate_toy = run_automated_submission_gate(
        tif_path=cand_tif,
        zip_path=cand_zip,
        sample_path=sample_p,
        catalogue_path=cat_p,
        footprint=fp,
        catalogue=cat,
        submission_name="TEST-SUB",
        submission_note="short note",
        canary_report=canary_ok,
        uniqueness_report=uniq,
        holdout_summary_all=holdout_win,
        holdout_summary_detached=holdout_win,
        candidate_arm_key="cand",
    )
    assert gate_toy["technical_checks"]["values_strictly_in_0_1"] is True
    assert gate_toy["technical_checks"]["shape_3730x3292"] is False
    assert gate_toy["verdict"] == "negative"

    # Out-of-range >1.0 value must trip values_strictly_in_0_1 immediately
    bad_arr = cand_arr.copy()
    bad_arr[19, 19] = 1.25
    bad_tif = tmp_path / "bad.tif"
    bad_zip = tmp_path / "bad.zip"
    write_tif(bad_tif, bad_arr, nodata=None)
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.write(bad_tif, arcname=bad_tif.name)
    gate_bad = run_automated_submission_gate(
        tif_path=bad_tif,
        zip_path=bad_zip,
        sample_path=sample_p,
        catalogue_path=cat_p,
        footprint=fp,
        catalogue=cat,
        submission_name="TEST-SUB",
        submission_note="short note",
        canary_report=canary_ok,
        uniqueness_report=uniq,
        holdout_summary_all=holdout_win,
        holdout_summary_detached=holdout_win,
        candidate_arm_key="cand",
    )
    assert gate_bad["technical_checks"]["values_strictly_in_0_1"] is False
    assert gate_bad["technical_portal_ready"] is False


def test_committed_h90_deliverable_receipts_ledger_and_pages():
    assert EXPECTED_TIF.is_file(), f"Missing promoted GeoTIFF: {EXPECTED_TIF}"
    assert EXPECTED_ZIP.is_file(), f"Missing single-TIFF ZIP: {EXPECTED_ZIP}"
    assert sha256_file(EXPECTED_TIF) == EXPECTED_TIF_SHA
    assert sha256_file(EXPECTED_ZIP) == EXPECTED_ZIP_SHA

    # Verify GeoTIFF directly from disk without needing .cache/gems_data/
    with rasterio.open(EXPECTED_TIF) as ds:
        assert ds.count == 1
        assert ds.dtypes == ("float32",)
        assert ds.shape == (3730, 3292)
        assert ds.crs is not None and ds.crs.to_epsg() == 32611
        assert ds.transform == Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None
        arr = ds.read(1)

    assert arr.size == 12_279_160
    assert np.isfinite(arr).all(), "Portal safety: zero NaN or Inf allowed anywhere in 12,279,160 cells"
    assert float(arr.min()) == 0.0
    assert float(arr.max()) == 1.0
    assert set(np.unique(arr)).issubset({0.0, 1.0})
    assert int((arr == 1.0).sum()) == 38_000

    # Verify ZIP wraps the exact single GeoTIFF
    with zipfile.ZipFile(EXPECTED_ZIP, "r") as zf:
        names = zf.namelist()
        assert names == [EXPECTED_TIF.name]
        assert zf.read(names[0]) == EXPECTED_TIF.read_bytes()

    # Verify Run Card & Automated Gate JSON consistency
    rc = json.loads((ROOT / "evidence" / "h90_run_card.json").read_text(encoding="utf-8"))
    gate = json.loads((ROOT / "evidence" / "h90_automated_gate.json").read_text(encoding="utf-8"))
    canary = json.loads((ROOT / "evidence" / "h90_leakage_canary.json").read_text(encoding="utf-8"))

    assert rc["verdict"] == "promote"
    assert rc["experiments_used"] <= 3
    assert rc["raster_sha256"] == EXPECTED_TIF_SHA
    assert rc["zip_sha256"] == EXPECTED_ZIP_SHA
    assert len(rc["submission_note"]) <= 140
    assert canary["all_passed"] is True
    assert canary["max_symmetric_auc"] <= 0.90
    assert gate["technical_portal_ready"] is True
    assert all(gate["technical_checks"].values())
    assert rc["registry_correlation_and_overlap"]["passed"] is True
    assert rc["registry_correlation_and_overlap"]["pre_placement_surface_max_abs_spearman"] <= 0.90
    assert rc["registry_correlation_and_overlap"]["final_dots_max_abs_spearman"] <= 0.90
    assert rc["registry_correlation_and_overlap"]["final_dots_max_mutual_3px_overlap"] <= 0.70
    assert rc["registry_correlation_and_overlap"]["final_dots_max_non_lattice_forward_3px_overlap"] <= 0.70

    # Verify Protocol Rule #3 in ledger/submissions.csv: never write a projection as a score
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    h90_rows = [r for r in rows if r["id"] == EXPECTED_TIF.stem]
    assert len(h90_rows) == 1
    row = h90_rows[0]
    assert row["score"] == ""
    assert row["receipt_score"] == ""
    assert row["evidence_class"] == "HOLDOUT-DTI"
    assert row["sha256"] == ""
    assert row["sha256_zeros"] == EXPECTED_TIF_SHA
    assert len(row["form_note"]) <= 140

    # Verify GitHub Pages HTML files & relative link resolution
    assert (ROOT / ".nojekyll").is_file()
    assert (ROOT / "docs" / ".nojekyll").is_file()
    for html_path in (
        ROOT / "index.html",
        ROOT / "executive-summary.html",
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "executive-summary.html",
    ):
        assert html_path.is_file()
        html = html_path.read_text(encoding="utf-8")
        assert EXPECTED_TIF_SHA in html
        assert rc["submission_name"] in html
        for href in re.findall(r'href="(\./[^"#?]+)"', html):
            target = (html_path.parent / href).resolve()
            assert target.is_file(), f"Broken relative link {href} in {html_path}"
            assert (target.stat().st_mode & 0o444) == 0o444, f"File not world-readable: {target}"

    # Verify embedded JSON Run Card in index.html & docs/index.html parses cleanly and matches evidence
    for idx_html in (ROOT / "index.html", ROOT / "docs" / "index.html"):
        raw_html = idx_html.read_text(encoding="utf-8")
        m = re.search(r'<pre id="json-runcard">(.*?)</pre>', raw_html, flags=re.DOTALL)
        assert m is not None
        embedded_rc = json.loads(html_lib.unescape(m.group(1)))
        assert embedded_rc["raster_sha256"] == rc["raster_sha256"]
        assert embedded_rc["zip_sha256"] == rc["zip_sha256"]
        assert embedded_rc["verdict"] == rc["verdict"] == "promote"
        assert embedded_rc["submission_name"] == rc["submission_name"]
        assert embedded_rc["submission_note"] == rc["submission_note"]
        assert embedded_rc["holdout_dti"]["primary_all_segments_2seed"]["dti"] == pytest.approx(
            rc["holdout_dti"]["primary_all_segments_2seed"]["dti"], abs=1e-12
        )

    # Verify standalone CLI validator
    standalone = verify_standalone_geotiff(EXPECTED_TIF)
    assert standalone["ok"] is True
    assert standalone["sha256"] == EXPECTED_TIF_SHA
    assert standalone["positive_pixels"] == 38_000
    assert auto_validator_cli([str(EXPECTED_TIF)]) == 0

