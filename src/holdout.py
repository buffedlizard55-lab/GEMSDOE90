"""Buffered whole-segment hide-and-recover holdout (the shared evaluator).

Protocol (one protocol, used by every experiment in this repository):

1. Label the catalogue raster into connected fault *segments* (8-connectivity).
2. Assign every segment to one of K folds by the 25 km spatial block that holds
   its centroid, so whole segments — never random pixels — move together and
   neighbouring segments tend to move together.
3. For fold f: hidden = all pixels of the fold's segments; visible = every other
   catalogue pixel.  Any catalogue-derived feature must be rebuilt from `visible`
   only (enforced by passing `visible` into the feature builder).
4. Scoring domain = footprint minus the *visible* fault pixels, pixel-exactly
   (this mirrors the organizer's rule that mapped fault pixels are masked out).
5. Truth for fold f = hidden pixels inside the scoring domain.  In the
   brief-literal protocol ("buffered") hidden pixels within `buffer_px` of a
   visible fault are dropped from the truth as well, so the 300 m kernel cannot
   bleed credit across the split.
6. DTI terms are pooled over folds and the ratio is taken once.

Uncertainty: spatial block bootstrap over the 25 km blocks (resample blocks with
replacement, re-pool the per-block terms, recompute the ratio).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import distance_transform_edt, label

from .metric import DTITerms, R_PX, _max_credit_field, kernel, pool

EVALUATOR_VERSION = "gems90-holdout-1.0.0"


@dataclass
class Folds:
    fold_id: np.ndarray           # int16 raster: -1 off-catalogue, else fold index
    block_id: np.ndarray          # int32 raster: 25 km block index (-1 outside footprint)
    n_folds: int
    n_segments: int
    seg_per_fold: list[int] = field(default_factory=list)
    px_per_fold: list[int] = field(default_factory=list)


def make_folds(catalogue: np.ndarray, inside: np.ndarray, n_folds: int = 5,
               block_px: int = 250, seed: int = 20261024) -> Folds:
    """Whole-segment folds grouped by 25 km (250 px) spatial blocks."""
    catalogue = np.asarray(catalogue, dtype=bool)
    lab, n_seg = label(catalogue, structure=np.ones((3, 3), dtype=int))
    h, w = catalogue.shape
    rows, cols = np.mgrid[0:h, 0:w]
    block = (rows // block_px) * (w // block_px + 1) + (cols // block_px)
    block_id = np.where(inside, block, -1).astype("int32")

    # centroid block of every segment
    idx = np.nonzero(catalogue)
    seg_of_px = lab[idx]
    blk_of_px = block[idx]
    seg_block = np.zeros(n_seg + 1, dtype="int64")
    # modal block per segment == block of the segment's first pixel is unstable;
    # use the block containing the segment centroid instead.
    sum_r = np.bincount(seg_of_px, weights=idx[0], minlength=n_seg + 1)
    sum_c = np.bincount(seg_of_px, weights=idx[1], minlength=n_seg + 1)
    cnt = np.bincount(seg_of_px, minlength=n_seg + 1).astype("float64")
    with np.errstate(invalid="ignore", divide="ignore"):
        cr = np.where(cnt > 0, sum_r / np.maximum(cnt, 1), 0).astype("int64")
        cc = np.where(cnt > 0, sum_c / np.maximum(cnt, 1), 0).astype("int64")
    seg_block = (cr // block_px) * (w // block_px + 1) + (cc // block_px)

    rng = np.random.default_rng(seed)
    uniq_blocks = np.unique(seg_block[1:]) if n_seg else np.array([], dtype="int64")
    block_fold = {int(b): int(f) for b, f in zip(uniq_blocks, rng.integers(0, n_folds, size=uniq_blocks.size))}
    seg_fold = np.full(n_seg + 1, -1, dtype="int16")
    for s in range(1, n_seg + 1):
        seg_fold[s] = block_fold.get(int(seg_block[s]), 0)

    fold_id = np.full(catalogue.shape, -1, dtype="int16")
    fold_id[idx] = seg_fold[seg_of_px]
    return Folds(
        fold_id=fold_id, block_id=block_id, n_folds=n_folds, n_segments=int(n_seg),
        seg_per_fold=[int((seg_fold[1:] == f).sum()) for f in range(n_folds)],
        px_per_fold=[int((fold_id == f).sum()) for f in range(n_folds)],
    )


def fold_masks(folds: Folds, fold: int, inside: np.ndarray, buffer_px: float = 3.0,
               buffered: bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(visible, truth, scored) rasters for one fold."""
    hidden = folds.fold_id == fold
    visible = (folds.fold_id >= 0) & ~hidden
    scored = inside & ~visible
    truth = hidden & scored
    if buffered and buffer_px > 0 and visible.any():
        d_vis = distance_transform_edt(~visible)
        truth = truth & (d_vis >= buffer_px)
    return visible, truth, scored


