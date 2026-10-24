"""Synthetic unit tests and receipt/ledger integrity checks for A5 q50 PRUNE refill (IR90-35 fix).

CI runs `pytest -q` without the gitignored `.cache/` rasters, so all operator tests use
synthetic arrays while artifact tests inspect committed JSON/CSV receipts.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from aniso_prune import build_strike_field, collar_membership, refill_mask  # noqa: E402
import build_aniso_prune_q50 as build  # noqa: E402
from src.prune_q50 import (  # noqa: E402
    q50_prune_and_refill,
    q50_refill_pool,
    refill_Audit_stats,
    support_credit_comparison,
    unmapped_support_mask,
)


def _synthetic_problem(h: int = 120, w: int = 80):
    foot = np.ones((h, w), dtype=bool)
    cat = np.zeros((h, w), dtype=bool)
    # Vertical mapped fault trace down column 40
    cat[10 : h - 10, 40] = True
    field = build_strike_field(cat)

    support = np.zeros((h, w), dtype=bool)
    # Cross-strike flank ridges at col 43 (3 px across strike) and col 37
    support[15 : h - 15, 43] = True
    support[15 : h - 15, 37] = True
    # Outside-collar ridges distributed across all 5 km (20 px) blocks
    for col in (10, 22, 58, 70):
        support[4 : h - 4, col] = True

    parent = np.zeros((h, w), dtype=bool)
    # Collar dots on flank ridges
    parent[20 : h - 20 : 6, 43] = True
    parent[20 : h - 20 : 6, 37] = True
    # Along-strike tip continuation dot at row h-8, col 40 (2 px beyond tip at h-11, >1 px along strike)
    support[h - 8, 40] = True
    parent[h - 8, 40] = True
    # Outside-collar parent dots spaced every 4 px so R=3 px kernel saddles exist at midpoints
    for col in (10, 22, 58, 70):
        parent[6 : h - 6 : 4, col] = True

    return foot, cat, support, parent, field


def test_q50_refill_pool_rejects_sub3px_collar_and_retained_dots() -> None:
    foot, cat, support, parent, field = _synthetic_problem()
    with pytest.raises(ValueError, match=">= 3.0 px"):
        q50_refill_pool(
            foot, support, cat, parent, field, across_px=5.0, along_px=1.0,
            collar_membership_fn=collar_membership, min_cat_dist_px=2.5,
        )
    pool = q50_refill_pool(
        foot, support, cat, parent, field, across_px=5.0, along_px=1.0,
        collar_membership_fn=collar_membership, min_cat_dist_px=3.0,
    )
    assert not np.any(pool & cat)
    assert not np.any(pool & parent)
    assert float(field.dist[pool].min()) >= 3.0
    supp_unm = unmapped_support_mask(foot, support, cat, field, 5.0, 1.0, collar_membership)
    assert np.all(pool <= supp_unm)


def test_q50_prune_and_refill_holds_count_spreads_blocks_and_beats_fifo_credit() -> None:
    foot, cat, support, parent, field = _synthetic_problem()
    res1 = q50_prune_and_refill(
        parent, foot, support, cat, field, across_px=5.0, along_px=1.0,
        collar_membership_fn=collar_membership, block_px=20, min_cat_dist_px=3.0,
    )
    res2 = q50_prune_and_refill(
        parent, foot, support, cat, field, across_px=5.0, along_px=1.0,
        collar_membership_fn=collar_membership, block_px=20, min_cat_dist_px=3.0,
    )
    assert np.array_equal(res1["candidate"], res2["candidate"])
    assert res1["n_candidate"] == res1["n_parent"]
    assert res1["n_removed"] == res1["n_added"] > 0
    assert float(field.dist[res1["refill"]].min()) >= 3.0

    # Compare against row-ordered FIFO refill on the same pool
    rank = np.full(support.shape, -1, dtype=np.int32)
    sy, sx = np.nonzero(support)
    rank[sy, sx] = np.arange(sy.size, dtype=np.int32)
    ref_fifo = refill_mask(res1["pool"], rank, res1["n_removed"])
    cand_fifo = res1["retained"] | ref_fifo

    q50_audit = refill_Audit_stats(res1["refill"], res1["retained"], parent, field.dist, block_px=20)
    fifo_audit = refill_Audit_stats(ref_fifo, res1["retained"], parent, field.dist, block_px=20)
    assert q50_audit["refill_dots_below_3px_catalogue"] == 0
    assert q50_audit["refill_bbox_y"][1] > fifo_audit["refill_bbox_y"][1]

    comp = support_credit_comparison(
        parent=parent,
        retained=res1["retained"],
        cand_q50=res1["candidate"],
        cand_fifo=cand_fifo,
        support_offcat=support & foot & ~cat,
        support_unmapped=res1["support_unmapped"],
    )
    assert comp["q50_refill_recovered_T_all_offcat"] >= comp["fifo_refill_recovered_T_all_offcat"]


def test_receipt_records_ir90_35_northern_strip_audit_and_three_q50_variants() -> None:
    receipt = json.loads(build.RECEIPT.read_text(encoding="utf-8"))
    assert receipt["axis"] == "PRUNE"
    assert receipt["irregularity_resolved"] == "IR90-41"
    assert receipt["predictions_frozen_before_proxy"] is True
    assert all(receipt["compliance"].values())

    # All 9 prior BUILT PRUNE variants must be audited and shown to fail addition_evenness_gate
    prior = receipt["prior_prune_fifo_northern_strip_audit"]["variants_audited"]
    assert len(prior) == 9
    for row in prior:
        assert row["passes_addition_evenness_gate"] is False
        assert row["refill_bbox_y"][0] == 0
        assert row["refill_bbox_y"][1] <= 264
        assert row["refill_fraction_in_north_strip_y_le_264"] == 1.0
        assert row["blocks_with_zero_additions_among_20plus"] >= 739

    # All 3 new q50 PRUNE variants must pass addition_evenness_gate with 0/848 dense blocks starved
    variants = receipt["variants"]
    assert [v["value"] for v in variants] == ["anisoA5L0p5q50", "anisoA5L1q50", "anisoA5L2q50"]
    assert [v["along_px"] for v in variants] == [0.5, 1.0, 2.0]
    assert [v["parent_diff"]["n_removed"] for v in variants] == [1333, 2386, 3663]
    for v in variants:
        assert v["status"] == "BUILT"
        assert v["n_dots"] == 37654
        assert v["parent_diff"]["n_added"] == v["parent_diff"]["n_removed"]
        assert 1.0 <= v["pct_changed"] <= 50.0
        assert len(v["form_note"]) <= 140
        assert "MODEL" in v["predicted_change"] and "not a score" in v["predicted_change"]
        q_aud = v["refill_diagnostics"]["q50_spatial_and_shadow_audit"]
        f_aud = v["refill_diagnostics"]["paired_fifo_spatial_and_shadow_audit"]
        cred = v["refill_diagnostics"]["support_credit_comparison_vs_fifo"]
        assert q_aud["passes_addition_evenness_gate"] is True
        assert f_aud["passes_addition_evenness_gate"] is False
        assert q_aud["refill_dots_below_3px_catalogue"] == 0
        assert q_aud["min_catalogue_distance_of_refill_px"] >= 3.0
        assert q_aud["addition_evenness_report"]["blocks_with_zero_additions_among_20plus"] == 0
        assert cred["q50_vs_fifo_recovered_T_ratio"] > 2.0
        assert cred["q50_net_delta_T_outside_collar_vs_r0"] > 0.0
        assert v["parent_diff"]["removed_to_nearest_added_median_px"] < 20.0

    # Proxy reports must be labeled PROXY and canary must not trip
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["sgmc_control"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["leakage_canary"]["evidence_class"] == "PROXY"
    assert not receipt["proxy_reports"]["leakage_canary"]["auc_gt_0_90"]


def test_ledger_reservations_and_mechanism_cards_match_q50_receipt() -> None:
    receipt = json.loads(build.RECEIPT.read_text(encoding="utf-8"))
    with build.LEDGER.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_id = {r["id"]: r for r in rows}
    all_hashes = [r[k] for r in rows for k in ("sha256", "sha256_zeros") if r.get(k)]
    assert len(all_hashes) == len(set(all_hashes))

    res = json.loads(build.RESERVATIONS.read_text(encoding="utf-8"))
    assert res["anisotropic_q50_refill_reservations"]["occupied_values"] == [
        "anisoA5L0p5q50",
        "anisoA5L1q50",
        "anisoA5L2q50",
    ]
    assert build.check_reservations()["foreign_duplicates"] == []
    assert build.check_reservations()["own_reproduction_rows_present"] == 3

    cards = json.loads(build.CARDS_JSON.read_text(encoding="utf-8"))
    card_ids = {c["id"] for c in cards["aniso_q50_refill"]["variants"]}
    assert card_ids == {v["id"] for v in receipt["variants"]}

    for v in receipt["variants"]:
        row = by_id[v["id"]]
        assert row["status"] == "BUILT"
        assert row["axis"] == "PRUNE"
        assert row["value"] == v["value"]
        assert int(row["n_dots"]) == 37654
        assert float(row["pct_changed"]) == pytest.approx(v["pct_changed"], abs=1e-6)
        assert row["sha256"] == v["sha256"]
        assert row["sha256_zeros"] == v["sha256_zeros"]
        assert row["form_note"] == v["form_note"]
        assert row["receipt"] == "N" and row["receipt_score"] == ""
