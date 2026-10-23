"""Unit tests for the coverage-infill (MASS add-direction) machinery."""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import ndimage as ndi

from src import reach


def test_kernel_offsets_match_triangular_definition():
    offs, credits = reach.kernel_offsets(3.0)
    d = np.hypot(offs[:, 0], offs[:, 1])
    assert np.all(d > 0) and np.all(d < 3.0)
    assert np.allclose(credits, 1.0 - d / 3.0)
    # Whole pixels strictly inside a radius-3 disk, excluding the centre: 24.
    assert len(offs) == 24
    assert credits.max() == pytest.approx(2.0 / 3.0)  # nearest neighbour is 1 px away


def test_credit_map_equals_bruteforce_max_over_dots():
    rng = np.random.default_rng(0)
    dots = np.zeros((21, 21), dtype=bool)
    idx = rng.choice(21 * 21, size=6, replace=False)
    dots.flat[idx] = True
    credit = reach.credit_map(dots, 3.0)
    ys, xs = np.nonzero(dots)
    brute = np.zeros((21, 21))
    for y in range(21):
        for x in range(21):
            d = np.min(np.hypot(ys - y, xs - x))
            brute[y, x] = max(0.0, 1.0 - d / 3.0)
    assert np.allclose(credit, brute, atol=1e-6)


def test_gain_field_equals_bruteforce_marginal_credit():
    rng = np.random.default_rng(1)
    dots = np.zeros((25, 25), dtype=bool)
    dots[rng.choice(625, size=8, replace=False).reshape(-1) // 25,
         rng.choice(625, size=8, replace=False) % 25] = True
    credit = reach.credit_map(dots, 3.0)
    pool = np.zeros((25, 25), dtype=bool)
    pool[3:22, 3:22] = True
    gain = reach.gain_field(pool, credit, 3.0)
    for (qy, qx) in [(5, 5), (12, 12), (20, 4)]:
        tot = 0.0
        for y in range(25):
            for x in range(25):
                d = math.hypot(qy - y, qx - x)
                if 0 < d < 3.0:
                    tot += max(0.0, (1.0 - d / 3.0) - credit[y, x])
        assert gain[qy, qx] == pytest.approx(tot, abs=1e-5)
    assert gain[~pool].sum() == 0


def test_proportional_quotas_exact_sum_and_cap():
    w = np.array([10.0, 30.0, 60.0])
    q = reach.proportional_quotas(w, 7)
    assert q.sum() == 7
    assert list(q) == [1, 2, 4]  # largest remainder
    assert reach.proportional_quotas(np.array([5.0, 0.0]), 5).tolist() == [5, 0]


def test_infill_select_count_determinism_and_pool_discipline():
    dots = np.zeros((120, 120), dtype=bool)
    dots[10:110:3, 10:110] = True
    pool = np.zeros((120, 120), dtype=bool)
    pool[9:112, 9:112] = True
    pool &= ~dots
    a = reach.infill_select(pool, dots, n_total=200, block_px=50)
    b = reach.infill_select(pool, dots, n_total=200, block_px=50)
    assert int(a["selected"].sum()) == 200
    assert np.array_equal(a["selected"], b["selected"])          # deterministic
    assert not np.any(a["selected"] & dots)                      # no double mass
    assert not np.any(a["selected"] & ~pool)                     # only eligible cells
    # Marginal gains are positive and bounded by the isolated-dot patch credit.
    assert np.all(a["gains"] > 0)
    assert np.all(a["gains"] < 25.0)
    # Quotas are honoured when the pool allows it
    assert np.array_equal(a["quota"], b["quota"])
    assert int((a["block_counts_add"] > a["quota"]).sum()) == 0


def test_infill_leaves_unoccupied_blocks_empty():
    dots = np.zeros((100, 100), dtype=bool)
    dots[0:50:4, 0:50:4] = True
    pool = np.ones((100, 100), dtype=bool) & ~dots
    res = reach.infill_select(pool, dots, n_total=40, block_px=50)
    assert int(res["selected"].sum()) == 40
    assert res["selected"][50:, 50:].sum() == 0
    assert res["selected"][50:, 0:50].sum() == 0


def test_density_cv_and_contiguous():
    counts = np.array([0, 4, 4, 4, 4])
    assert reach.density_cv(counts) == pytest.approx(0.0)
    block = np.zeros((3, 3), dtype=bool)
    block[0, 0] = block[0, 1] = block[1, 1] = True
    assert reach.largest_contiguous(block) == 3
    assert reach.largest_contiguous(np.zeros((2, 2), dtype=bool)) == 0


def test_truth_free_add_delta_sign_and_monotonicity():
    kwargs = dict(n_parent=37_654, dti=0.2778, support_px=121_131, truth_px=55_000)
    small = reach.truth_free_add_delta(gain_sum=1_000, n_add=1_000, **kwargs)
    large = reach.truth_free_add_delta(gain_sum=3_000, n_add=3_000, **kwargs)
    assert small > 0 and large > small
    # Zero measured credit gain can only lose: mass is added, nothing is covered.
    assert reach.truth_free_add_delta(gain_sum=0.0, n_add=1_000, **kwargs) < 0
