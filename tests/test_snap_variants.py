"""Unit and consistency tests for the SNAP (cross-strike) session.

Pure helpers are tested on synthetic geometry; ledger/receipt tests read only repository files
(never competition rasters, which are gitignored).  File-level gates are exercised by
`scripts/build_snap_variants.py --verify` on a machine that has the pinned inputs restored.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("snapbuild", ROOT / "scripts" / "build_snap_variants.py")
SNAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAP)


def test_rank_normalise_is_bounded_and_monotone() -> None:
    values = np.array([3.0, 1.0, 2.0, 2.0, 10.0])
    ranks = SNAP._rank_normalise(values)
    assert ranks.min() == 0.0 and ranks.max() == 1.0
    assert ranks[1] < ranks[2] == ranks[3] < ranks[4]
    assert ranks[0] > ranks[3]


def test_candidate_offsets_respect_cap() -> None:
    for cap in (1.0, 1.5, 2.0):
        offsets = SNAP.candidate_offsets(cap)
        assert offsets, "cap must admit at least one integer offset"
        assert all(1.0 <= d <= cap + 1e-9 for _dy, _dx, d, _ in offsets)
        assert (0, 0, 0.0, 0.0) not in offsets


def test_directional_offsets_stay_inside_the_half_disc() -> None:
    for normal in (np.array([1.0, 0.0]), np.array([0.0, 1.0]), np.array([np.sqrt(0.5), np.sqrt(0.5)])):
        for dy, dx, dist in SNAP.directional_offsets(normal, 2.0):
            cos_to_normal = abs((dy * normal[0] + dx * normal[1]) / dist)
            assert cos_to_normal >= np.cos(np.pi / 4) - 1e-9
            assert dist <= 2.0 + 1e-9
    # a pure +x normal must never admit a pure along-strike (+-y) 1 px step
    assert (1, 0, 1.0) not in SNAP.directional_offsets(np.array([0.0, 1.0]), 2.0)


def test_strike_normal_recovers_the_perpendicular_of_a_synthetic_line() -> None:
    east_west = np.array([[10.0, x] for x in range(-6, 7)])   # varies along x -> normal along y
    north_south = np.array([[y, 10.0] for y in range(-6, 7)])  # varies along y -> normal along x
    n_ew = SNAP.strike_normal((10.0, 0.0), cKDTree(east_west), east_west)
    n_ns = SNAP.strike_normal((0.0, 10.0), cKDTree(north_south), north_south)
    assert abs(abs(n_ew[1]) - 0.0) < 1e-6 and abs(abs(n_ew[0]) - 1.0) < 1e-6
    assert abs(abs(n_ns[0]) - 0.0) < 1e-6 and abs(abs(n_ns[1]) - 1.0) < 1e-6


def test_occupancy_free_enforces_two_pixel_separation() -> None:
    occ = np.zeros((12, 12), dtype=bool)
    occ[6, 6] = True
    assert not SNAP.occupancy_free(occ, 6, 6)   # occupied
    assert not SNAP.occupancy_free(occ, 6, 7)   # 1.0 px away
    assert not SNAP.occupancy_free(occ, 7, 7)   # 1.41 px away
    assert SNAP.occupancy_free(occ, 6, 8)       # exactly 2.0 px away
    assert SNAP.occupancy_free(occ, 8, 8)       # 2.83 px away


def _receipt() -> dict:
    return json.loads((ROOT / "evidence" / "snap_build_receipt.json").read_text(encoding="utf-8"))


def _ledger_rows() -> list[dict]:
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_receipt_has_three_arms_with_distinct_hashes_and_a_dose_ladder() -> None:
    receipt = _receipt()
    variants = receipt["variants"]
    assert len(variants) == 3
    assert len({v["sha256"] for v in variants}) == 3
    assert len({v["sha256_zeros"] for v in variants}) == 3
    moved = [v["parent_diff"]["snap"]["dots_moved"] for v in variants]
    multipliers = [v["parent_diff"]["epsilon_multiplier"] for v in variants]
    assert multipliers == sorted(multipliers), "arms must be ordered permissive -> strict"
    assert moved == sorted(moved, reverse=True), "a stricter threshold must move fewer dots"
    for v in variants:
        assert v["n_dots"] == 37_654
        assert v["axis"] == "SNAP"
        assert v["status"] == "BUILT"
        assert len(v["form_note"]) <= 140
        assert v["parent_diff"]["snap"]["mean_displacement_px"] <= 2.0 + 1e-9
        assert v["parent_diff"]["snap"]["min_sep_px"] >= 2.0


def _all_receipt_variants() -> dict[str, dict]:
    """Union of every session receipt in evidence/ that records built variants."""
    out: dict[str, dict] = {}
    for path in sorted((ROOT / "evidence").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for variant in data.get("variants", []) if isinstance(data, dict) else []:
            if isinstance(variant, dict) and "id" in variant and "files" in variant:
                out[variant["id"]] = variant
    return out


def test_snap_ledger_rows_match_the_receipt_and_the_ledger_is_complete() -> None:
    """The ledger is cumulative: every BUILT row must belong to some session receipt.

    Sibling sessions merge their own receipts into the same repository, so equality against
    this session's receipt alone would break on any merge; the union is the correct invariant.
    """
    receipt = _receipt()
    rows = {r["id"]: r for r in _ledger_rows() if r["status"] == "BUILT"}
    expected = set(_all_receipt_variants())
    assert expected == set(rows), "every BUILT row must belong to a recorded session receipt"
    for v in receipt["variants"]:
        row = rows[v["id"]]
        assert row["sha256"] == v["files"]["nan"]["sha256"]
        assert row["sha256_zeros"] == v["files"]["zeros"]["sha256"]
        assert row["axis"] == "SNAP" and row["parent"] == "h33-h33-2-b2"
        assert row["receipt"] == "N" and row["receipt_score"] == ""
        assert row["value"].startswith("cross-strike consensus")


def test_no_snap_hash_is_reused_by_any_other_ledger_row() -> None:
    receipt = _receipt()
    ours = {v["sha256"] for v in receipt["variants"]} | {v["sha256_zeros"] for v in receipt["variants"]}
    mine = {v["id"] for v in receipt["variants"]}
    others = {r["sha256"] for r in _ledger_rows() if r["id"] not in mine and r["sha256"]}
    others |= {r["sha256_zeros"] for r in _ledger_rows() if r["id"] not in mine and r["sha256_zeros"]}
    assert not (ours & others)


def test_snap_tokens_do_not_collide_with_any_recorded_sibling_value() -> None:
    reservations = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text(encoding="utf-8"))
    existing: set[str] = set()
    for values in reservations["snap_audit"]["existing_snap_values"].values():
        existing |= {str(v).strip().lower() for v in values}
    for token, _mult in SNAP.DOSES:
        assert f"snapx{token}" not in existing
        assert not any(f"snapx{token}" in value for value in existing)


def test_snap_arms_are_exempt_from_the_one_to_fifty_percent_rule_but_recorded() -> None:
    receipt = _receipt()
    for v in receipt["variants"]:
        pct = v["pct_changed"]
        assert pct > 0.0
        # SNAP is explicitly exempt from the 1-50% change rule (brief s5); the number must still
        # be recorded honestly, and a reader must be able to see it exceeds 50%.
        assert v["parent_diff"]["pct_of_parent_dots_changed"] == pytest.approx(pct, abs=1e-9)


@pytest.mark.skipif(
    not (ROOT / "evidence" / "snap_build_receipt.json").is_file(),
    reason="receipt absent",
)
def test_receipt_keeps_the_parent_claim_labelled_as_a_claim() -> None:
    parent = _receipt()["parent"]
    assert parent["evidence_class"] == "CLAIM"
    assert parent["claimed_live_score"] == pytest.approx(0.2778)
    assert parent["r0_byte_identity_passed"] is True
    assert parent["d28_symmetric_difference_px"] == 0
