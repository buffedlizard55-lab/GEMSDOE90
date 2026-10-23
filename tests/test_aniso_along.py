"""Artifact integrity tests for fixed-count A5 along-strike PRUNE variants."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_aniso_prune_along as build  # noqa: E402


def test_receipt_fixed_count_ladder_and_report_only_diagnostics() -> None:
    receipt = json.loads(build.RECEIPT.read_text(encoding="utf-8"))
    assert receipt["axis"] == "PRUNE"
    assert receipt["compliance"]["fixed_count_required_and_satisfied"] is True
    assert receipt["compliance"]["parent_isotropic_gt_2px_floor_preserved_on_every_final_dot"] is True
    assert receipt["predictions_frozen_before_proxy"] is True
    assert [v["along_px"] for v in receipt["variants"]] == [1.5, 1.0, 0.5]
    assert all(v["across_px"] == 5.0 for v in receipt["variants"])
    assert all(v["n_dots"] == 37654 for v in receipt["variants"])
    assert all(v["parent_diff"]["n_added"] == v["parent_diff"]["n_removed"] for v in receipt["variants"])
    removed = [v["parent_diff"]["n_removed"] for v in receipt["variants"]]
    assert removed == sorted(removed, reverse=True)  # narrower along collar removes fewer dots
    assert all(1.0 <= v["pct_changed"] <= 50.0 for v in receipt["variants"])
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["sgmc_control"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["n_withheld_positives"] > 0
    assert not receipt["proxy_reports"]["leakage_canary"]["auc_gt_0_90"]
    for v in receipt["variants"]:
        assert v["refill_diagnostics"]["min_catalogue_distance_of_final_set_px"] > 2.0
        assert len(v["form_note"]) <= 140
        assert "MODEL" in v["predicted_change"] and "not a score" in v["predicted_change"]
        required = {"hypothesis", "mechanism", "non_fault_confounder", "predicted_live_change", "falsifier"}
        assert required <= set(v["mechanism_card"])


def test_ledger_cards_hashes_and_counts_match() -> None:
    receipt = json.loads(build.RECEIPT.read_text(encoding="utf-8"))
    with build.LEDGER.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_id = {r["id"]: r for r in rows}
    hashes = [r[k] for r in rows for k in ("sha256", "sha256_zeros") if r.get(k)]
    assert len(hashes) == len(set(hashes))
    cards = json.loads((ROOT / "ledger" / "mechanism_cards.json").read_text(encoding="utf-8"))
    assert {v["id"] for v in cards["aniso_along_refill"]["variants"]} == {v["id"] for v in receipt["variants"]}
    for v in receipt["variants"]:
        row = by_id[v["id"]]
        assert row["status"] == "BUILT"
        assert row["axis"] == "PRUNE"
        assert int(row["n_dots"]) == 37654
        assert float(row["pct_changed"]) == pytest.approx(v["pct_changed"], abs=1e-6)
        assert row["sha256"] == v["sha256"]
        assert row["sha256_zeros"] == v["sha256_zeros"]
        assert row["form_note"] == v["form_note"]
        assert row["receipt_score"] == ""


def test_reproduction_reservation_and_withdrawn_files_are_separate() -> None:
    report = build.check_reservations()
    assert report["foreign_duplicates"] == []
    assert report["own_reproduction_rows_present"] == 3
    withdrawn = json.loads((ROOT / "evidence" / "aniso_norefill_receipt.json").read_text(encoding="utf-8"))
    assert withdrawn["withdrawal"]["irregularity"] == "IR90-27"
    for v in withdrawn["variants"]:
        assert v["status"] == "WITHDRAWN"
        assert not (ROOT / v["files"]["nan"]["path"]).exists()
        assert not (ROOT / v["files"]["zeros"]["path"]).exists()
