"""Exact distance-weighted Tversky index (DTI) — the official GEMS Prize metric.

Transcribed line-by-line from the DrivenData problem description for competition
#306 (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/):

    k(d)  = max(1 - d/R, 0),  R = 300 m = 3 px on the 100 m grid
    TP_w  = sum_{g in G}  max_{x : d(x,g) <= R}  p(x) k(d(x,g))
    FP_w  = sum_{x : p(x) > 0}  p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w  = sum_{g in G} [1 - max_x p(x) k(d(x,g))]
    DTI   = TP_w / (TP_w + alpha FP_w + beta FN_w + eps),  alpha = 0.2, beta = 0.8

Because FN_w = |G| - TP_w exactly, and alpha + beta = 1, the algebra collapses to

    DTI = T / (0.2 T + 0.2 (S - M) + 0.8 |G|)

with T = TP_w, S = sum_x p(x), M = sum_x p(x) max_g k(d(x,g)).  Both forms are
implemented and asserted equal in tests/test_metric_exact.py.

Distance is Euclidean in pixels (the kernel has 300 m support on a 100 m grid);
this is the single modelling assumption, flagged in IRREGULARITIES.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
R_PX = 3.0
EPS = 0.0


def kernel(dist_px: np.ndarray) -> np.ndarray:
    """Triangular kernel k(d) = max(1 - d/R, 0) for distances given in pixels."""
    return np.maximum(0.0, 1.0 - np.asarray(dist_px, dtype="float64") / R_PX)


def coverage_field(dots: np.ndarray) -> np.ndarray:
    """max_x p(x) k(d(x, .)) for binary unit-mass predictions.

    k is monotone decreasing in d, so the max over dots equals k(distance to the
    nearest dot) — exact, not an approximation.
    """
    dots = np.asarray(dots, dtype=bool)
    if not dots.any():
        return np.zeros(dots.shape, dtype="float64")
    return kernel(distance_transform_edt(~dots))


@dataclass(frozen=True)
class DTITerms:
    tp_w: float
    fp_w: float
    fn_w: float
    n_truth: int
    mass: float

    @property
    def dti(self) -> float:
        den = self.tp_w + ALPHA * self.fp_w + BETA * self.fn_w + EPS
        return float(self.tp_w / den) if den > 0 else 0.0


def dti_terms(pred: np.ndarray, truth: np.ndarray, scored: np.ndarray) -> DTITerms:
    """Pooled DTI terms for one evaluation tile.

    pred    float array of predictions in [0, 1] (non-finite treated as 0)
    truth   boolean array of ground-truth fault pixels
    scored  boolean array: pixels that participate in scoring (footprint minus
            pixel-exact masked faults)
    """
    pred = np.asarray(pred, dtype="float64")
    truth = np.asarray(truth, dtype=bool) & scored
    pred = np.where(np.isfinite(pred) & scored, pred, 0.0)

    if truth.any():
        k_to_truth = kernel(distance_transform_edt(~truth))
    else:
        k_to_truth = np.zeros(pred.shape, dtype="float64")

    # TP_w: for each truth pixel, the best (mass x kernel) over predictions.
    # Computed exactly by a max-plus sweep over the 7x7 kernel support.
    tp_field = _max_credit_field(pred)
    tp_w = float(tp_field[truth].sum())
    fp_w = float((pred * (1.0 - k_to_truth))[pred > 0].sum())
    fn_w = float(truth.sum() - tp_w)
    return DTITerms(tp_w=tp_w, fp_w=fp_w, fn_w=fn_w,
                    n_truth=int(truth.sum()), mass=float(pred.sum()))


def _max_credit_field(pred: np.ndarray) -> np.ndarray:
    """field(g) = max_x p(x) k(d(x, g)) over the 7x7 kernel support (exact)."""
    h, w = pred.shape
    out = np.zeros_like(pred)
    r = int(R_PX)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            kv = 1.0 - np.hypot(dy, dx) / R_PX
            if kv <= 0:
                continue
            ys, ye = max(0, dy), min(h, h + dy)
            xs, xe = max(0, dx), min(w, w + dx)
            if ys >= ye or xs >= xe:
                continue
            src = pred[ys - dy:ye - dy, xs - dx:xe - dx] * kv
            np.maximum(out[ys:ye, xs:xe], src, out=out[ys:ye, xs:xe])
    return out


def dti(pred: np.ndarray, truth: np.ndarray, scored: np.ndarray) -> float:
    return dti_terms(pred, truth, scored).dti


def dti_from_algebra(T: float, S: float, M: float, n_truth: float) -> float:
    """DTI = T / (0.2 T + 0.2 (S - M) + 0.8 |G|) — the collapsed identity."""
    den = ALPHA * T + ALPHA * (S - M) + BETA * n_truth
    return float(T / den) if den > 0 else 0.0


def pool(terms: list[DTITerms]) -> DTITerms:
    """Pool DTI terms across folds/tiles, then take one ratio (never averaged)."""
    return DTITerms(
        tp_w=float(sum(t.tp_w for t in terms)),
        fp_w=float(sum(t.fp_w for t in terms)),
        fn_w=float(sum(t.fn_w for t in terms)),
        n_truth=int(sum(t.n_truth for t in terms)),
        mass=float(sum(t.mass for t in terms)),
    )


def break_even_credit(theta: float) -> float:
    """Expected coverage credit a far-from-truth unit dot must bring to raise DTI.

    d/dn [ T / (0.2T + 0.2(S-M) + 0.8|G|) ] > 0  <=>  dT > 0.2 theta /(1 - 0.2 theta) * (1 - m).
    """
    return float(ALPHA * theta / (1.0 - ALPHA * theta))