def block_terms(pred: np.ndarray, truth: np.ndarray, scored: np.ndarray,
                block_id: np.ndarray, k_to_truth: np.ndarray | None = None) -> dict[int, DTITerms]:
    """DTI terms split by spatial block (for the block bootstrap).

    TP/FP fields are computed globally (so kernel support crossing a block edge
    is handled exactly) and only the *attribution* of each pixel's contribution
    is split by block.  `k_to_truth` may be supplied when several predictions
    are scored against the same truth (it depends on the truth only).
    """
    pred = np.where(np.isfinite(pred) & scored, np.asarray(pred, dtype="float64"), 0.0)
    truth = np.asarray(truth, dtype=bool) & scored
    if k_to_truth is None:
        k_to_truth = kernel(distance_transform_edt(~truth)) if truth.any() else np.zeros(pred.shape)
    tp_field = _max_credit_field(pred)

    nb = int(block_id.max()) + 1
    tsel = truth
    psel = pred > 0
    tp = np.bincount(block_id[tsel], weights=tp_field[tsel], minlength=nb)
    nt = np.bincount(block_id[tsel], minlength=nb)
    fp = np.bincount(block_id[psel], weights=(pred * (1.0 - k_to_truth))[psel], minlength=nb)
    mass = np.bincount(block_id[psel], weights=pred[psel], minlength=nb)
    present = np.unique(np.concatenate([np.unique(block_id[tsel]), np.unique(block_id[psel])])) \
        if (tsel.any() or psel.any()) else np.array([], dtype=int)
    return {int(b): DTITerms(tp_w=float(tp[b]), fp_w=float(fp[b]),
                             fn_w=float(nt[b] - tp[b]), n_truth=int(nt[b]),
                             mass=float(mass[b])) for b in present}


def pooled_dti_with_ci(per_block: dict[int, DTITerms], n_boot: int = 400,
                       seed: int = 7, alpha: float = 0.05) -> dict:
    """Pooled DTI plus a spatial block bootstrap CI (blocks resampled with replacement)."""
    keys = sorted(per_block)
    terms = [per_block[k] for k in keys]
    overall = pool(terms)
    if not keys:
        return {"dti": 0.0, "ci": [0.0, 0.0], "n_truth": 0, "blocks": 0}
    rng = np.random.default_rng(seed)
    tp = np.array([t.tp_w for t in terms])
    fp = np.array([t.fp_w for t in terms])
    fn = np.array([t.fn_w for t in terms])
    nb = len(keys)
    draws = rng.integers(0, nb, size=(n_boot, nb))
    TP, FP, FN = tp[draws].sum(1), fp[draws].sum(1), fn[draws].sum(1)
    den = TP + 0.2 * FP + 0.8 * FN
    vals = np.where(den > 0, TP / np.maximum(den, 1e-12), 0.0)
    lo, hi = np.quantile(vals, [alpha / 2, 1 - alpha / 2])
    return {"dti": overall.dti, "ci": [float(lo), float(hi)],
            "tp_w": overall.tp_w, "fp_w": overall.fp_w, "fn_w": overall.fn_w,
            "n_truth": overall.n_truth, "mass": overall.mass, "blocks": nb,
            "evaluator": EVALUATOR_VERSION}


def leakage_auc(score: np.ndarray, truth: np.ndarray, scored: np.ndarray,
                max_neg: int = 400_000, seed: int = 3) -> float:
    """Single-feature ROC AUC on the holdout (leakage canary; >0.90 means leakage
    until proven otherwise).  Returns the symmetric AUC max(a, 1-a)."""
    rng = np.random.default_rng(seed)
    s = np.asarray(score, dtype="float64")
    pos = s[truth & scored]
    negmask = scored & ~truth
    neg_all = s[negmask]
    if pos.size == 0 or neg_all.size == 0:
        return float("nan")
    if neg_all.size > max_neg:
        neg_all = neg_all[rng.choice(neg_all.size, max_neg, replace=False)]
    pos = pos[np.isfinite(pos)]
    neg_all = neg_all[np.isfinite(neg_all)]
    if pos.size == 0 or neg_all.size == 0:
        return float("nan")
    allv = np.concatenate([pos, neg_all])
    order = np.argsort(allv, kind="mergesort")
    ranks = np.empty_like(order, dtype="float64")
    ranks[order] = np.arange(1, allv.size + 1)
    # average ranks for ties
    _, inv, counts = np.unique(allv, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=ranks)
    ranks = (sums / counts)[inv]
    n1, n0 = pos.size, neg_all.size
    auc = (ranks[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    return float(max(auc, 1 - auc))
