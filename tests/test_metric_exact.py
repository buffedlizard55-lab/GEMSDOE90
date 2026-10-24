"""The official DTI, checked against brute force and against its own algebra."""
import numpy as np
import pytest

from src.metric import (ALPHA, BETA, R_PX, break_even_credit, coverage_field,
                        dti_from_algebra, dti_terms, kernel, pool)


def brute_force_terms(pred, truth, scored):
    h, w = pred.shape
    pts = [(i, j) for i in range(h) for j in range(w) if scored[i, j] and pred[i, j] > 0]
    gs = [(i, j) for i in range(h) for j in range(w) if scored[i, j] and truth[i, j]]
    tp = 0.0
    for g in gs:
        best = 0.0
        for p in pts:
            d = np.hypot(p[0] - g[0], p[1] - g[1])
            if d <= R_PX:
                best = max(best, pred[p] * max(0.0, 1 - d / R_PX))
        tp += best
    fp = 0.0
    for p in pts:
        best = 0.0
        for g in gs:
            d = np.hypot(p[0] - g[0], p[1] - g[1])
            best = max(best, max(0.0, 1 - d / R_PX))
        fp += pred[p] * (1 - best)
    fn = 0.0
    for g in gs:
        best = 0.0
        for p in pts:
            d = np.hypot(p[0] - g[0], p[1] - g[1])
            best = max(best, pred[p] * max(0.0, 1 - d / R_PX))
        fn += 1 - best
    return tp, fp, fn


def test_kernel_values():
    assert kernel(0.0) == pytest.approx(1.0)
    assert kernel(1.0) == pytest.approx(2 / 3)
    assert kernel(2.0) == pytest.approx(1 / 3)
    assert kernel(3.0) == pytest.approx(0.0)
    assert kernel(4.0) == pytest.approx(0.0)


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_terms_match_brute_force(seed):
    rng = np.random.default_rng(seed)
    pred = (rng.random((14, 15)) < 0.08) * rng.random((14, 15))
    truth = rng.random((14, 15)) < 0.05
    scored = np.ones((14, 15), bool)
    scored[0, :] = False
    t = dti_terms(pred, truth, scored)
    tp, fp, fn = brute_force_terms(pred, truth, scored)
    assert t.tp_w == pytest.approx(tp, abs=1e-9)
    assert t.fp_w == pytest.approx(fp, abs=1e-9)
    assert t.fn_w == pytest.approx(fn, abs=1e-9)
    assert t.dti == pytest.approx(tp / (tp + ALPHA * fp + BETA * fn), abs=1e-12)


@pytest.mark.parametrize("seed", [10, 11, 12])
def test_algebraic_identity(seed):
    """DTI = T / (0.2T + 0.2(S - M) + 0.8|G|) must equal the three-term form."""
    rng = np.random.default_rng(seed)
    pred = (rng.random((20, 20)) < 0.1) * 1.0
    truth = rng.random((20, 20)) < 0.04
    scored = np.ones((20, 20), bool)
    t = dti_terms(pred, truth, scored)
    kd = kernel(__import__("scipy.ndimage", fromlist=["x"]).distance_transform_edt(~truth))
    M = float((pred * kd).sum())
    assert t.fn_w == pytest.approx(t.n_truth - t.tp_w, abs=1e-9)
    assert dti_from_algebra(t.tp_w, t.mass, M, t.n_truth) == pytest.approx(t.dti, abs=1e-12)


def test_coverage_field_is_max_over_dots():
    dots = np.zeros((9, 9), bool)
    dots[4, 4] = True
    dots[4, 7] = True
    c = coverage_field(dots)
    assert c[4, 4] == pytest.approx(1.0)
    assert c[4, 5] == pytest.approx(2 / 3)
    assert c[4, 6] == pytest.approx(2 / 3)   # nearer to the second dot
    assert c[0, 0] == pytest.approx(0.0)


def test_unit_mass_dominates_fractional_mass():
    """Scaling predictions up always helps: the 0.8|G| term is constant."""
    truth = np.zeros((20, 20), bool)
    truth[10, 5:15] = True
    dots = np.zeros((20, 20), float)
    dots[10, 5:15:3] = 1.0
    scored = np.ones((20, 20), bool)
    full = dti_terms(dots, truth, scored).dti
    half = dti_terms(dots * 0.5, truth, scored).dti
    assert full > half


def test_pooling_is_a_single_ratio():
    a = dti_terms(np.ones((5, 5)) * 0.0, np.zeros((5, 5), bool), np.ones((5, 5), bool))
    t = np.zeros((5, 5), bool)
    t[2, 2] = True
    p = np.zeros((5, 5))
    p[2, 2] = 1.0
    b = dti_terms(p, t, np.ones((5, 5), bool))
    pooled = pool([a, b])
    assert pooled.tp_w == pytest.approx(b.tp_w)
    assert pooled.dti == pytest.approx(b.tp_w / (b.tp_w + ALPHA * b.fp_w + BETA * b.fn_w))


def test_break_even_matches_numerical_derivative():
    """A far-from-truth dot pays iff its marginal credit exceeds 0.2t/(1-0.2t)."""
    T, S, M, G = 5000.0, 37654.0, 1800.0, 12545.0
    base = dti_from_algebra(T, S, M, G)
    be = break_even_credit(base)
    assert dti_from_algebra(T + be * 1.0001, S + 1, M, G) > base
    assert dti_from_algebra(T + be * 0.9999, S + 1, M, G) < base
    assert be == pytest.approx(ALPHA * base / (1 - ALPHA * base))
    assert ALPHA + BETA == 1.0
