"""Unit tests for the high-dose MASS session.

Geometry helpers are exercised on synthetic coordinates; everything else reads only
committed JSON/CSV. No competition raster is opened, so CI runs without the pinned data.
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

import build_mass_high_dose as build  # noqa: E402

RECEIPT = ROOT / "evidence" / "mass_high_dose_receipt.json"
CARD_KEYS = {
    "hypothesis", "mechanism", "non_fault_confounder", "matched_count_control",
    "competing_prediction", "predicted_live_change", "model_bracket", "falsifier",
    "structural_geologist_note",
}


def test_random_removal_is_seeded_unique_and_count_exact() -> None:
    a = build.random_removal(1000, 400, seed=7)
    b = build.random_removal(1000, 400, seed=7)
    c = build.random_removal(1000, 400, seed=8)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)
    assert len(a) == 400 and len(np.unique(a)) == 400
    assert np.array_equal(a, np.sort(a))
    assert a.min() >= 0 and a.max() < 1000


def _grid_dots(shape: tuple[int, int] = (400, 400), step: int = 5) -> tuple[np.ndarray, np.ndarray]:
    ys, xs = np.nonzero(np.zeros(shape, dtype=bool))
    yy, xx = np.mgrid[0:shape[0]:step, 0:shape[1]:step]
    return yy.ravel(), xx.ravel()


def test_spatial_report_accepts_uniform_removal_and_rejects_a_corner_wipeout() -> None:
    ys, xs = _grid_dots()
    rng = np.random.default_rng(0)
    uniform = np.zeros(len(ys), dtype=bool)
    uniform[rng.choice(len(ys), len(ys) // 2, replace=False)] = True
    ok = build.spatial_removal_report(uniform, ys, xs, (400, 400), 0.5)
    assert build.region_evenness_gate(ok)
    assert ok["largest_emptied_cluster_blocks"] <= build.MAX_EMPTIED_CLUSTER_BLOCKS

    corner = (ys < 150) & (xs < 150)          # one contiguous south-west wipeout
    bad = build.spatial_removal_report(corner, ys, xs, (400, 400), 0.5)
    assert not build.region_evenness_gate(bad)
    assert bad["largest_emptied_cluster_blocks"] > build.MAX_EMPTIED_CLUSTER_BLOCKS


def test_strand_report_finds_one_long_strand_for_a_continuous_line() -> None:
    dots = np.zeros((60, 60), dtype=bool)
    dots[30, 5:45:2] = True                    # 20 dots, 2 px apart = one strand
    report = build.strand_report(dots, link_px=5.0)
    assert report["dots"] == 20
    assert report["strands"] == 1
    assert report["strands_ge_10dots"] == 1
    assert report["largest_strand_dots"] == 20
    assert report["fraction_nn_beyond_kernel"] == 0.0


def test_strand_report_separates_a_sparse_field_into_isolated_dots() -> None:
    dots = np.zeros((60, 60), dtype=bool)
    dots[5:55:10, 5:55:10] = True              # 25 dots, 10 px apart = no links at 5 px
    report = build.strand_report(dots, link_px=5.0)
    assert report["strands"] == 25
    assert report["strands_ge_10dots"] == 0
    assert report["fraction_nn_beyond_kernel"] == 1.0


def test_receipt_records_three_new_single_axis_subset_arms_with_full_cards() -> None:
    receipt = json.loads(RECEIPT.read_text())
    assert receipt["axis"] == "MASS"
    assert receipt["parent"]["id"] == "h33-h33-2-b2"
    assert receipt["parent"]["evidence_class"] == "CLAIM"          # never promoted to a score
    variants = receipt["variants"]
    assert len(variants) == 3
    assert [(v["selection_rule"], v["dose_pct"]) for v in variants] == [
        ("shadow", 40), ("shadow", 48), ("random", 40)]
    for v in variants:
        assert v["status"] == "BUILT"
        assert v["added_dots"] == 0 and v["moved_dots"] == 0        # subset only
        assert 1.0 <= v["pct_changed"] <= 50.0
        assert v["n_dots"] == build.R0_DOTS - v["removed_dots"]
        assert v["n_dots"] == v["retained_dots"]
        assert len(v["form_note"]) <= 140
        assert CARD_KEYS.issubset(v["mechanism_card"])
        assert v["files"]["nan"]["checks"]["zero_catalogue_mass"]
        assert v["files"]["nan"]["checks"]["no_new_mass_within_3px"]
        assert v["files"]["nan"]["checks"]["subset_of_R0_no_additions_no_moves"]
        assert build.region_evenness_gate(v["spatial_removal"])
        assert v["model_bracket"]["low"] < v["model_bracket"]["high"]
        assert v["predicted_change"].endswith("not a score)")
    assert len({v["sha256"] for v in variants}) == 3
    assert len({v["sha256_zeros"] for v in variants}) == 3
    random_arm = next(v for v in variants if v["selection_rule"] == "random")
    assert random_arm["seed"] == build.SEED


def test_deep_arm_stops_below_the_region_isolation_threshold() -> None:
    """50% shadow is recorded as a rejected probe, not as a candidate, and 48% passes."""
    receipt = json.loads(RECEIPT.read_text())
    probes = receipt["ranking"]["rejected_region_isolation_probes"]
    assert "shadow50pct" in probes
    assert probes["shadow50pct"]["candidate_built"] is False
    assert probes["shadow50pct"]["passes_region_evenness_gate"] is False
    assert all(not probes[k]["passes_region_evenness_gate"] for k in ("fifo10pct", "fifo20pct", "fifo40pct"))
    assert probes["fifo40pct"]["largest_emptied_cluster_blocks"] > 100   # one big contiguous hole
    assert max(v["dose_pct"] for v in receipt["variants"]) == 48
    assert receipt["region_evenness_gate"]["max_emptied_cluster_blocks"] == build.MAX_EMPTIED_CLUSTER_BLOCKS


def test_ledger_carries_every_built_arm_and_no_receipt_claim() -> None:
    receipt = json.loads(RECEIPT.read_text())
    rows = list(csv.DictReader((ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8")))
    by_id = {r["id"]: r for r in rows}
    for v in receipt["variants"]:
        row = by_id[v["id"]]
        assert row["sha256"] == v["sha256"]
        assert row["sha256_zeros"] == v["sha256_zeros"]
        assert row["axis"] == "MASS"
        assert row["status"] == "BUILT"
        assert row["receipt"] == "N" and row["receipt_score"] == ""    # agent never submits
        assert row["date"] == ""
    led = [r["sha256"] for r in rows if r["sha256"]]
    assert len(led) == len(set(led))                                  # no duplicate submissions
    zeros = [r["sha256_zeros"] for r in rows if r["sha256_zeros"]]
    assert len(zeros) == len(set(zeros))


def test_no_rejected_or_region_isolated_arm_is_left_in_the_ledger() -> None:
    rows = list(csv.DictReader((ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8")))
    joined = " ".join(f"{r.get('id', '')} {r.get('value', '')}".lower() for r in rows)
    assert "fifo-drop" not in joined and "fifo40" not in joined
    assert "shadow-drop 50%" not in joined


def test_pair_reservation_fails_closed_after_the_first_build() -> None:
    with pytest.raises(ValueError, match="duplicate experiment reservation"):
        build.check_reservations()


def test_rejected_and_selected_values_are_recorded_in_the_reservation_registry() -> None:
    reg = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text())
    block = reg["mass_high_dose"]
    assert block["selected_values"] == ["shadow40pct", "shadow48pct", "rand40pct"]
    assert "fifo40pct" in block["rejected_values"] and "shadow50pct" in block["rejected_values"]
    joined = " ".join(block["sibling_values"]).lower()
    assert "40pct" not in joined and "48pct" not in joined       # nothing above 30% anywhere else
    assert "random" not in joined and "rand" not in joined        # no credit-blind control elsewhere
