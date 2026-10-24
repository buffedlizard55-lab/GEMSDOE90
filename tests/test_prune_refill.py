"""Unit tests for the credit-aware fixed-count refill (src/prune_refill.py).

Synthetic, deterministic, no competition data. The refill is the metric's own marginal
rule evaluated truth-free on a proxy support, so the tests check geometry and determinism
only -- never a score.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.prune_refill import (
    credit_aware_refill,
    kernel_offsets,
    marginal_gain_field,
    support_credit,
)


def test_kernel_offsets_exclude_centre_and_match_triangle():
    offs, credits = kernel_offsets(3.0)
    assert (0, 0) not in set(map(tuple, offs.tolist()))
    assert offs.shape[0] == credits.shape[0]
    for (dy, dx), k in zip(offs.tolist(), credits.tolist()):
        d = np.hypot(dy, dx)
        assert 0.0 < d < 3.0
        assert k == pytest.approx(1.0 - d / 3.0)


def test_support_credit_single_dot():
    dot = np.zeros((9, 9), dtype=bool)
    dot[4, 4] = True
    support = np.ones((9, 9), dtype=bool)
    c = support_credit(dot, support, 3.0)
    assert c[4, 4] == pytest.approx(1.0)
    assert c[5, 4] == pytest.approx(1.0 - 1.0 / 3.0)
    assert c[4, 7] == pytest.approx(1.0 - 3.0 / 3.0)
    assert c[4, 8] == 0.0
    # outside the support the credit is forced to zero
    sup2 = np.ones((9, 9), dtype=bool)
    sup2[4, 5] = False
    c2 = support_credit(dot, sup2, 3.0)
    assert c2[4, 5] == 0.0


def test_marginal_gain_empty_kept_equals_own_disk_credit():
    support = np.ones((11, 11), dtype=bool)
    kept = np.zeros((11, 11), dtype=bool)
    pool = support.copy()
    gain = marginal_gain_field(pool, support_credit(kept, support), support, 3.0)
    # an isolated new dot covers its whole triangular disk: the discrete sum of k over the
    # 24 offsets plus its own pixel credit (the continuous analogue is pi R^2 / 3)
    offs, credits = kernel_offsets(3.0)
    assert gain[5, 5] == pytest.approx(float(credits.sum()) + 1.0, rel=1e-5)


def test_refill_prefers_the_uncovered_gap():
    # A support bar with a hole: the hole's pixels carry no credit, so a new dot there
    # supplies strictly more marginal credit than a dot on already-covered ground.
    support = np.zeros((15, 15), dtype=bool)
    support[7, :] = True
    kept = np.zeros((15, 15), dtype=bool)
    kept[7, 2] = True
    kept[7, 12] = True
    pool = support & ~kept
    fill = credit_aware_refill(pool, kept, support, n_refill=1, radius=3.0)
    # the best pixel is any ground at least one kernel radius from both seeds (credit 0),
    # i.e. the middle of the gap -- never an already-covered pixel next to a seed
    assert int(fill.sum()) == 1
    rows, cols = np.nonzero(fill)
    assert rows[0] == 7
    assert 5 <= cols[0] <= 9
    assert abs(int(cols[0]) - 2) >= 3 and abs(int(cols[0]) - 12) >= 3


def test_refill_is_deterministic_and_respects_pool():
    rng = np.random.default_rng(0)
    support = rng.random((40, 40)) > 0.6
    kept = rng.random((40, 40)) > 0.9
    pool = support & ~kept
    n = 12
    a = credit_aware_refill(pool, kept, support, n_refill=n, radius=3.0)
    b = credit_aware_refill(pool, kept, support, n_refill=n, radius=3.0)
    assert np.array_equal(a, b)
    assert int(a.sum()) == n
    assert not np.any(a & ~pool)
    assert not np.any(a & kept)


def test_refill_rejects_oversized_request():
    support = np.ones((10, 10), dtype=bool)
    pool = support.copy()
    with pytest.raises(ValueError):
        credit_aware_refill(pool, np.zeros_like(support, dtype=bool), support, n_refill=500)


def test_refill_zero_request_is_empty():
    support = np.ones((10, 10), dtype=bool)
    out = credit_aware_refill(support, np.zeros_like(support, dtype=bool), support, n_refill=0)
    assert not out.any()
