"""Unit tests for the AXIS=MASS add operator (region-even block-budgeted additions)."""
from __future__ import annotations

import numpy as np
import pytest

from src import mass_add


def test_block_counts_matches_manual_sum():
    mask = np.zeros((12, 9), dtype=bool)
    mask[0:3, 0:4] = True
    mask[7, 8] = True
    counts = mass_add.block_counts(mask, block_px=5)
    # 3 block rows (12/5 -> 3), 2 block cols (9/5 -> 2)
    assert counts.shape == (3, 2)
    assert counts.sum() == int(mask.sum())
    assert counts[0, 0] == 12 and counts[1, 1] == 1 and counts[0, 1] == 0


def test_allocate_quotas_exact_and_capped():
    counts = np.array([100, 40, 4, 0, 60], dtype=np.int64)
    capacity = np.abs(np.array([[500], [500], [500], [500], [500]], dtype=np.int64)).ravel()
    q = mass_add.allocate_quotas(counts, capacity, n_add=41, cap_frac=0.5)
    assert q.sum() == 41
    assert q[3] == 0, "a block with zero parent dots must receive nothing"
    assert q[2] <= 2, "cap is floor(0.5 * 4)"
    assert np.all(q <= np.floor(0.5 * counts))


def test_allocate_quotas_respects_capacity_and_fails_closed():
    counts = np.array([10, 10], dtype=np.int64)
    capacity = np.array([1, 1], dtype=np.int64)
    with pytest.raises(ValueError):
        mass_add.allocate_quotas(counts, capacity, n_add=5)


def test_allocate_quotas_is_deterministic():
    counts = np.array([7, 3, 11, 2], dtype=np.int64)
    capacity = np.full(4, 50, dtype=np.int64)
    a = mass_add.allocate_quotas(counts, capacity, n_add=9)
    b = mass_add.allocate_quotas(counts, capacity, n_add=9)
    assert np.array_equal(a, b)


def test_fifo_pick_respects_per_block_quota():
    shape = (10, 10)
    elig = np.zeros(shape, dtype=bool)
    elig[0:2, 0:2] = True  # block (0,0): 4 cells
    elig[6:8, 6:8] = True  # block (1,1): 4 cells
    rank = np.arange(shape[0] * shape[1], dtype=float).reshape(shape)
    quotas = np.zeros((2, 2), dtype=np.int64)
    quotas[0, 0] = 1
    quotas[1, 1] = 2
    ys, xs = mass_add.fifo_pick_within_blocks(elig, rank, quotas, block_px=5)
    assert ys.size == 3
    in_block00 = ((ys // 5) * 2 + (xs // 5) == 0).sum()
    in_block11 = ((ys // 5) * 2 + (xs // 5) == 3).sum()
    assert in_block00 == 1 and in_block11 == 2
    # lowest rank in each block is the top-left cell
    assert (0, 0) in set(zip(ys.tolist(), xs.tolist()))


def test_gapmax_prefers_the_largest_gap():
    shape = (7, 15)
    support = np.zeros(shape, dtype=bool)
    support[3, :] = True  # a 1-px ridge
    dots = np.zeros(shape, dtype=bool)
    dots[3, 0] = True
    dots[3, 3] = True
    dots[3, 12] = True
    elig = support & ~dots
    quotas = np.zeros((1, 1), dtype=np.int64)
    quotas[0, 0] = 1
    ys, xs, gains = mass_add.gapmax_pick_within_blocks(elig, support, dots, quotas, block_px=50)
    assert ys.size == 1 and ys[0] == 3
    # the widest gap is between x=3 and x=12 -> midpoint-ish, not next to a dot
    assert 6 <= xs[0] <= 9
    assert gains[0] > 1.0


def test_coverage_matches_isolated_kernel_sum():
    shape = (9, 9)
    support = np.ones(shape, dtype=bool)
    dots = np.zeros(shape, dtype=bool)
    dots[4, 4] = True
    cov = mass_add.coverage(dots, support)
    expected = sum(k for _dy, _dx, k in mass_add.kernel_offsets(3))
    assert cov[4, 4] == pytest.approx(1.0)
    assert cov.sum() == pytest.approx(expected)


def test_parent_fit_reproduces_claimed_dti():
    fit = mass_add.parent_fit(0.2778, 37654, 65000, 0.44)
    assert fit["T"] / fit["D"] == pytest.approx(0.2778, abs=1e-9)


def test_addition_pays_only_above_the_threshold():
    fit = mass_add.parent_fit(0.2778, 37654, 65000, 0.44)
    # c = 0, so the break-even exclusive credit is 0.2T/(D-0.2T)
    break_even = 0.2 * fit["T"] / (fit["D"] - 0.2 * fit["T"])
    below = mass_add.predicted_add_delta(np.array([break_even * 0.5]), np.zeros(1), 1.0, fit)
    above = mass_add.predicted_add_delta(np.array([break_even * 2.0]), np.zeros(1), 1.0, fit)
    assert below < 0 < above
    assert break_even == pytest.approx(0.056, abs=0.005)


def test_addition_evenness_gate_accepts_scaled_copy_and_rejects_islands():
    good = {
        "nominal_dose": 0.10,
        "add_share_p05": 0.05,
        "add_share_p95": 0.15,
        "add_share_max": 0.20,
        "adds_into_blocks_with_zero_parent_dots": 0,
        "blocks_with_zero_additions_among_20plus": 10,
        "blocks_with_20plus_dots": 500,
    }
    assert mass_add.addition_evenness_gate(good)
    island = dict(good, add_share_p05=0.0, add_share_max=3.0, adds_into_blocks_with_zero_parent_dots=900)
    assert not mass_add.addition_evenness_gate(island)


def test_addition_report_counts_are_consistent():
    rng = np.random.default_rng(7)
    parent = rng.random((60, 60)) < 0.02
    added = rng.random((60, 60)) < 0.004
    rep = mass_add.addition_report(added, parent, block_px=20)
    assert rep["blocks_with_parent_dots"] > 0
    assert rep["add_share_max"] >= rep["add_share_median"]
    assert rep["nominal_dose"] == pytest.approx(added.sum() / parent.sum(), abs=1e-6)
