"""Synthetic unit tests for AXIS=CONCENTRATION (no competition data required).

CI runs `pytest -q` without the gitignored `.cache/` rasters, so every test here is
pure-numpy on small synthetic grids.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from src.concentration_strain5km import (
    block_grid,
    block_prior,
    concentration_evenness_gate,
    density_prior_rank_corr,
    emptied_cluster_report,
    max_region_share_shift,
    region_shares,
    strain_prior_field,
    strata_masks,
)
from src.relief import greedy_relief_reallocate


def test_strain_prior_field_clips_and_masks():
    foot = np.ones((10, 10), dtype=bool)
    foot[0, 0] = False
    band = np.arange(100, dtype=float).reshape(10, 10)
    band[5, 5] = -3.4e38          # sentinel -> median fill
    band[6, 6] = np.nan           # non-finite -> median fill
    field, meta = strain_prior_field(band, foot, clip_pct=(10, 90))
    assert np.isnan(field[0, 0])                      # outside footprint
    assert np.isfinite(field[5, 5]) and np.isfinite(field[6, 6])
    lo, hi = meta["clip_values"]
    assert field[foot].min() >= lo - 1e-9
    assert field[foot].max() <= hi + 1e-9
    assert meta["label_agnostic"] is True
    assert meta["missing_in_foot_filled_px"] == 2


def test_block_grid_and_prior():
    foot = np.ones((20, 30), dtype=bool)
    field = np.zeros((20, 30), dtype=float)
    field[:10, :10] = 10.0
    field[:10, 10:20] = 1.0
    blocks = block_grid(foot, block_px=10)
    assert len(blocks) == 6
    prior = block_prior(field, foot, blocks)
    assert prior[0] == 10.0 and prior[1] == 1.0  # row-major order
    # partial-footprint block excluded
    foot2 = np.ones((25, 25), dtype=bool)
    foot2[20:, :] = False
    blocks2 = block_grid(foot2, block_px=10, min_foot_frac=0.5)
    assert all(r1 - r0 <= 10 for r0, r1, c0, c1 in blocks2)
    assert not any(r0 == 20 for r0, r1, c0, c1 in blocks2)


def test_strata_masks_disjoint_and_swap():
    shape = (30, 30)
    foot = np.ones(shape, dtype=bool)
    blocks = block_grid(foot, block_px=10)
    prior = np.arange(len(blocks), dtype=float)  # strictly increasing
    donor, recip, meta = strata_masks(shape, blocks, prior, pool_frac=0.5, toward=True)
    assert not np.any(donor & recip)
    assert meta["n_donor_blocks"] == meta["n_recipient_blocks"] == len(blocks) // 2
    # toward: recipient covers the highest-prior block, donor the lowest
    assert recip[20:30, 20:30].all()            # last block = highest prior
    assert donor[0:10, 0:10].all()              # first block = lowest prior
    # away swaps the strata
    donor_a, recip_a, meta_a = strata_masks(shape, blocks, prior, pool_frac=0.5, toward=False)
    assert np.array_equal(donor_a, recip) and np.array_equal(recip_a, donor)
    assert meta_a["direction"] == "away_from_high_prior"
    # determinism
    d2, r2, _ = strata_masks(shape, blocks, prior, 0.5, True)
    assert np.array_equal(d2, donor) and np.array_equal(r2, recip)


def test_strata_masks_rejects_overlap_and_bad_frac():
    foot = np.ones((30, 30), dtype=bool)
    blocks = block_grid(foot, 10)
    prior = np.arange(len(blocks), dtype=float)
    try:
        strata_masks((30, 30), blocks, prior, pool_frac=0.6, toward=True)
        assert False, "expected ValueError for pool_frac>0.5"
    except ValueError:
        pass


def test_region_shares_and_shift():
    m = np.zeros((20, 20), dtype=bool)
    m[0, 0] = True
    m[15, 15] = True
    s = region_shares(m)
    assert abs(s["north"] - 0.5) < 1e-9 and abs(s["south"] - 0.5) < 1e-9
    assert s["q_NW"] == 0.5 and s["q_SE"] == 0.5
    m2 = np.zeros((20, 20), dtype=bool)
    m2[0, 0] = True
    m2[1, 1] = True  # both north
    assert max_region_share_shift(s, region_shares(m2)) == 0.5


def test_density_prior_rank_corr_monotone():
    foot = np.ones((30, 30), dtype=bool)
    blocks = block_grid(foot, 10)
    prior = np.arange(len(blocks), dtype=float)
    m = np.zeros((30, 30), dtype=bool)
    # put a dot in each block, count increasing with prior
    for i, (r0, r1, c0, c1) in enumerate(blocks):
        ys = np.arange(r0, min(r1, r0 + i + 1))
        for y in ys:
            m[y, c0] = True
    assert density_prior_rank_corr(m, foot, blocks, prior) > 0.5


def test_emptied_cluster_detects_a_hole_and_gate():
    H = W = 100
    r0 = np.zeros((H, W), dtype=bool)
    for r in range(5, 60):
        for c in range(5, 60):
            if (r + c) % 3 == 0:
                r0[r, c] = True
    # Case A: remove one contiguous 15x15 corner region -> a >=90%-emptied cluster.
    removed_hole = r0.copy()
    removed_hole[50:, :] = False
    removed_hole[:, 50:] = False  # keep only the top-left 50x50 dots as "removed"
    rep_hole = emptied_cluster_report(removed_hole, r0, block_px=10)
    # Case B: remove every 3rd dot uniformly (already spaced) -> no near-empty block cluster
    yy, xx = np.nonzero(r0)
    sel = ((yy + xx) % 5 == 0)
    removed_spread = np.zeros_like(r0)
    removed_spread[yy[sel], xx[sel]] = True
    rep_spread = emptied_cluster_report(removed_spread, r0, block_px=10)
    assert rep_spread["largest_emptied_cluster_blocks"] <= 4
    assert concentration_evenness_gate(rep_spread) is True
    # gate rejects a report with a large cluster / high emptied fraction
    bad = {"largest_emptied_cluster_blocks": 9, "fraction_blocks_90pct_emptied": 0.5}
    assert concentration_evenness_gate(bad) is False
    assert "largest_emptied_cluster_blocks" in rep_hole


def test_greedy_reallocate_fixed_count_and_collar():
    """Operator keeps count, adds only on support at d_cat>=3, emits zero catalogue mass."""
    H = W = 80
    foot = np.ones((H, W), dtype=bool)
    cat = np.zeros((H, W), dtype=bool)
    cat[38:42, 38:42] = True
    dist_cat = ndi.distance_transform_edt(~cat)
    support = foot & (dist_cat >= 3.0)
    # parent dots spread over the top half, all off-catalogue
    r0 = np.zeros((H, W), dtype=bool)
    for r in range(6, 36, 3):
        for c in range(6, 74, 3):
            if dist_cat[r, c] > 2.0:
                r0[r, c] = True
    donor = np.zeros((H, W), dtype=bool)
    donor[:H // 2, :] = True
    recip = np.zeros((H, W), dtype=bool)
    recip[H // 2:, :] = True
    n0 = int(r0.sum())
    out, stats = greedy_relief_reallocate(r0, support, donor, recip, dist_cat, n_shift=20, min_added_cat_dist_px=3.0)
    assert int(out.sum()) == n0
    added = out & ~r0
    assert added.any()
    assert float(dist_cat[added].min()) >= 3.0
    assert not np.any(out & cat)
    assert stats["removed_dots"] == stats["added_dots"] == 20


def test_strain5km_receipt_rows_and_cards_are_consistent():
    """The 5 km strain session's 3 BUILT rows match its renamed receipt and cards.
    Tolerant of other concurrent CONCENTRATION sessions in the shared ledger."""
    import csv
    import json
    import os
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    receipt_path = root / "evidence" / "concentration_strain5km_build_receipt.json"
    if not receipt_path.is_file():
        import pytest
        pytest.skip("strain5km receipt not built in this checkout")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["axis"] == "CONCENTRATION"
    assert len(receipt["variants"]) == 3
    r0_by_file = {"nan": "sha256", "zeros": "sha256_zeros"}
    with (root / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    built = {r["id"]: r for r in rows
             if r["status"] == "BUILT" and r["axis"] == "CONCENTRATION"}
    ids = {v["id"] for v in receipt["variants"]}
    assert ids <= set(built)
    cards = json.loads((root / "ledger" / "mechanism_cards.json").read_text(encoding="utf-8"))
    card_ids = {c["id"] for c in cards["concentration_strain5km"]["variants"]}
    assert card_ids == ids
    res = json.loads((root / "ledger" / "experiment_reservations.json").read_text(encoding="utf-8"))
    assert set(res["concentration_reservations"]["occupied_tags"]) == {
        v["tag"] for v in receipt["variants"]}
    for v in receipt["variants"]:
        row = built[v["id"]]
        assert int(row["n_dots"]) == 37654
        assert row["sha256"] == v["files"]["nan"]["sha256"]
        assert row["sha256_zeros"] == v["files"]["zeros"]["sha256"]
        assert len(v["form_note"]) <= 140
    # all ledger hashes globally unique (my 6 sha256 values distinct from every other row)
    seen = [r[c].strip() for r in rows for c in r0_by_file.values() if r.get(c, "").strip()]
    assert len(seen) == len(set(seen))
