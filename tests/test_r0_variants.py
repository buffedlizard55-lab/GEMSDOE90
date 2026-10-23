from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_r0_variants as build  # noqa: E402


def test_fifo_bfs_rank_covers_exact_8_connected_support_and_is_deterministic() -> None:
    mask = np.zeros((8, 9), dtype=bool)
    mask[1, 1:5] = True
    mask[2, 4] = True
    mask[5, 7:9] = True
    rank1 = build.fifo_bfs_visit_rank(mask)
    rank2 = build.fifo_bfs_visit_rank(mask)
    assert np.array_equal(rank1, rank2)
    assert np.all(rank1[mask] >= 0)
    assert np.all(rank1[~mask] == -1)
    assert sorted(rank1[mask].tolist()) == list(range(int(mask.sum())))


def test_original_dot_thin_is_deterministic_and_keeps_only_support() -> None:
    mask = np.zeros((15, 20), dtype=bool)
    mask[3, 2:16] = True
    mask[4, 5:12] = True
    rank = build.fifo_bfs_visit_rank(mask)
    out = build.original_dot_thin(mask, rank, 2.8)
    out_again = build.original_dot_thin(mask, rank, 2.8)
    assert np.array_equal(out, out_again)
    assert np.all(~out | mask)
    assert out.any()
    assert out.sum() < mask.sum()


def test_prune_values_are_unique_in_cross_session_reservations() -> None:
    registry = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text())
    occupied = {float(v) for source in registry["sources"] for v in source["values_px"]}
    assert tuple(build.THRESHOLDS) == tuple(registry["available_selected_values_px"])
    assert not occupied.intersection(build.THRESHOLDS)


def test_repeated_build_is_stopped_by_pair_reservation_after_first_build() -> None:
    # Once the session variants are recorded, the local ledger is the authoritative duplicate guard.
    with pytest.raises(ValueError, match="duplicate experiment reservation"):
        build.check_pair_reservations()


def test_submission_notes_are_under_140_chars() -> None:
    receipt = json.loads((ROOT / "evidence" / "build_receipt.json").read_text())
    assert len(receipt["variants"]) == 3
    assert all(len(row["form_note"]) <= 140 for row in receipt["variants"])


def _built_variants():
    """Every BUILT variant from every session receipt in evidence/."""
    out = []
    for name in ("build_receipt.json", "build_receipt_mass.json"):
        path = ROOT / "evidence" / name
        if path.is_file():
            out.extend(json.loads(path.read_text())["variants"])
    return out


def test_ledger_and_build_receipt_agree_on_every_built_hash() -> None:
    import csv

    receipt = {"variants": _built_variants()}
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as fh:
        built = {row["id"]: row for row in csv.DictReader(fh) if row["status"] == "BUILT"}
    assert set(built) == {v["id"] for v in receipt["variants"]}
    for v in receipt["variants"]:
        row = built[v["id"]]
        assert row["sha256"] == v["files"]["nan"]["sha256"]
        assert row["sha256_zeros"] == v["files"]["zeros"]["sha256"]
        pct = v.get("pct_changed", v.get("pct_changed_vs_r0"))
        assert float(row["pct_changed"]) == pytest.approx(pct, abs=1e-6)
        assert 1.0 <= pct <= 50.0


def test_built_hashes_are_not_reused_from_any_other_ledger_row() -> None:
    import csv

    receipt = {"variants": _built_variants()}
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    built_ids = {v["id"] for v in receipt["variants"]}
    others = [r for r in rows if r["id"] not in built_ids]
    other_hashes = {r["sha256"] for r in others if r["sha256"]} | {r["sha256_zeros"] for r in others if r["sha256_zeros"]}
    ours = set()
    for v in receipt["variants"]:
        ours |= {v["files"]["nan"]["sha256"], v["files"]["zeros"]["sha256"]}
    assert len(ours) == 2 * len(receipt["variants"])  # no repeat among our own variants either
    assert not ours & other_hashes
