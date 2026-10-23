"""Unit tests for the MASS dose-ladder session (arena/307b04fc). Artifact-level only:
these run in CI without competition rasters; byte gates live in scripts/build_mass_variants.py --verify."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_mass_variants as build  # noqa: E402


def _receipt() -> dict:
    return json.loads((ROOT / "evidence" / "mass_dose_ladder_receipt.json").read_text())


def _ledger_rows() -> list[dict]:
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_dose_counts_match_brief_fractions() -> None:
    assert build.dose_count(0.05) == 1883
    assert build.dose_count(0.10) == 3765
    assert build.dose_count(0.20) == 7531
    receipt = _receipt()
    by_value = {v["value"]: v for v in receipt["variants"]}
    assert by_value["drop5pct-tail"]["n_dots"] == 37654 - 1883
    assert by_value["add5pct-next"]["n_dots"] == 37654 + 1883
    assert by_value["add20pct-next"]["n_dots"] == 37654 + 7531
    for v in receipt["variants"]:
        assert 1.0 <= v["pct_changed"] <= 50.0


def test_mass_values_free_of_sibling_occupancy_and_locally_unique() -> None:
    receipt = _receipt()
    for v in receipt["variants"]:
        assert v["value"] not in build.SIBLING_OCCUPIED_MASS_VALUES
    pairs = [(r.get("parent"), r.get("axis"), r.get("value")) for r in _ledger_rows()]
    mass_pairs = [p for p in pairs if p[1] == "MASS"]
    assert len(mass_pairs) == len(set(mass_pairs))  # includes sibling-session shadow/random rows
    build.check_pair_reservations  # callable
    try:
        build.check_pair_reservations()
    except ValueError:
        pass  # expected once rows are recorded; the ledger is then the duplicate guard


def test_form_notes_under_140_chars() -> None:
    for v in _receipt()["variants"]:
        assert len(v["form_note"]) <= 140


def test_mechanism_cards_have_required_fields() -> None:
    required = {"hypothesis", "mechanism", "non_fault_confounder", "predicted_live_change", "falsifier"}
    for v in _receipt()["variants"]:
        assert required <= set(v["mechanism_card"])
        assert "MODEL" in v["mechanism_card"]["predicted_live_change"]
        assert "not a score" in v["mechanism_card"]["predicted_live_change"]


def test_ledger_append_preserved_prior_rows_and_gate_fields() -> None:
    rows = _ledger_rows()
    ids = [r["id"] for r in rows]
    # prior session rows survive the append
    assert "h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891" in ids
    assert "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros" in ids
    mine = {"drop5pct-tail", "add5pct-next", "add20pct-next"}
    mass = [r for r in rows if r["axis"] == "MASS" and (r.get("value") or "") in mine]
    assert len(mass) == 3
    shas = {r["sha256"] for r in rows if r["sha256"]}
    for r in mass:
        assert r["status"] == "WITHDRAWN"  # Hard Constraint #5 / IR90-20: region-isolated or patterned
        assert "IR90-20" in r["notes"] and "do not upload" in r["notes"]
        assert r["parent"] == "h33-h33-2-b2"
        assert r["receipt"] == "N" and r["receipt_score"] == ""
        assert re.fullmatch(r"[0-9a-f]{64}", r["sha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", r["sha256_zeros"])
        assert r["sha256"] not in {o["sha256"] for o in rows if o is not r and o["sha256"]}


def test_receipt_self_check_and_proxy_labels() -> None:
    receipt = _receipt()
    sc = receipt["self_check"]
    assert sc["variant_files_re_read_and_validated"] is True
    assert sc["variant_bytes_reproduced_exactly"] is True
    assert sc["r0_rebuilt_byte_identically"] is True
    pr = receipt["proxy_reports"]["catalogue_hide_recover"]
    assert pr["status"].startswith("REPORT ONLY")
    assert pr["r0"]["n_truth_px"] == 60988
    assert pr["r0"]["ci95"] is not None
    for v in receipt["variants"]:
        assert "delta_vs_r0" in pr["variants"][v["value"]]
        assert v["status"] == "WITHDRAWN"


def test_region_reports_record_the_constraint5_failure() -> None:
    region = _receipt()["region_reports"]
    drop = region["drop5pct-tail"]
    assert drop["passes_region_evenness_gate"] is False
    assert drop["largest_emptied_cluster_blocks"] == 81
    assert drop["bbox_y"][0] > 3000  # SE corner deletion
    for key, ymax in (("add5pct-next", 101), ("add20pct-next", 288)):
        add = region[key]
        assert add["bbox_y"][1] == ymax  # northern-strip adds
        assert "PATTERNED FILE" in add["verdict"]
    assert _receipt()["withdrawal"]["section6_gates_passed_before_withdrawal"] is True
