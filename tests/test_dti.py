"""Unit tests for the brief's DTI algebra (internal consistency; official code UNVERIFIED)."""
import numpy as np
import pytest

from src.dti import (
    components_from_arrays,
    dot_pays,
    dti_from_arrays,
    dti_from_components,
    kernel,
    marginal_gain,
)


def test_kernel_triangular():
    assert kernel(0) == 1.0
    assert kernel(3) == 0.0
    assert kernel(1.5) == pytest.approx(0.5)
    assert kernel(10) == 0.0


def test_algebra_isolated_truth():
    # Dot exactly on the only truth pixel: T=S=M=1, G=1 -> 1/(0.2+0+0.8)=1
    assert dti_from_components(1, 1, 1, 1) == pytest.approx(1.0)
    # Dot far away: no credit
    assert dti_from_components(0, 1, 0, 1) == 0.0
    # Half credit: 0.5/(0.1+0.1+0.8)=0.5
    assert dti_from_components(0.5, 1, 0.5, 1) == pytest.approx(0.5)
    assert dti_from_components(0, 0, 0, 0) == 0.0


def test_marginal_matches_brute_force_and_shortcut_scale():
    # Incumbent-scale state: pick T,S,M,G giving DTI ~= 0.2778 (CLAIM scale only)
    G = 50_000
    T, S, M = 13_900.0, 37_654.0, 12_000.0
    base = dti_from_components(T, S, M, G)
    assert 0.20 < base < 0.35
    # A dot earning no credit must hurt; a perfect new dot on uncovered truth must help.
    assert marginal_gain(T, S, M, G, dT=0.0, dM=0.0) < 0
    assert marginal_gain(T, S, M, G, dT=1.0, dM=1.0) > 0
    # Brief shortcut: break-even credit ~0.2*DTI for an isolated truth pixel (dT=dM=k).
    ks = np.linspace(0, 1, 2001)
    breakeven = next(k for k in ks if dot_pays(T, S, M, G, dT=float(k), dM=float(k)))
    assert breakeven == pytest.approx(0.2 * base, rel=0.15)


def test_components_from_arrays():
    p = np.zeros((21, 21), dtype=float)
    g = np.zeros((21, 21), dtype=int)
    g[10, 10] = 1
    p[10, 10] = 1.0
    T, S, M = components_from_arrays(p, g)
    assert (T, S, M) == pytest.approx((1.0, 1.0, 1.0))
    assert dti_from_arrays(p, g) == pytest.approx(1.0)

    p2 = np.zeros_like(p)
    p2[10, 13] = 1.0  # distance 3 -> kernel 0 under A1
    T, S, M = components_from_arrays(p2, g)
    assert (T, S, M) == pytest.approx((0.0, 1.0, 0.0))

    p3 = np.zeros_like(p)
    p3[10, 11] = 1.0  # distance 1 -> k = 2/3
    T, S, M = components_from_arrays(p3, g)
    assert T == pytest.approx(2 / 3)
    assert M == pytest.approx(2 / 3)


def test_extra_dot_on_covered_truth_does_not_double_count_T():
    p = np.zeros((21, 21), dtype=float)
    g = np.zeros((21, 21), dtype=int)
    g[10, 10] = 1
    p[10, 10] = 1.0
    p[10, 11] = 1.0
    T, S, M = components_from_arrays(p, g)
    assert T == pytest.approx(1.0)  # max-credit, not summed
    assert S == 2.0


def test_binary_exact_matches_sparse_loop() -> None:
    """The O(N) distance-transform form must equal the per-dot max-plus loop."""
    import numpy as np

    from src import dti

    rng = np.random.default_rng(20261023)
    for _ in range(3):
        dots = rng.random((48, 61)) < 0.025
        truth = rng.random((48, 61)) < 0.035
        # Same algebra, different summation order: equal to float64 rounding, not bitwise.
        assert dti.dti_binary_exact(dots, truth) == pytest.approx(
            dti.dti_from_arrays(dots.astype(float), truth.astype(int)), rel=1e-12, abs=1e-15
        )


def test_binary_exact_empty_and_full_edge_cases() -> None:
    import numpy as np

    from src import dti

    empty = np.zeros((10, 10), dtype=bool)
    some = np.zeros((10, 10), dtype=bool)
    some[5, 5] = True
    assert dti.dti_binary_exact(empty, some) == 0.0
    # A dot exactly on the only truth pixel: T=1, S=1, M=1, |G|=1 -> 1/(0.2+0+0.8)=1
    assert dti.dti_binary_exact(some, some) == 1.0
