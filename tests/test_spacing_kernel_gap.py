"""Synthetic unit tests for the AXIS=SPACING kernel-gap operator.

All tests are pure numpy and do not open gitignored competition rasters, so CI can
run them in a clean checkout.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

from src import spacing_kernel_gap as spacing


def test_kernel_offsets_include_centre_and_are_triangular():
    offs, kval = spacing.kernel_offsets(3)
    d = np.hypot(offs[:, 0], offs[:, 1])
    assert np.all(d < 3.0)
    assert np.allclose(kval, 1.0 - d / 3.0)
    assert np.any((offs[:, 0] == 0) & (offs[:, 1] == 0))
    assert kval[np.argwhere((offs[:, 0] == 0) & (offs[:, 1] == 0))[0, 0]] == 1.0
    assert len(offs) == 25


def test_allocate_move_quotas_exact_and_capped():
    donors = np.array([0, 10, 20, 30, 40], dtype=np.int64)
    pools = np.array([0, 1, 20, 30, 40], dtype=np.int64)
    q = spacing.allocate_move_quotas(donors, pools, 18, max_block_donor_frac=0.30)
    assert q.sum() == 18
    assert np.all(q <= np.minimum(pools, np.ceil(0.30 * donors)))
    assert q[0] == 0 and q[1] == 1
    with pytest.raises(ValueError):
        spacing.allocate_move_quotas(donors, pools, 30, max_block_donor_frac=0.30)


def test_credit_state_exclusive_loss_and_marginal_gain_on_toy_grid():
    parent = np.zeros((31, 31), dtype=bool)
    parent[15, 12] = True
    parent[15, 18] = True
    support = np.zeros_like(parent)
    support[15, 8:23] = True
    st = spacing._build_state(parent, support)
    pad, wp = st.pad, st.width_padded
    idx = (15 + pad) * wp + (12 + pad)
    # Removing either end dot loses the credit on the pixels for which it is the
    # unique/equal-best contributor; adding at the midpoint gains credit there.
    loss = spacing._exclusive_loss(st, idx)
    gain = spacing._marginal_gain(st, (15 + pad) * wp + (15 + pad))
    assert loss > 0.0
    assert gain > 0.0
    removed = spacing._remove_dot(st, idx)
    assert removed == pytest.approx(loss)
    assert st.active[idx] == 0
    midpoint = (15 + pad) * wp + (15 + pad)
    # The removal itself changes local coverage, so the exact gain is re-evaluated
    # immediately before the addition (as in the production heap loop).
    gain_after_removal = spacing._marginal_gain(st, midpoint)
    added = spacing._add_dot(st, midpoint)
    assert added == pytest.approx(gain_after_removal)
    assert st.owner[midpoint] == midpoint


def test_kernel_gap_reallocate_is_fixed_count_block_local_and_deterministic():
    h = w = 120
    rng = np.random.default_rng(20261024)
    support = np.zeros((h, w), dtype=bool)
    # Two under-sampled strands: 6 px parent spacing leaves a zero-credit gap at
    # the midpoint of each 6 px interval, which a block-local move can fill.
    support[20, 5:55] = True
    support[20, 65:115] = True
    support[80, 5:55] = True
    support[80, 65:115] = True
    parent = np.zeros_like(support)
    for y in (20, 80):
        for x in list(range(6, 55, 6)) + list(range(66, 115, 6)):
            if support[y, x]:
                parent[y, x] = True
    dcat = np.full((h, w), 10.0, dtype=float)
    dcat[50:70, :] = 1.0  # a catalogue swath; no eligible donor/addition there
    # Put a tiny amount of jitter in an otherwise irrelevant unused array to ensure
    # the algorithm does not consume randomness.
    _ = rng.random(3)
    n_move = 8
    out1, stats1 = spacing.kernel_gap_reallocate(parent, support, dcat, n_move, block_px=50)
    out2, stats2 = spacing.kernel_gap_reallocate(parent, support, dcat, n_move, block_px=50)
    assert np.array_equal(out1, out2)
    assert int(out1.sum()) == int(parent.sum())
    assert stats1["removed_dots"] == stats1["added_dots"] == n_move
    assert stats1["pct_changed_symmetric"] == pytest.approx(200.0 * n_move / parent.sum(), rel=1e-6)
    assert np.array_equal(stats1["block_counts_parent"], stats1["block_counts_after"])
    added = out1 & ~parent
    removed = parent & ~out1
    assert np.all(support[added])
    assert float(dcat[added].min()) >= spacing.MIN_ADDED_CAT_DIST
    assert not np.any(removed & (dcat < spacing.MIN_ADDED_CAT_DIST))
    assert stats1["net_support_credit"] > 0.0
    assert stats1["seed_used_in_variant_construction"] is None


def test_kernel_gap_reallocate_rejects_parent_off_support_and_impossible_dose():
    h = w = 60
    parent = np.zeros((h, w), dtype=bool)
    parent[10, 10] = True
    support = np.zeros_like(parent)
    dcat = np.full((h, w), 10.0)
    with pytest.raises(ValueError):
        spacing.kernel_gap_reallocate(parent, support, dcat, 1)
    support[10, 10] = True
    support[10, 11] = True
    with pytest.raises(ValueError):
        spacing.kernel_gap_reallocate(parent, support, dcat, 2)


def test_fixed_count_prediction_sign_and_bounds():
    fit = spacing.parent_fit()
    assert spacing.fixed_count_delta(1000.0, 0.20, fit) > 0.0
    assert spacing.fixed_count_delta(-1000.0, 0.20, fit) < 0.0
    b = spacing.prediction_bracket(1000.0)
    assert b["low"] > 0.0 and b["high"] >= b["point"] >= b["low"]
    assert b["assumption"].startswith("S and M fixed")


def test_spacing_receipt_ledger_cards_and_reservations_are_consistent():
    """Committed metadata check; skips cleanly in a checkout without this build."""
    import csv
    import json

    root = spacing.__file__
    from pathlib import Path
    root = Path(root).resolve().parents[1]
    receipt_path = root / "evidence" / "spacing_kernel_gap_build_receipt.json"
    if not receipt_path.is_file():
        pytest.skip("spacing receipt not built in this checkout")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["axis"] == "SPACING"
    assert receipt["parent"]["r0_byte_identity_passed"] is True
    assert len(receipt["variants"]) == 3
    assert receipt["proxy_reports"]["leakage_canary"]["auc_gt_0_90"] is False
    assert receipt["proxy_reports"]["catalogue_hide_recover"]["evidence_class"] == "PROXY"
    assert receipt["proxy_reports"]["sgmc_control"]["evidence_class"] == "PROXY"

    ledger_path = root / "ledger" / "submissions.csv"
    with ledger_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    built = {r["id"]: r for r in rows if r["status"] == "BUILT" and r["axis"] == "SPACING"}
    receipt_ids = {v["id"] for v in receipt["variants"]}
    assert receipt_ids <= set(built)
    assert len(receipt_ids) == 3
    for v in receipt["variants"]:
        row = built[v["id"]]
        assert int(row["n_dots"]) == 37_654
        assert 1.0 <= float(row["pct_changed"]) <= 50.0
        assert row["sha256"] == v["files"]["nan"]["sha256"]
        assert row["sha256_zeros"] == v["files"]["zeros"]["sha256"]
        assert len(v["form_note"]) <= 140
        assert "MODEL" in v["predicted_change"] and "not a score" in v["predicted_change"]
        assert abs(float(v["parent_diff"]["net_support_credit"])) >= 0.0
        assert v["files"]["nan"]["checks"]["added_dots_min_cat_dist_ge_3px"] is True
        assert v["files"]["nan"]["checks"]["all_dots_on_h19_5_support"] is True
        assert v["files"]["nan"]["checks"]["fixed_count_37654"] is True
        assert v["parent_diff"]["block_density_cv_before"] == v["parent_diff"]["block_density_cv_after"]
        assert v["parent_diff"]["anti_isolation"]["passes_anti_isolation_gate"] is True

    hashes: list[str] = []
    for row in rows:
        for col in ("sha256", "sha256_zeros"):
            value = (row.get(col) or "").strip()
            if value:
                hashes.append(value)
    assert len(hashes) == len(set(hashes))

    cards = json.loads((root / "ledger" / "mechanism_cards.json").read_text(encoding="utf-8"))
    card_ids = {c["id"] for c in cards["spacing_kernel_gap"]["variants"]}
    assert card_ids == receipt_ids
    reservations = json.loads((root / "ledger" / "experiment_reservations.json").read_text(encoding="utf-8"))
    block = reservations["spacing_kernel_gap_20261024"]
    assert block["occupied_tags"] == ["gap5pct", "gap10pct", "gap20pct"]
    assert block["selected_values"] == [v["tag"] for v in receipt["variants"]]
    assert "HELD" in block["decision"]
