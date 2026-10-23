"""Synthetic unit tests and receipt/ledger integrity checks for AXIS=RELIEF."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_relief_variants as relief_build  # noqa: E402
from src.dti import components_from_arrays, dti_from_components, marginal_gain  # noqa: E402
from src.relief import (  # noqa: E402
    block_density_cv,
    clean_band_median_fill,
    greedy_relief_reallocate,
    landform_relief_index,
    relief_terciles,
)


def test_clean_band_median_fill_replaces_sentinels_inside_footprint() -> None:
    foot = np.ones((6, 6), dtype=bool)
    foot[0, :] = False
    band = np.arange(36, dtype=np.float32).reshape(6, 6)
    band[2, 2] = -3.4028235e38
    band[3, 3] = np.nan
    filled, missing = clean_band_median_fill(band, foot)
    assert missing == 2
    assert np.isfinite(filled[foot]).all()
    assert np.isnan(filled[~foot]).all()


def test_landform_relief_index_and_terciles_partition_footprint_cleanly() -> None:
    yy, xx = np.mgrid[0:30, 0:30]
    foot = np.ones((30, 30), dtype=bool)
    foot[:3, :] = False  # 810 in-footprint pixels (divisible by 3 -> 270 each)
    det_elev = (yy * 10.0 + xx * 0.1).astype(np.float32)
    det_slope = (yy * 0.5 + 1.0).astype(np.float32)
    idx, meta = landform_relief_index(det_elev, det_slope, foot, slope_sigma_px=3.0)
    assert meta["missing_det_elev_filled_px"] == 0
    assert np.isnan(idx[~foot]).all()
    assert np.all((idx[foot] > 0.0) & (idx[foot] <= 1.0))

    terc, (q1, q2) = relief_terciles(idx, foot)
    assert q1 < q2
    assert set(terc) == {"basin", "piedmont", "range_front"}
    # Disjoint and exhaustive over footprint
    union = terc["basin"] | terc["piedmont"] | terc["range_front"]
    assert np.array_equal(union, foot)
    assert not np.any(terc["basin"] & terc["piedmont"])
    assert not np.any(terc["piedmont"] & terc["range_front"])
    assert not np.any(terc["basin"] & terc["range_front"])
    for m in terc.values():
        assert abs(int(m.sum()) - 270) <= 1


def test_dti_marginal_gain_is_strictly_increasing_in_kernel_credit_for_on_support_dots() -> None:
    # Any unit-mass dot lying directly on the off-catalogue support has dM = 1.0.
    T, S, M, G = 12_000.0, 37_654.0, 37_654.0, 121_000
    gains = [marginal_gain(T, S, M, G, dT=dt, dM=1.0, p=1.0) for dt in (0.0, 0.25, 0.8, 1.5, 3.0)]
    assert gains == sorted(gains)
    assert len(set(gains)) == len(gains)


def test_greedy_relief_reallocate_holds_count_and_enforces_3px_collar_on_additions() -> None:
    H, W = 36, 36
    foot = np.ones((H, W), dtype=bool)
    cat = np.zeros((H, W), dtype=bool)
    cat[18, :] = True  # horizontal catalogue trace across middle
    dist_cat = distance_transform_edt(~cat)

    donor = np.zeros((H, W), dtype=bool)
    donor[:17, :] = True
    recip = np.zeros((H, W), dtype=bool)
    recip[19:, :] = True

    support = np.zeros((H, W), dtype=bool)
    support[4, 3:33] = True     # donor ridge far from catalogue
    support[15, 5:25] = True    # donor ridge at d_cat=3
    support[16, 8:14] = True    # donor ridge at d_cat=2 (inside 3 px, > 1 px)
    support[20, 4:32] = True    # recipient ridge at d_cat=2 (MUST NOT be added!)
    support[26, 3:33] = True    # recipient ridge at d_cat=8 (eligible!)

    parent = np.zeros((H, W), dtype=bool)
    parent[4, 4:32:3] = True    # 10 spaced donor dots
    parent[4, 5] = True         # 1 crowded donor dot (tiny exclusive credit -> dropped first)
    parent[16, 10] = True       # 1 inherited R0 dot at d_cat=2.0 < 3.0
    parent[26, 5] = True        # 1 existing recipient dot
    n_parent = int(parent.sum())

    out1, stats1 = greedy_relief_reallocate(parent, support, donor, recip, dist_cat, n_shift=4)
    out2, stats2 = greedy_relief_reallocate(parent, support, donor, recip, dist_cat, n_shift=4)
    assert np.array_equal(out1, out2)
    assert stats1 == stats2
    assert int(out1.sum()) == n_parent
    assert stats1["removed_dots"] == 4 and stats1["added_dots"] == 4
    # Crowded dot at (4, 5) must be among the dropped donor dots
    assert not out1[4, 5]
    # Every newly added dot must sit in recipient tercile, on support, and at dist_cat >= 3.0
    added = out1 & ~parent
    assert int(added.sum()) == 4
    assert np.all(recip[added])
    assert np.all(support[added])
    assert float(dist_cat[added].min()) >= 3.0
    # Zero catalogue mass
    assert not np.any(out1 & cat)
    # Gained support credit matches exact component difference after removals
    retained = out1 & parent
    T_ret, _, _ = components_from_arrays(retained.astype(float), support)
    T_fin, _, _ = components_from_arrays(out1.astype(float), support)
    assert (T_fin - T_ret) == pytest.approx(stats1["gained_support_credit"], abs=1e-5)


def test_block_density_cv_behaves_sensibly() -> None:
    foot = np.ones((20, 20), dtype=bool)
    uniform = np.zeros((20, 20), dtype=bool)
    uniform[2::10, 2::10] = True  # 1 dot per 10x10 block -> CV == 0
    assert block_density_cv(uniform, foot, block_px=10) == pytest.approx(0.0)
    clustered = np.zeros((20, 20), dtype=bool)
    clustered[1:5, 1:5] = True
    assert block_density_cv(clustered, foot, block_px=10) > 1.0


def test_repeated_relief_build_is_stopped_by_reservation_guard() -> None:
    with pytest.raises(ValueError, match="duplicate experiment"):
        relief_build.check_relief_reservations()


def test_relief_receipt_ledger_and_cards_are_consistent_and_collision_free() -> None:
    receipt = json.loads((ROOT / "evidence" / "relief_build_receipt.json").read_text(encoding="utf-8"))
    prune_receipt = json.loads((ROOT / "evidence" / "build_receipt.json").read_text(encoding="utf-8"))
    cards = json.loads((ROOT / "ledger" / "mechanism_cards.json").read_text(encoding="utf-8"))

    assert receipt["axis"] == "RELIEF"
    assert len(receipt["variants"]) == 3
    assert not receipt["proxy_reports"]["leakage_canary"]["auc_gt_0_90"]
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["sgmc_control"]["evidence_class"] == "PROXY"

    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as fh:
        all_rows = list(csv.DictReader(fh))

    built_relief = {r["id"]: r for r in all_rows if r["status"] == "BUILT" and r["axis"] == "RELIEF"}
    assert set(built_relief) == {v["id"] for v in receipt["variants"]}

    relief_cards = cards.get("relief", {}).get("variants", cards.get("variants", []))
    card_ids = {c["id"] for c in relief_cards}
    assert card_ids == {v["id"] for v in receipt["variants"]}

    for v in receipt["variants"]:
        row = built_relief[v["id"]]
        assert int(row["n_dots"]) == 37_654
        assert row["sha256"] == v["files"]["nan"]["sha256"]
        assert row["sha256_zeros"] == v["files"]["zeros"]["sha256"]
        assert len(v["form_note"]) <= 140
        assert row["form_note"] == v["form_note"]
        assert 10.0 <= v["mass_shifted_pct"] <= 15.0
        assert 1.0 <= v["pct_changed"] <= 50.0
        assert float(row["pct_changed"]) == pytest.approx(v["pct_changed"], abs=1e-6)
        assert v["files"]["nan"]["added_dots_below_3px"] == 0
        assert v["files"]["zeros"]["added_dots_below_3px"] == 0

    # Global SHA-256 uniqueness across all ledger rows (historical + PRUNE + RELIEF)
    seen_shas: list[str] = []
    for r in all_rows:
        for col in ("sha256", "sha256_zeros"):
            val = (r.get(col) or "").strip()
            if val:
                seen_shas.append(val)
    assert len(seen_shas) == len(set(seen_shas))
