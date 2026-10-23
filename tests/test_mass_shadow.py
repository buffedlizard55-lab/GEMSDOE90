"""Unit tests for the MASS axis ranking (src/mass.py) and its build receipt.

Nothing here touches competition rasters: the geometry helpers are exercised on
synthetic dot coordinates, and the receipt checks read committed JSON/CSV only.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import dti, mass  # noqa: E402
import build_mass_shadow as build  # noqa: E402


def test_disk_patch_is_inside_the_kernel_and_credit_is_linear() -> None:
    offsets, credit = mass.disk_patch(3.0)
    dist = np.hypot(offsets[:, 0], offsets[:, 1])
    assert np.all(dist < 3.0)
    assert offsets.shape[0] == 25  # the 49-cell 7x7 grid minus the 24 cells at d >= 3 px
    assert np.allclose(credit, 1.0 - dist / 3.0)
    assert credit.max() == 1.0 and credit.min() > 0.0


def test_isolated_dot_exclusive_credit_equals_its_own_disk_credit() -> None:
    pts = np.array([[10.0, 10.0]])
    nbrs = mass.neighbour_lists(pts)
    alive = np.ones(1, dtype=bool)
    e = mass.exclusive_credit(pts, nbrs, alive, 0)
    _offsets, credit = mass.disk_patch(3.0)
    assert e == float(credit.sum())
    assert e < mass.credit_disk_area()  # discrete patch is slightly smaller than the integral


def test_a_close_neighbour_reduces_exclusive_credit_and_shadows_it_monotonically() -> None:
    alone = np.array([[10.0, 10.0]])
    e_alone = mass.exclusive_credit(alone, mass.neighbour_lists(alone), np.ones(1, bool), 0)
    far = np.array([[10.0, 10.0], [10.0, 12.5]])
    near = np.array([[10.0, 10.0], [10.0, 11.0]])
    e_far = mass.exclusive_credit(far, mass.neighbour_lists(far), np.ones(2, bool), 0)
    e_near = mass.exclusive_credit(near, mass.neighbour_lists(near), np.ones(2, bool), 0)
    assert e_alone > e_far > e_near > 0.0


def test_greedy_removal_is_deterministic_nested_and_count_exact() -> None:
    # Two short parallel strands, one of them over-sampled: the shadow order must
    # strip the redundant strand first.
    pts = [[5.0, c] for c in range(2, 18)] + [[8.0, c] for c in range(2, 18, 3)]
    pts = np.asarray(pts, dtype=float)
    nbrs = mass.neighbour_lists(pts)
    n = len(pts)
    snap = (n // 10, n // 5, n // 3)
    a = mass.greedy_shadow_removal(pts, nbrs, n_remove=snap[-1], snapshots=snap)
    again = mass.greedy_shadow_removal(pts, nbrs, n_remove=snap[-1], snapshots=snap)
    assert np.array_equal(a["order"], again["order"])
    assert np.allclose(a["credit_at_removal"], again["credit_at_removal"])
    assert a["removed_masks"][snap[0]].sum() == snap[0]
    assert np.all(a["removed_masks"][snap[0]] <= a["removed_masks"][snap[1]])
    assert np.all(a["removed_masks"][snap[1]] <= a["removed_masks"][snap[2]])
    # Credit at removal is non-decreasing: the greedy eats the cheapest dots first.
    assert np.all(np.diff(a["credit_at_removal"]) >= -1e-12)


def test_removing_a_fully_shadowed_dot_is_strictly_favourable_under_the_algebra() -> None:
    # Removing a dot that supplies no credit (T unchanged) removes 0.2*(1-c) of
    # denominator, so DTI must rise. c is the dot's own credit to its truth pixel.
    T, S, M, G = 10.0, 40.0, 10.0, 30
    before = dti.dti_from_components(T, S, M, G)
    for c in (0.0, 0.5, 0.9):
        after = dti.dti_from_components(T, S - 1.0, M - c, G)
        assert after > before


def test_predicted_removal_delta_is_positive_for_cheap_dots_and_negative_for_costly_ones() -> None:
    cheap = mass.predicted_removal_delta(credit_sum=1000.0, n_removed=3765, n_parent=37654,
                                         footprint_px=5_167_373, mean_dot_credit=0.3, truth_px=60_000)
    costly = mass.predicted_removal_delta(credit_sum=100_000.0, n_removed=3765, n_parent=37654,
                                         footprint_px=5_167_373, mean_dot_credit=0.3, truth_px=60_000)
    assert cheap > 0.0 > costly


def test_build_receipt_records_three_single_axis_subset_variants() -> None:
    receipt = json.loads((ROOT / "evidence" / "mass_build_receipt.json").read_text())
    assert receipt["axis"] == "MASS"
    variants = receipt["variants"]
    assert len(variants) == 3
    assert all(v["removal_statistics"]["sub3px_dots_removed"] < 300 for v in variants)
    for v in variants:
        assert v["status"] == "BUILT"
        assert v["added_dots"] == 0                       # subset only, no refill, no moves
        assert 1.0 <= v["pct_changed"] <= 50.0
        assert v["n_dots"] == build.R0_DOTS - v["removed_dots"]
        assert len(v["form_note"]) <= 140
        assert v["files"]["nan"]["checks"]["zero_catalogue_mass"]
        assert v["files"]["nan"]["checks"]["no_new_mass_within_3px"]
        assert v["files"]["nan"]["checks"]["subset_of_R0_no_additions_no_moves"]
        assert v["model_bracket"]["low"] < v["model_bracket"]["high"]
    assert len({v["sha256"] for v in variants}) == 3
    assert len({v["sha256_zeros"] for v in variants}) == 3


def test_ledger_carries_every_built_variant_and_no_receipt_claim() -> None:
    receipt = json.loads((ROOT / "evidence" / "mass_build_receipt.json").read_text())
    rows = list(csv.DictReader((ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8")))
    by_id = {r["id"]: r for r in rows}
    for v in receipt["variants"]:
        row = by_id[v["id"]]
        assert row["sha256"] == v["sha256"]
        assert row["axis"] == "MASS"
        assert row["status"] == "BUILT"
        assert row["receipt"] == "N" and row["receipt_score"] == ""   # agent never submits
    led_sha = {r["sha256"] for r in rows if r["sha256"]}
    assert len(led_sha) == sum(1 for r in rows if r["sha256"])       # no duplicate hashes


def test_mass_doses_do_not_collide_with_recorded_sibling_values() -> None:
    reg = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text())
    block = reg["mass_axis"]
    assert tuple(v.replace("pct", "") for v in block["selected_values"]) == ("shadow10", "shadow20", "shadow30")
    joined = " ".join(block["sibling_values"]).lower()
    assert "shadow" not in joined
    build.check_reservations()  # must not raise for the selected doses
