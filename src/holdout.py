"""Spatially-blocked hide-and-recover holdout for the 2026-10-24 lane (H1).

Protocol (parallel-run brief): withhold whole fault regions in spatial blocks
with a buffer, derive every catalogue-based quantity only from the visible
faults, mask visible faults pixel-exactly, and score *pooled* DTI
(alpha=0.2, beta=0.8, triangular R=3 px kernel) using the algebra in
``src/dti.py`` (assumptions A1/A2 there; UNVERIFIED against official code,
which was never supplied -- every number from this module is HOLDOUT-DTI,
never an organizer score).

Fast exactness note: for binary unit-mass dots the max-credit definition
collapses to nearest-neighbour distances, because max_p k(p,g) =
k(min_p dist(p,g)) for the decreasing triangular kernel.  Hence
T = sum_g k(dist(g, nearest dot)) and M = sum_p k(dist(p, nearest truth)),
computed with two EDTs.  ``tests/test_holdout90.py`` pins this identity
against the reference ``src.dti.components_from_arrays`` on random arrays.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata

from src.dti import ALPHA, BETA, R_PX, dti_from_components, kernel


def binary_components(dots: np.ndarray, truth: np.ndarray) -> tuple[float, float, float, int]:
    """(T, S, M, G) for binary unit-mass ``dots`` scored on binary ``truth``."""
    dots = np.asarray(dots, dtype=bool)
    truth = np.asarray(truth, dtype=bool)
    S = float(dots.sum())
    G = int(truth.sum())
    if G == 0 or S == 0:
        return 0.0, S, 0.0, G
    dist_to_dot = ndi.distance_transform_edt(~dots)
    T = float(kernel(dist_to_dot[truth]).sum())
    dist_to_truth = ndi.distance_transform_edt(~truth)
    M = float(kernel(dist_to_truth[dots]).sum())
    return T, S, M, G


def block_components(
    dots: np.ndarray, truth: np.ndarray, block_id: np.ndarray
) -> dict[str, np.ndarray]:
    """Per-block (T, S, M, G); credit is attributed to the truth/dot pixel's block.

    Cross-block kernel credit (a dot within 3 px outside a block) still counts,
    exactly as in the pooled score; only the bookkeeping is per-block, which is
    what the block bootstrap needs.
    """
    dots = np.asarray(dots, dtype=bool)
    truth = np.asarray(truth, dtype=bool)
    n_blocks = int(block_id.max()) + 1
    T = np.zeros(n_blocks)
    S = np.zeros(n_blocks)
    M = np.zeros(n_blocks)
    G = np.zeros(n_blocks)
    if truth.any() and dots.any():
        dist_to_dot = ndi.distance_transform_edt(~dots)
        np.add.at(T, block_id[truth], kernel(dist_to_dot[truth]))
        dist_to_truth = ndi.distance_transform_edt(~truth)
        np.add.at(M, block_id[dots], kernel(dist_to_truth[dots]))
    np.add.at(S, block_id[dots], 1.0)
    np.add.at(G, block_id[truth], 1.0)
    return {"T": T, "S": S, "M": M, "G": G}


def pooled_dti(comp: dict[str, np.ndarray], alpha: float = ALPHA, beta: float = BETA) -> float:
    return dti_from_components(
        float(comp["T"].sum()), float(comp["S"].sum()), float(comp["M"].sum()), int(comp["G"].sum()),
        alpha=alpha, beta=beta,
    )


def block_bootstrap_ci(
    comp: dict[str, np.ndarray], n_boot: int = 2000, seed: int = 20261024
) -> tuple[float, float, float]:
    """(point, lo95, hi95) resampling whole blocks that contain truth or dots."""
    rng = np.random.default_rng(seed)
    live = np.nonzero((comp["G"] > 0) | (comp["S"] > 0))[0]
    if live.size == 0:
        return 0.0, 0.0, 0.0
    T, S, M, G = (comp[k][live] for k in ("T", "S", "M", "G"))
    point = pooled_dti(comp)
    idx = rng.integers(0, live.size, size=(n_boot, live.size))
    boots = []
    for row in idx:
        boots.append(dti_from_components(T[row].sum(), S[row].sum(), M[row].sum(), int(G[row].sum())))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def paired_block_bootstrap(
    comp_a: dict[str, np.ndarray],
    comp_b: dict[str, np.ndarray],
    n_boot: int = 2000,
    seed: int = 20261024,
) -> tuple[float, float, float]:
    """(DTI_B - DTI_A point, lo95, hi95) with the same blocks resampled for both arms."""
    rng = np.random.default_rng(seed)
    live = np.nonzero(
        (comp_a["G"] > 0) | (comp_b["G"] > 0) | (comp_a["S"] > 0) | (comp_b["S"] > 0)
    )[0]
    point = pooled_dti(comp_b) - pooled_dti(comp_a)
    if live.size == 0:
        return 0.0, 0.0, 0.0

    def subset(comp, row):
        return dti_from_components(
            comp["T"][live][row].sum(), comp["S"][live][row].sum(),
            comp["M"][live][row].sum(), int(comp["G"][live][row].sum()),
        )

    idx = rng.integers(0, live.size, size=(n_boot, live.size))
    diffs = [subset(comp_b, row) - subset(comp_a, row) for row in idx]
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def make_blocks(
    shape: tuple[int, int], block_px: int = 250, n_folds: int = 5, seed: int = 20261024
) -> tuple[np.ndarray, np.ndarray]:
    """(block_id map, fold map).  Blocks are block_px squares (250 px = 25 km);
    folds are a seeded balanced permutation over blocks."""
    h, w = shape
    br = np.arange(h) // block_px
    bc = np.arange(w) // block_px
    n_bc = int(bc.max()) + 1
    block_id = (br[:, None] * n_bc + bc[None, :]).astype(np.int32)
    n_blocks = int(block_id.max()) + 1
    rng = np.random.default_rng(seed)
    fold_of_block = np.arange(n_blocks) % n_folds
    rng.shuffle(fold_of_block)
    fold_map = fold_of_block[block_id].astype(np.int32)
    return block_id, fold_map


def auc_rank(values: np.ndarray, labels: np.ndarray) -> float:
    """Mann-Whitney ROC-AUC via ranks (ties averaged`)."""
    values = np.asarray(values, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)
    n_pos = int(labels.sum())
    n_neg = int((~labels).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = rankdata(values)
    return float((ranks[labels].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def spearman_sample(
    a: np.ndarray, b: np.ndarray, mask: np.ndarray, n: int = 200_000, seed: int = 20261024
) -> float:
    """Spearman rank correlation on a seeded sample of ``mask`` pixels (finite in both)."""
    ys, xs = np.nonzero(mask)
    rng = np.random.default_rng(seed)
    if ys.size > n:
        take = rng.choice(ys.size, size=n, replace=False)
        ys, xs = ys[take], xs[take]
    av = np.asarray(a[ys, xs], dtype=np.float64)
    bv = np.asarray(b[ys, xs], dtype=np.float64)
    ok = np.isfinite(av) & np.isfinite(bv)
    if ok.sum() < 100 or np.std(av[ok]) == 0 or np.std(bv[ok]) == 0:
        return float("nan")
    ra, rb = rankdata(av[ok]), rankdata(bv[ok])
    return float(np.corrcoef(ra, rb)[0, 1])


def dot_overlap_within(dots: np.ndarray, other: np.ndarray, px: float = 3.0) -> float:
    """Fraction of ``dots`` lying within ``px`` of any ``other`` dot (lane-uniqueness check)."""
    dots = np.asarray(dots, dtype=bool)
    other = np.asarray(other, dtype=bool)
    if not dots.any() or not other.any():
        return 0.0
    dist = ndi.distance_transform_edt(~other)
    return float((dist[dots] <= px).mean())


# =============================================================================
# Segment-fold protocol (gems90-holdout-1.0.0), added 2026-10-24 by the
# DISCOVERY lane.  Same module on purpose: the brief forbids forking a shared
# tool, and these names do not collide with the component protocol above.
# Use `make_folds`/`fold_masks`/`block_terms`/`pooled_dti_with_ci` for the
# 4-fold whole-segment protocol, `make_holdout`/`score_pooled` for the
# whole-component protocol.
# =============================================================================
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
