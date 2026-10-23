"""Unit and consistency tests for the MASS session (scripts/build_mass_variants.py)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_mass_variants as mass  # noqa: E402


def test_unique_kernel_credit_is_deterministic_and_isolated_dot_gets_one_pixel() -> None:
    dots = np.zeros((21, 21), dtype=bool)
    dots[10, 10] = True
    support = dots.copy()
    credit, (ys, xs) = mass.unique_kernel_credit(dots, support)
    # An isolated dot owns only its own pixel, where k = 1.0.
    assert credit[0] == pytest.approx(1.0)
    assert (ys, xs) == (np.array([10]), np.array([10]))


def test_unique_kernel_credit_drops_for_a_dot_claimed_by_a_neighbour() -> None:
    dots = np.zeros((21, 21), dtype=bool)
    dots[10, 9] = True   # left dot
    dots[10, 11] = True  # right dot
    support = np.zeros((21, 21), dtype=bool)
    support[10, 10] = True  # only support pixel sits between them, 1 px from each
    credit, _ = mass.unique_kernel_credit(dots, support)
    # The single shared support pixel is 1 px from both dots, so one of them owns it
    # at k = 1 - 1/3 and the other owns nothing: neither reaches its own-pixel 1.0.
    assert credit.sum() == pytest.approx(1 - 1 / 3)
    assert np.all(credit < 1.0)
    assert np.count_nonzero(credit) == 1


def test_select_drops_is_deterministic_disjoint_and_ordered() -> None:
    rng = np.random.default_rng(7)
    grid = rng.random((40, 40))
    ys, xs = np.nonzero(grid < 0.05)
    base_idx = np.arange(len(ys))
    fifo = np.full((40, 40), -1, dtype=np.int64)
    fifo[ys, xs] = rng.permutation(len(ys))
    credit = rng.random(len(ys)) * 3 + 1.0
    a = mass.select_drops(base_idx, ys, xs, fifo, credit, "uniq", 10)
    b = mass.select_drops(base_idx, ys, xs, fifo, credit, "uniq", 10)
    assert np.array_equal(a, b) and len(a) == 10
    order_credit = credit[a]
    assert np.all(np.diff(order_credit) >= -1e-12)  # lowest credit first
    f = mass.select_drops(base_idx, ys, xs, fifo, credit, "fifo", 10)
    assert not np.array_equal(f, a)


def test_model_prediction_has_the_right_signs() -> None:
    p = mass.model_prediction(7531)
    for scenario in p["scenarios"].values():
        assert scenario["all_dropped_dots_off_truth"] > 0
        assert scenario["half_dropped_dots_on_truth"] < 0


def test_mass_receipt_ledger_and_notes_agree() -> None:
    receipt = json.loads((ROOT / "evidence" / "build_receipt_mass.json").read_text())
    rows = {r["id"]: r for r in csv.DictReader(
        (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8"))}
    assert {v["value"] for v in receipt["variants"]} == {"fifo20", "uniq20", "uniq30"}
    for v in receipt["variants"]:
        assert v["n_dots"] < mass.R0_DOTS
        assert 1.0 <= v["pct_changed_vs_r0"] <= 50.0
        assert v["min_catalogue_distance_px"] >= 3.0
        row = rows[v["id"]]
        assert row["axis"] == "MASS" and row["status"] == "BUILT"
        assert row["sha256"] == v["files"]["nan"]["sha256"]
        assert row["sha256_zeros"] == v["files"]["zeros"]["sha256"]
        assert len(row["form_note"]) <= 140
        assert row["receipt"] == "N" and row["receipt_score"] == ""
        assert v["files"]["nan"]["checks"]["zero_catalogue_mass"]
        assert v["files"]["nan"]["checks"]["min_catalogue_distance_ge_3px"]


def test_no_two_built_files_share_a_hash_or_a_pair() -> None:
    seen_hash, seen_pair = set(), set()
    for name in ("build_receipt.json", "build_receipt_mass.json"):
        receipt = json.loads((ROOT / "evidence" / name).read_text())
        for v in receipt["variants"]:
            for sha in (v["files"]["nan"]["sha256"], v["files"]["zeros"]["sha256"]):
                assert sha not in seen_hash
                seen_hash.add(sha)
            pair = (receipt["parent"]["id"], receipt["axis"], v["value"])
            assert pair not in seen_pair
            seen_pair.add(pair)
