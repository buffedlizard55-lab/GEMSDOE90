from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from src.snap import minimum_nearest_neighbour_distance, offsets_within, snap_dots  # noqa: E402
import build_snap_vertical as build  # noqa: E402


def synthetic_parent() -> np.ndarray:
    parent = np.zeros((21, 21), dtype=bool)
    parent[5, 5] = True  # inherited near-collar dot; must never move
    parent[5, 10] = True
    parent[10, 10] = True
    parent[15, 15] = True
    return parent


def test_offsets_are_euclidean_and_capped() -> None:
    dy, dx, distance = offsets_within(2.0)
    assert len(distance) == 13
    assert np.max(distance) == 2.0
    assert (0 in dy) and (0 in dx)
    assert np.all(np.hypot(dy, dx) <= 2.0)


def test_gain_gated_snap_preserves_count_collar_and_spacing() -> None:
    parent = synthetic_parent()
    response = np.zeros(parent.shape, dtype=float)
    response[5, 9] = 1.0
    response[10, 9] = 1.0
    response[5, 6] = 1.0  # would move the near-collar dot if it were eligible
    distance = np.full(parent.shape, 10.0)
    distance[5, 5] = 2.5
    result = snap_dots(parent, response, np.ones(parent.shape, dtype=bool), distance)
    assert result.candidate.sum() == parent.sum()
    assert len(result.origins) == 2
    assert result.candidate[5, 5]
    assert result.candidate[5, 9] and result.candidate[10, 9]
    assert np.all(result.gains >= 0.10)
    assert np.all(result.displacements <= 2.0)
    assert minimum_nearest_neighbour_distance(result.candidate) >= 2.8
    assert np.array_equal(result.candidate & (distance < 3), parent & (distance < 3))


def test_separation_floor_blocks_otherwise_strong_move() -> None:
    parent = np.zeros((13, 13), dtype=bool)
    parent[5, 5] = True
    parent[5, 8] = True  # 3 px apart: valid parent, but destination (5,6) would clump
    response = np.zeros(parent.shape, dtype=float)
    response[5, 6] = 1.0
    distance = np.full(parent.shape, 10.0)
    result = snap_dots(parent, response, np.ones(parent.shape, dtype=bool), distance)
    assert len(result.origins) == 0
    assert np.array_equal(result.candidate, parent)


def test_gain_gate_and_missing_response_leave_dots_fixed() -> None:
    parent = synthetic_parent()
    response = np.full(parent.shape, np.nan)
    distance = np.full(parent.shape, 10.0)
    result = snap_dots(parent, response, np.ones(parent.shape, dtype=bool), distance)
    assert len(result.origins) == 0
    assert np.array_equal(result.candidate, parent)


def test_snap_receipt_and_ledger_agree() -> None:
    receipt = json.loads((ROOT / "evidence" / "snap_build_receipt.json").read_text())
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as stream:
        rows = [row for row in csv.DictReader(stream)
                if row.get("status") == "BUILT" and (row.get("axis") or "").upper() == "SNAP"
                and row.get("site") == "GEMSDOE90"]
    by_id = {row["id"]: row for row in rows}
    assert set(by_id) == {row["id"] for row in receipt["variants"]}
    assert len(by_id) == 3
    for variant in receipt["variants"]:
        row = by_id[variant["id"]]
        assert row["sha256"] == variant["sha256"]
        assert row["sha256_zeros"] == variant["sha256_zeros"]
        assert float(row["pct_changed"]) == pytest.approx(variant["pct_changed"], abs=1e-6)
        assert row["value"] == variant["value"]
        assert len(row["form_note"]) <= 140


def test_snap_values_are_unique_and_repeat_build_is_refused() -> None:
    reservations = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text())
    occupied = set(reservations["snap_axis"]["occupied_values"])
    selected = set(reservations["snap_axis"]["selected_values"])
    assert selected == {spec["value"] for spec in build.VARIANT_SPECS}
    assert not selected & occupied
    with pytest.raises(ValueError, match="duplicate experiment reservation"):
        build.check_pair_reservations()


def test_snap_receipt_records_real_mechanism_and_hard_constraint_failure() -> None:
    receipt = json.loads((ROOT / "evidence" / "snap_build_receipt.json").read_text())
    assert receipt["parent"]["r0_byte_identity_passed"]
    assert receipt["manifest"]["verified_count"] == 26
    assert receipt["hard_constraint_status"]["general_minimum_3px_from_catalogue"] == "FAIL_INHERITED_FROM_R0"
    assert not receipt["hard_constraint_status"]["upload_eligible"]
    for band in receipt["proxy_reports"]["leakage_canary"]["bands"].values():
        assert not band["triggered"]
        assert band["symmetric_auc"] < 0.90
    for variant in receipt["variants"]:
        stats = variant["parent_diff"]
        assert variant["n_dots"] == 37_654
        assert stats["n_moved"] > 0
        assert variant["pct_changed"] == pytest.approx(100 * stats["n_moved"] / 37_654)
        assert stats["max_displacement_px"] <= 2.0
        assert stats["minimum_nearest_neighbour_distance_px"] >= 2.8
        assert variant["files"]["nan"]["near_catalogue_dots_below_3px"] == 1_611
        assert not variant["files"]["nan"]["general_3px_hard_constraint_passed"]
        assert not variant["upload_eligible"]
        assert all(variant["files"][mode]["checks"].values() for mode in ("nan", "zeros"))


def test_snap_hashes_are_unique_across_full_ledger() -> None:
    receipt = json.loads((ROOT / "evidence" / "snap_build_receipt.json").read_text())
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    own_ids = {row["id"] for row in receipt["variants"]}
    own_hashes = {row[key] for row in receipt["variants"] for key in ("sha256", "sha256_zeros")}
    assert len(own_hashes) == 6
    for row in rows:
        if row["id"] in own_ids:
            continue
        assert not own_hashes & {row.get("sha256", ""), row.get("sha256_zeros", "")}
