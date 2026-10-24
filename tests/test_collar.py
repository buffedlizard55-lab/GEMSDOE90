"""Unit tests for the collar/refill algebra (AXIS = PRUNE, session 2026-10-24).

Synthetic grids only: no competition raster, no truth, no leaderboard value.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.collar import (
    PER_CREDIT,
    exclusive_credit,
    prediction_scenarios,
    rebalance_quotas,
    refill_max_marginal,
    region_even_quotas,
)
from src.mass_add import block_counts, kernel_offsets


def kernel_sum() -> float:
    return float(sum(k for _, _, k in kernel_offsets(3)))


def test_exclusive_credit_of_an_isolated_dot_is_its_whole_kernel():
    mask = np.zeros((21, 21), bool)
    mask[10, 10] = True
    support = np.zeros_like(mask)
    support[7:14, 7:14] = True  # a solid 7x7 patch fully inside the R=3 kernel
    ys, xs, credit = exclusive_credit(mask, support, 3)
    assert ys.tolist() == [10] and xs.tolist() == [10]
    assert credit[0] == pytest.approx(kernel_sum(), abs=1e-6)


def test_exclusive_credit_is_max_minus_second_not_a_convolution():
    mask = np.zeros((21, 21), bool)
    mask[10, 10] = True
    mask[10, 11] = True  # 1 px apart: heavy overlap
    support = np.zeros_like(mask)
    support[7:14, 7:16] = True
    _, _, credit = exclusive_credit(mask, support, 3)
    total = float(sum(k for _, _, k in kernel_offsets(3)))
    # Neither dot owns the shared lens, so each owns strictly less than its full kernel...
    assert all(c < total for c in credit)
    # ...and the pair's *marginal* value is additive-overlap-free: much less than 2 kernels.
    # Exclusive credit is the exact T-loss of deleting one dot, so this is the correct ranking
    # quantity for a fixed-count swap and a convolution-based ranking would overstate it.
    assert credit.sum() < total


def test_region_even_quotas_is_exact_capped_and_proportional():
    parent = np.zeros((100, 300), bool)
    parent[0:10, 0:10] = True       # 100 dots in block (0, 0)
    parent[50:60, 100:110] = True   # 100 dots in block (1, 2)
    parent[90:95, 290:295] = True   # 25 dots in the last block
    q = region_even_quotas(parent, 45, block_px=50)
    assert q.sum() == 45
    counts = block_counts(parent, 50).ravel()
    assert np.all(q <= counts)
    flat = q.reshape(block_counts(parent, 50).shape)
    assert flat[0, 0] == flat[1, 2] == 20  # equal populations, equal quota
    assert flat[1, 5] == 5                 # quarter population, quarter quota
    with pytest.raises(ValueError):
        region_even_quotas(parent, 10_000, block_px=50)


def test_rebalance_quotas_moves_shortfall_and_keeps_the_total():
    quotas = np.array([5, 5, 0, 0])
    capacity = np.array([1, 2, 4, 10])
    q, moved = rebalance_quotas(quotas, capacity)
    assert q.sum() == quotas.sum()
    assert moved == 7
    assert np.all(q <= capacity)
    assert q[2] + q[3] >= 7 - 3  # the shortfall went where the pool is
    with pytest.raises(ValueError):
        rebalance_quotas(np.array([5, 5]), np.array([0, 1]))


def test_refill_is_deterministic_unique_and_quota_exact():
    support = np.zeros((60, 60), bool)
    support[5:55, 5:55] = True
    kept = np.zeros_like(support)
    kept[20, 20] = True
    pool = support & ~kept
    quotas = np.zeros(4, np.int64)
    quotas[0] = 3
    quotas[3] = 2
    ay, ax, gains = refill_max_marginal(pool, support, kept, quotas, 3, block_px=30)
    assert ay.size == 5 == quotas.sum()
    assert len({(int(y), int(x)) for y, x in zip(ay, ax)}) == 5
    assert np.all(pool[ay, ax])
    assert np.all(np.diff(gains[:3]) <= 1e-12)  # greedy: non-increasing inside a block
    ay2, ax2, gains2 = refill_max_marginal(pool, support, kept, quotas, 3, block_px=30)
    assert np.array_equal(ay, ay2) and np.array_equal(ax, ax2)
    assert np.allclose(gains, gains2)


def test_refill_prefers_uncovered_support_over_a_covered_cell():
    support = np.zeros((40, 40), bool)
    support[10:30, 5:35] = True
    kept = np.zeros_like(support)
    kept[20, 20] = True
    pool = support & ~kept
    ay, ax, gains = refill_max_marginal(pool, support, kept, np.array([1]), 3, block_px=40)
    y, x = int(ay[0]), int(ax[0])
    covered_gain = 0.0
    for dy, dx, k in kernel_offsets(3):
        yy, xx = 20 + dy, 20 + dx
        if support[yy, xx]:
            covered_gain += k
    assert gains[0] >= covered_gain - kernel_sum()  # a far corner of the rectangle wins on coverage
    assert max(abs(y - 20), abs(x - 20)) > 3


def test_prediction_scenarios_bracket_contains_the_central_estimate():
    s = prediction_scenarios(gained=3000.0, lost=500.0, per_credit=PER_CREDIT)
    assert s["uniform_truth_scenario"] == pytest.approx((3000.0 - 500.0) * PER_CREDIT, rel=1e-6)
    assert s["collar_hypothesis_scenario"] == pytest.approx(3000.0 * PER_CREDIT, rel=1e-6)
    lo, hi = s["bracket"]
    assert lo <= s["central"] <= hi
    assert lo == pytest.approx(min(s["uniform_truth_scenario"], s["collar_hypothesis_scenario"]))
    # A swap that loses more credit than it gains is negative in the conservative scenario.
    neg = prediction_scenarios(gained=100.0, lost=5000.0, per_credit=PER_CREDIT)
    assert neg["uniform_truth_scenario"] < 0 < neg["collar_hypothesis_scenario"]
