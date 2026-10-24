"""Synthetic and artifact integrity tests for matched anisotropic PRUNE without refill."""
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

import build_aniso_prune_norefill as build  # noqa: E402


def test_delete_only_candidate_is_strict_subset_with_exact_accounting() -> None:
    parent = np.zeros((10, 10), dtype=bool)
    parent[[1, 3, 5, 7, 9], [1, 3, 5, 7, 9]] = True
    collar = np.zeros_like(parent)
    collar[5, 5] = True
    candidate, stats = build.make_norefill_candidate(parent, collar)
    assert candidate.sum() == 4
    assert not candidate[5, 5]
    assert not np.any(candidate & ~parent)
    assert stats["n_removed"] == 1
    assert stats["n_added"] == 0
    assert stats["symmetric_difference_px"] == 1
    assert stats["pct_changed_of_parent"] == pytest.approx(20.0)


def test_delete_only_candidate_rejects_nonparent_collar_and_bad_dose() -> None:
    parent = np.zeros((10, 10), dtype=bool)
    parent[0, 0] = True
    outside = np.zeros_like(parent)
    outside[1, 1] = True
    with pytest.raises(ValueError, match="restricted to parent"):
        build.make_norefill_candidate(parent, outside)
    with pytest.raises(ValueError, match="required 1-50%"):
        build.make_norefill_candidate(parent, np.zeros_like(parent))


def test_mask_digest_is_deterministic_and_content_sensitive() -> None:
    a = np.zeros((4, 5), dtype=bool)
    a[2, 3] = True
    b = a.copy()
    assert build.mask_digest(a) == build.mask_digest(b)
    b[2, 3] = False
    assert build.mask_digest(a) != build.mask_digest(b)


def test_receipt_mechanism_counts_proxies_and_snap_feasibility() -> None:
    receipt = json.loads(build.RECEIPT.read_text(encoding="utf-8"))
    assert receipt["axis"] == "PRUNE"
    assert receipt["predictions_frozen_before_proxy"] is True
    assert len(receipt["variants"]) == 3
    assert [v["n_dots"] for v in receipt["variants"]] == [35022, 33991, 33029]
    assert [v["parent_diff"]["n_removed"] for v in receipt["variants"]] == [2632, 3663, 4625]
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["sgmc_control"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["n_withheld_positives"] > 0
    assert not receipt["proxy_reports"]["leakage_canary"]["auc_gt_0_90"]
    pivot = receipt["snap_feasibility_pivot"]
    assert pivot["inherited_R0_dots_below_3px"] == 1611
    assert pivot["dots_with_no_on_support_H19_5_legal_destination_within_2px"] == 822
    assert pivot["dots_with_no_in_footprint_legal_destination_within_2px"] == 30
    for v in receipt["variants"]:
        assert v["parent_diff"]["n_added"] == 0
        assert v["parent_diff"]["strict_subset_of_R0"] is True
        assert v["matched_refill_control"]["removed_count_matches"] is True
        assert len(v["form_note"]) <= 140
        assert "MODEL" in v["predicted_change"] and "not a score" in v["predicted_change"]
        required = {"hypothesis", "mechanism", "non_fault_confounder", "predicted_live_change", "falsifier"}
        assert required <= set(v["mechanism_card"])


def test_ledger_cards_and_hashes_are_consistent() -> None:
    receipt = json.loads(build.RECEIPT.read_text(encoding="utf-8"))
    with build.LEDGER.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_id = {r["id"]: r for r in rows}
    all_hashes = []
    for row in rows:
        for key in ("sha256", "sha256_zeros"):
            if row.get(key):
                all_hashes.append(row[key])
    assert len(all_hashes) == len(set(all_hashes))
    cards = json.loads((ROOT / "ledger" / "mechanism_cards.json").read_text(encoding="utf-8"))
    card_ids = {v["id"] for v in cards["aniso_norefill"]["variants"]}
    assert card_ids == {v["id"] for v in receipt["variants"]}
    for v in receipt["variants"]:
        row = by_id[v["id"]]
        assert row["status"] == "WITHDRAWN"
        assert "IR90-29" in row["notes"] and "do not upload" in row["notes"]
        assert row["axis"] == "PRUNE"
        assert int(row["n_dots"]) == v["n_dots"]
        assert float(row["pct_changed"]) == pytest.approx(v["pct_changed"], abs=1e-6)
        assert row["sha256"] == v["sha256"]
        assert row["sha256_zeros"] == v["sha256_zeros"]
        assert row["form_note"] == v["form_note"]
        assert row["receipt_score"] == ""


def test_own_reproduction_does_not_collide_with_foreign_reservations() -> None:
    report = build.check_reservations()
    assert report["foreign_duplicates"] == []
    assert report["own_reproduction_rows_present"] == 3
