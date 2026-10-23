"""DTI algebra from the brief (s2). MODEL / UNVERIFIED against official code:
the official metric code was not supplied and drivendata.org may not be fetched,
so the kernel discretisation and the max-credit definition of T below are
explicit assumptions, unit-tested for internal consistency only. Replace with
data/metric_code.py the moment the human supplies it, and re-run tests.

Brief algebra:  DTI = T / (alpha*T + alpha*(S - M) + beta*|G|), alpha=0.2, beta=0.8
  T = kernel credit, S = sum p, M = sum_p p * max_g k(p, g), triangular kernel R = 3 px.
Assumption A1: k(d) = max(0, 1 - d/3) with d = Euclidean distance in pixels.
Assumption A2: T = sum_g max_p (p * k(p, g))  (best dot covers each truth pixel).
"""
from __future__ import annotations

import numpy as np

ALPHA, BETA, R_PX = 0.2, 0.8, 3


def kernel(dist_px: np.ndarray | float) -> np.ndarray | float:
    return np.maximum(0.0, 1.0 - np.asarray(dist_px, dtype=float) / R_PX) if np.ndim(dist_px) else max(0.0, 1.0 - float(dist_px) / R_PX)


def dti_from_components(T: float, S: float, M: float, G: int, alpha: float = ALPHA, beta: float = BETA) -> float:
    den = alpha * T + alpha * (S - M) + beta * G
    return float(T / den) if den > 0 else 0.0


def marginal_gain(T: float, S: float, M: float, G: int, dT: float, dM: float, p: float = 1.0) -> float:
    """Exact DTI change from adding one dot of mass p with credit gain dT and
    max-kernel gain dM, by direct recomputation (no shortcut; brief s2)."""
    before = dti_from_components(T, S, M, G)
    after = dti_from_components(T + dT, S + p, M + p * dM, G)
    return after - before


def dot_pays(T: float, S: float, M: float, G: int, dT: float, dM: float, p: float = 1.0) -> bool:
    return marginal_gain(T, S, M, G, dT, dM, p) > 0


def components_from_arrays(p: np.ndarray, g: np.ndarray) -> tuple[float, float, float]:
    """(T, S, M) under assumptions A1/A2, computed sparsely over p's nonzero dots.
    Intended for PROXY hide-and-recover on withheld catalogue chunks, never as a gate."""
    p = np.asarray(p, dtype=float)
    truth = np.asarray(g) > 0
    S = float(p.sum())
    # M: for each dot, max kernel to any truth pixel = kernel(dist to nearest truth).
    from scipy.ndimage import distance_transform_edt

    if truth.any():
        k_at_dot = kernel(distance_transform_edt(~truth))
    else:
        return 0.0, S, 0.0
    M = float((p * k_at_dot).sum())
    # T needs max over dots of p*k per truth pixel (max-plus, not a convolution).
    # Sparse local update around each nonzero dot is exact under A2.
    credit = np.zeros_like(p)
    rows, cols = np.nonzero(p > 0)
    r = R_PX
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    kpatch = kernel(np.hypot(yy, xx))
    H, W = p.shape
    for i, j in zip(rows, cols):
        r0, r1 = max(0, i - r), min(H, i + r + 1)
        c0, c1 = max(0, j - r), min(W, j + r + 1)
        sub = kpatch[r0 - (i - r) : r0 - (i - r) + (r1 - r0), c0 - (j - r) : c0 - (j - r) + (c1 - c0)]
        credit[r0:r1, c0:c1] = np.maximum(credit[r0:r1, c0:c1], p[i, j] * sub)
    T = float(credit[truth].sum())
    return T, S, M


def dti_from_arrays(p: np.ndarray, g: np.ndarray) -> float:
    T, S, M = components_from_arrays(p, g)
    return dti_from_components(T, S, M, int((np.asarray(g) > 0).sum()))


def components_binary_exact(dots: np.ndarray, truth: np.ndarray) -> tuple[float, float, float, int]:
    """Exact (T, S, M, |G|) for a unit-mass BINARY prediction file, in O(N).

    For unit mass A2's max-plus credit collapses to the nearest-dot distance:
    T = sum_g k(dist(g, nearest dot)) and M = sum_p k(dist(p, nearest truth)).
    Both are exact distance transforms, so no per-dot loop is needed. This is the
    same algebra as `components_from_arrays`, only specialised to binary rasters;
    `tests/test_dti.py::test_binary_exact_matches_sparse_loop` pins that equality.
    """
    from scipy.ndimage import distance_transform_edt

    dots = np.asarray(dots) > 0
    truth = np.asarray(truth) > 0
    S = float(dots.sum())
    G = int(truth.sum())
    if G == 0:
        return 0.0, S, 0.0, 0
    if not dots.any():
        return 0.0, S, 0.0, G
    d_to_dot = distance_transform_edt(~dots)
    d_to_truth = distance_transform_edt(~truth)
    T = float(kernel(d_to_dot[truth]).sum())
    M = float(kernel(d_to_truth[dots]).sum())
    return T, S, M, G


def dti_binary_exact(dots: np.ndarray, truth: np.ndarray) -> float:
    T, S, M, G = components_binary_exact(dots, truth)
    return dti_from_components(T, S, M, G)
