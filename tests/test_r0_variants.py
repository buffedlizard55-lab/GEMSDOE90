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


def test_restore_specs_are_already_built_and_match_ledger() -> None:
    receipt = json.loads((ROOT / "evidence" / "build_receipt.json").read_text())
    assert build.recorded_pairs_match_ledger(receipt)
    # Restoration is not permission to run the same experiment a second time.
    with pytest.raises(ValueError, match="duplicate experiment reservation"):
        build.check_pair_reservations()
