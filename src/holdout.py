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
