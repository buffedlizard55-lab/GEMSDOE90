"""Synthetic unit tests and receipt/ledger integrity checks for the 2026-10-24
AXIS=RELIEF session-2 family (basin<->piedmont directed pairs).

The operator under test is the SAME pinned src.relief.greedy_relief_reallocate used by
the 2026-10-23 RELIEF family; these tests cover the new session's specs, reservation
guard, anti-isolation report and committed receipt/ledger consistency. Tests run without
the gitignored .cache data: raster-backed checks read committed JSON receipts only.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_relief_s2_variants as s2  # noqa: E402
from src.relief import greedy_relief_reallocate  # noqa: E402

R0_DOTS = 37_654


def test_specs_are_three_novel_directed_pairs_with_brief_band_doses() -> None:
    tags = tuple(s["tag"] for s in s2.VARIANT_SPECS)
    assert tags == ("p2b12p5pct", "p2b15pct", "b2p10pct")
    assert len(set(tags)) == 3
    for spec in s2.VARIANT_SPECS:
        # Fixed-count recipe shifts 10-15% of R0 mass; symmetric diff stays in 1-50%.
        assert 0.10 <= spec["mass_frac"] <= 0.15
        assert spec["n_shift"] == round(spec["mass_frac"] * R0_DOTS) or (
            spec["tag"] == "b2p10pct" and spec["n_shift"] == 3_766
        )
        sym_pct = 100.0 * 2.0 * spec["n_shift"] / R0_DOTS
        assert 1.0 <= sym_pct <= 50.0
        # Donor and recipient are distinct terciles and the moved dots stay inside them.
        assert spec["donor"] != spec["recipient"]
        assert spec["donor"] in {"basin", "piedmont", "range_front"}
        assert spec["recipient"] in {"basin", "piedmont", "range_front"}
        assert "d_cat>=3" in s2.value_string(spec)
        assert len(s2.VARIANT_SPECS) == 3


def test_no_spec_tag_collides_with_older_relief_families() -> None:
    # The session-2 rows themselves now live in the ledger; the novelty claim is that the
    # three tags do not appear on any OTHER (pre-session) RELIEF row.
    receipt_path = ROOT / "evidence" / "relief_s2_build_receipt.json"
    if not receipt_path.is_file():
        pytest.skip("RELIEF-s2 receipt not emitted in this sandbox (no .cache data)")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    own_ids = {v["id"] for v in receipt["variants"]}
    ledger = ROOT / "ledger" / "submissions.csv"
    with ledger.open(newline="", encoding="utf-8") as fh:
        older = [
            r
            for r in csv.DictReader(fh)
            if (r.get("axis") or "").upper() == "RELIEF" and r.get("id") not in own_ids
        ]
    occupied = " ".join(r.get("value", "") for r in older)
    for spec in s2.VARIANT_SPECS:
        assert spec["tag"] not in occupied


def test_reservation_guard_is_fail_closed_after_the_build() -> None:
    # Post-build the three tags ARE reserved, so re-running the builder must raise
    # (idempotent duplicate-build protection), mirroring the 2026-10-23 family guard.
    receipt_path = ROOT / "evidence" / "relief_s2_build_receipt.json"
    if not receipt_path.is_file():
        pytest.skip("RELIEF-s2 receipt not emitted in this sandbox (no .cache data)")
    with pytest.raises(ValueError, match="duplicate experiment"):
        s2.check_s2_reservations()


def test_reservation_guard_fails_on_duplicate_tag() -> None:
    # Pretend the first session-2 tag already exists in the ledger, then restore.
    ledger = ROOT / "ledger" / "submissions.csv"
    with ledger.open(newline="", encoding="utf-8") as fh:
        original = fh.read()
    tag = s2.VARIANT_SPECS[0]["tag"]
    try:
        with ledger.open("a", newline="", encoding="utf-8") as fh:
            fh.write(
                "x,GEMSDOE90,x,,,,,,,,,h33-h33-2-b2,RELIEF,"
                f"tag={tag}; duplicate probe,BUILT,N,,,,,\n"
            )
        with pytest.raises(ValueError, match="duplicate experiment"):
            s2.check_s2_reservations()
    finally:
        ledger.write_text(original, encoding="utf-8")


def test_spatial_removal_report_flags_a_contiguous_hole() -> None:
    # 20x20 parent dots on a regular 10-px lattice inside 50-px blocks (4 blocks).
    ys, xs = np.meshgrid(np.arange(5, 200, 10), np.arange(5, 200, 10), indexing="ij")
    ys, xs = ys.ravel(), xs.ravel()
    removed = np.zeros(len(ys), dtype=bool)
    # Empty every dot of the first 50-px block (25 dots) -> one 100%-emptied cluster.
    in_first = (ys < 50) & (xs < 50)
    removed[in_first] = True
    rep = s2.spatial_removal_report(ys, xs, removed, (200, 200), dose=0.1)
    assert rep["largest_emptied_cluster_blocks"] >= 1
    assert rep["fraction_blocks_90pct_emptied"] > 0.0
    # An even 10% thinning across all blocks must not open any hole.
    rng = np.random.default_rng(0)
    even = np.zeros(len(ys), dtype=bool)
    even[rng.choice(len(ys), size=len(ys) // 10, replace=False)] = True
    rep_even = s2.spatial_removal_report(ys, xs, even, (200, 200), dose=0.1)
    assert rep_even["largest_emptied_cluster_blocks"] == 0
    assert rep_even["gate_pass"]


def test_greedy_operator_synthetic_fixed_count_and_3px_collar() -> None:
    H = W = 40
    foot = np.ones((H, W), dtype=bool)
    cat = np.zeros((H, W), dtype=bool)
    cat[20, :] = True
    dist_cat = distance_transform_edt(~cat)
    donor = np.zeros((H, W), dtype=bool)
    donor[:19, :] = True
    recip = np.zeros((H, W), dtype=bool)
    recip[21:, :] = True
    support = np.zeros((H, W), dtype=bool)
    support[6, 2:38] = True       # donor ridge, far from catalogue
    support[28, 2:38] = True      # recipient ridge at d_cat=8 (eligible)
    support[22, 5:35] = True      # recipient ridge at d_cat=2 (never eligible)
    parent = np.zeros((H, W), dtype=bool)
    parent[6, 3:37:3] = True      # 12 spaced donor dots
    parent[28, 4] = True          # one pre-existing recipient dot
    n0 = int(parent.sum())
    out, stats = greedy_relief_reallocate(parent, support, donor, recip, dist_cat, n_shift=5)
    assert int(out.sum()) == n0
    assert stats["removed_dots"] == stats["added_dots"] == 5
    added = out & ~parent
    assert np.all(recip[added] & support[added])
    assert float(dist_cat[added].min()) >= 3.0
    assert not np.any(out & cat)


def test_receipt_ledger_and_cards_are_consistent_and_collision_free() -> None:
    receipt_path = ROOT / "evidence" / "relief_s2_build_receipt.json"
    if not receipt_path.is_file():
        pytest.skip("RELIEF-s2 receipt not emitted in this sandbox (no .cache data)")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["axis"] == "RELIEF"
    assert len(receipt["variants"]) == 3
    assert {v["tag"] for v in receipt["variants"]} == {"p2b12p5pct", "p2b15pct", "b2p10pct"}
    assert not receipt["proxy_reports"]["leakage_canary"]["auc_gt_0_90"]
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["sgmc_control"]["evidence_class"] == "PROXY"

    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as fh:
        ledger_rows = list(csv.DictReader(fh))
    by_id = {r["id"]: r for r in ledger_rows}
    all_hashes = [r["sha256"] for r in ledger_rows if r["sha256"]] + [
        r["sha256_zeros"] for r in ledger_rows if r["sha256_zeros"]
    ]
    assert len(all_hashes) == len(set(all_hashes)), "duplicate raster hash in ledger"

    cards = json.loads((ROOT / "ledger" / "mechanism_cards_relief_s2.json").read_text(encoding="utf-8"))
    card_ids = {c["id"] for c in cards["variants"]}
    for v in receipt["variants"]:
        row = by_id[v["id"]]
        assert row["status"] == "BUILT"
        assert row["axis"] == "RELIEF"
        assert int(row["n_dots"]) == 37_654
        assert 1.0 <= float(row["pct_changed"]) <= 50.0
        assert row["sha256"] == v["sha256"]
        assert row["sha256_zeros"] == v["sha256_zeros"]
        assert len(row["form_note"]) <= 140
        assert v["id"] in card_ids
        # Gates recorded on the re-read-from-disk audits.
        for mode in ("nan", "zeros"):
            chk = v["files"][mode]["checks"]
            assert chk["src_validate_gate_pass"]
            assert chk["zero_catalogue_mass"]
            assert chk["exact_expected_mask_after_disk_read"]
            assert chk["file_re_read_from_disk"]
        assert v["parent_diff"]["region_evenness_donor_tercile_5km"]["gate_pass"]
        assert v["parent_diff"]["region_evenness_all_blocks_5km"]["largest_emptied_cluster_blocks"] <= 4
        assert v["prediction_frozen_before_proxies"] is True
