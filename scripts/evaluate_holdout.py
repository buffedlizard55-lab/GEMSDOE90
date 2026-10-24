#!/usr/bin/env python3
"""Shared hide-and-recover holdout evaluator v1 (GEMSDOE90).

Protocol (parallel-run brief): withhold WHOLE fault segments (8-connected
catalogue components, assigned by component-centroid spatial block) with a
5 px buffer; every catalogue-based feature/mask for a fold candidate must be
derived only from the visible faults; visible faults are masked pixel-exactly;
score POOLED DTI (alpha=0.2, beta=0.8, 300 m triangular kernel = R=3 px at
100 m/px, src.dti assumptions A1/A2) on withheld positives inside the
evaluation blocks, with a 20 km block-bootstrap 95% CI.

This module is the shared evaluator: import `make_holdout` / `score_pooled`
from experiment scripts; do not fork it.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dti import dti_from_components, kernel

EVALUATOR_VERSION = "evaluate_holdout.py v1 (whole-component, 5px buffer, pooled DTI a0.2/b0.8 R3px, 20km block bootstrap)"


def make_holdout(catalogue: np.ndarray, footprint: np.ndarray, seed: int = 20261024,
                 holdout_frac: float = 0.25, buffer_px: int = 5, block_px: int = 200):
    """Return dict(visible, withheld, eval_mask, n_withheld_positives, segments)."""
    cat = np.asarray(catalogue) > 0
    foot = np.asarray(footprint, dtype=bool)
    lab, n = ndi.label(cat, structure=np.ones((3, 3), dtype=int))
    rng = np.random.default_rng(seed)
    # assign whole components by centroid block hash -> deterministic, spatial
    cents = ndi.center_of_mass(cat, lab, range(1, n + 1))
    block_ids = {}
    withheld_ids = []
    for i, (r, c) in enumerate(cents, start=1):
        key = (int(r) // block_px, int(c) // block_px)
        if key not in block_ids:
            block_ids[key] = rng.random()
        if block_ids[key] < holdout_frac:
            withheld_ids.append(i)
    withheld = np.isin(lab, withheld_ids) & foot
    buffer_zone = ndi.binary_dilation(withheld, iterations=buffer_px)
    visible = cat & ~buffer_zone & foot
    eval_mask = np.zeros_like(foot)
    H, W = foot.shape
    rows, cols = np.nonzero(withheld)
    blocks = {(int(r) // block_px, int(c) // block_px) for r, c in zip(rows, cols)}
    for br, bc in blocks:
        r0, r1 = br * block_px, min(H, (br + 1) * block_px)
        c0, c1 = bc * block_px, min(W, (bc + 1) * block_px)
        eval_mask[r0:r1, c0:c1] = foot[r0:r1, c0:c1]
    return {"visible": visible, "withheld": withheld, "eval_mask": eval_mask,
            "n_withheld_positives": int(withheld.sum()), "n_segments_withheld": len(withheld_ids),
            "n_segments_total": int(n), "blocks": sorted(blocks)}


def _components(dots: np.ndarray, truth: np.ndarray, eval_mask: np.ndarray):
    p = np.asarray(dots, dtype=bool) & eval_mask
    t = np.asarray(truth, dtype=bool) & eval_mask
    dist_t = ndi.distance_transform_edt(~t)
    k_at = kernel(dist_t)
    S = float(p.sum()); M = float(k_at[p].sum()); G = int(t.sum())
    credit = np.zeros(p.shape, dtype=np.float64)
    yy, xx = np.mgrid[-3:4, -3:4]
    kp = kernel(np.hypot(yy, xx))
    H, W = p.shape
    for i, j in zip(*np.nonzero(p)):
        y0, y1, x0, x1 = max(0, i - 3), min(H, i + 4), max(0, j - 3), min(W, j + 4)
        sub = kp[y0 - (i - 3): y0 - (i - 3) + (y1 - y0), x0 - (j - 3): x0 - (j - 3) + (x1 - x0)]
        credit[y0:y1, x0:x1] = np.maximum(credit[y0:y1, x0:x1], sub)
    T = float(credit[t].sum())
    return T, S, M, G


def score_pooled(candidates: dict[str, np.ndarray], holdout: dict, n_boot: int = 1000,
                 seed: int = 20261024, block_px: int = 200) -> dict:
    """Pooled HOLDOUT-DTI per candidate + 20 km block-bootstrap CI + deltas vs first candidate."""
    truth, eval_mask = holdout["withheld"], holdout["eval_mask"]
    blocks = holdout["blocks"]
    names = list(candidates)
    per_block = {}
    point = {}
    for name in names:
        dots = np.asarray(candidates[name], dtype=bool)
        # block-level (T,S,M,G) for bootstrap; global credit computed once per block via full field
        p = dots & eval_mask
        dist_t = ndi.distance_transform_edt(~(truth & eval_mask))
        k_at = kernel(dist_t)
        credit = np.zeros(p.shape)
        yy, xx = np.mgrid[-3:4, -3:4]; kp = kernel(np.hypot(yy, xx))
        H, W = p.shape
        for i, j in zip(*np.nonzero(p)):
            y0, y1, x0, x1 = max(0, i - 3), min(H, i + 4), max(0, j - 3), min(W, j + 4)
            credit[y0:y1, x0:x1] = np.maximum(credit[y0:y1, x0:x1],
                kp[y0-(i-3):y0-(i-3)+(y1-y0), x0-(j-3):x0-(j-3)+(x1-x0)])
        arr = np.zeros((len(blocks), 4))
        for bi, (br, bc) in enumerate(blocks):
            r0, r1, c0, c1 = br*block_px, min(H, (br+1)*block_px), bc*block_px, min(W, (bc+1)*block_px)
            ts = (truth & eval_mask)[r0:r1, c0:c1]; ps = p[r0:r1, c0:c1]
            arr[bi] = [credit[r0:r1, c0:c1][ts].sum(), ps.sum(), k_at[r0:r1, c0:c1][ps].sum(), ts.sum()]
        per_block[name] = arr
        T, S, M, G = arr.sum(axis=0)
        point[name] = dti_from_components(float(T), float(S), float(M), int(G))
    rng = np.random.default_rng(seed)
    nb = len(blocks)
    idx = rng.integers(0, nb, size=(n_boot, nb))
    def boot(arr):
        s = arr[idx].sum(axis=1)
        den = 0.2*s[:, 0] + 0.2*(s[:, 1]-s[:, 2]) + 0.8*s[:, 3]
        return np.where(den > 0, s[:, 0]/np.where(den == 0, 1, den), 0.0)
    boots = {n: boot(per_block[n]) for n in names}
    base = names[0]
    out = {"evaluator_version": EVALUATOR_VERSION, "label": "HOLDOUT-DTI",
           "n_withheld_positives": holdout["n_withheld_positives"],
           "n_segments_withheld": holdout["n_segments_withheld"], "candidates": {}}
    for n in names:
        d = boots[n] - boots[base]
        out["candidates"][n] = {"holdout_dti": round(point[n], 6),
            "ci95": [round(float(np.percentile(boots[n], 2.5)), 6), round(float(np.percentile(boots[n], 97.5)), 6)],
            "delta_vs_first": round(point[n]-point[base], 6),
            "delta_ci95": [round(float(np.percentile(d, 2.5)), 6), round(float(np.percentile(d, 97.5)), 6)],
            "n_dots_in_eval": int(per_block[n][:, 1].sum())}
    return out
