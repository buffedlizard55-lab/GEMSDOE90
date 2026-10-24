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


# =============================================================================
# CLI for the 4-fold whole-segment protocol (DISCOVERY lane, 2026-10-24).
#   python scripts/evaluate_holdout.py --budgets 8000,20000,35000
# The functions above remain the importable shared library for the
# whole-component protocol; nothing here replaces them.
# =============================================================================
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import emit as emitmod                       # noqa: E402
from src import holdout as hm                         # noqa: E402

CACHE = ROOT / ".cache" / "gems_data"
WORK = ROOT / ".cache" / "work"
N_FOLDS = 4
SEED = 20261024


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def grids():
    with rasterio.open(CACHE / "sample_submission.tif") as ds:
        a = ds.read(1)
        inside = np.isfinite(a) & (ds.read_masks(1) > 0)
    with rasterio.open(CACHE / "existing_faults.tif") as ds:
        cat = ds.read(1) == 1
    return inside, cat


def poisson_thin(mask: np.ndarray, sep: float, n: int, seed: int) -> np.ndarray:
    """Spatially even subset of `mask` with min separation `sep` (dart throwing)."""
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(mask.ravel())
    rng.shuffle(idx)
    h, w = mask.shape
    blocked = np.zeros(mask.shape, dtype=bool)
    r = int(np.ceil(sep))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disc = np.hypot(yy, xx) < sep
    out = np.zeros(mask.shape, dtype=bool)
    got = 0
    for k in idx:
        i, j = divmod(int(k), w)
        if blocked[i, j]:
            continue
        out[i, j] = True
        got += 1
        r0, r1 = max(0, i - r), min(h, i + r + 1)
        c0, c1 = max(0, j - r), min(w, j + r + 1)
        sub = disc[r0 - (i - r):r0 - (i - r) + (r1 - r0), c0 - (j - r):c0 - (j - r) + (c1 - c0)]
        blocked[r0:r1, c0:c1] |= sub
        if got >= n:
            break
    return out


def lattice(scored: np.ndarray, n: int) -> np.ndarray:
    step = max(1, int(round(np.sqrt(scored.sum() / max(n, 1)))))
    out = np.zeros(scored.shape, dtype=bool)
    out[::step, ::step] = True
    out &= scored
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budgets", default="12000,20000,30000,37654")
    ap.add_argument("--buffer-px", type=float, default=3.0)
    ap.add_argument("--n-max", type=int, default=60000)
    ap.add_argument("--out", default=str(ROOT / "evidence" / "holdout_report.json"))
    args = ap.parse_args()
    budgets = [int(b) for b in args.budgets.split(",")]

    inside, cat = grids()
    folds = hm.make_folds(cat, inside, n_folds=N_FOLDS, seed=SEED)
    block_id = folds.block_id
    with rasterio.open(CACHE / "parent" /
                       "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as ds:
        r0 = ds.read(1).astype("float32")
    r0 = np.where(np.isfinite(r0), r0, 0.0)

    methods = ["ours", "collar", "chance", "R0_oracle"]
    per_block = {m: {b: {} for b in budgets} for m in methods}
    fold_info = []

    for f in range(N_FOLDS):
        visible, truth, scored = hm.fold_masks(folds, f, inside, buffer_px=args.buffer_px)
        log(f"fold {f}: visible {int(visible.sum())} px, truth {int(truth.sum())} px, "
            f"scored {int(scored.sum())} px")
        fold_info.append({"fold": f, "visible_px": int(visible.sum()),
                          "truth_px": int(truth.sum()), "scored_px": int(scored.sum())})
        p = np.load(WORK / f"p_fold{f}.npy")
        pi = np.zeros(inside.shape, dtype="float32")
        pi[inside] = p
        pi[~scored] = 0.0
        pi = (pi / max(pi.sum(), 1e-9)) * float(truth.sum())   # scale only; ranking unchanged

        em = emitmod.greedy_emit(pi, scored, n_max=max(budgets))
        k_truth = hm.kernel(distance_transform_edt(~truth)) if truth.any() \
            else np.zeros(inside.shape)
        d_vis = distance_transform_edt(~visible)
        collar_mask = scored & (d_vis >= 2.0) & (d_vis <= 3.5)
        collar = poisson_thin(collar_mask, 2.8, max(budgets), seed=1000 + f)
        cr, cc = np.nonzero(collar)
        order = np.random.default_rng(2000 + f).permutation(cr.size)
        for b in budgets:
            preds = {
                "ours": emitmod.dots_to_raster(em, inside.shape, min(b, em.rows.size)),
                "collar": np.zeros(inside.shape, "float32"),
                "chance": lattice(scored, b).astype("float32"),
                "R0_oracle": np.where(scored, r0, 0.0).astype("float32"),
            }
            sel = order[:b]
            preds["collar"][cr[sel], cc[sel]] = 1.0
            for m, pr in preds.items():
                per_block[m][b][f] = hm.block_terms(pr, truth, scored, block_id, k_truth)
        del em, pi, p

    report = {"evaluator": hm.EVALUATOR_VERSION, "protocol": "buffered whole-segment hide-and-recover",
              "buffer_px": args.buffer_px, "n_folds": N_FOLDS, "n_segments": folds.n_segments,
              "seg_per_fold": folds.seg_per_fold, "folds": fold_info, "results": {}}
    for m in methods:
        report["results"][m] = {}
        for b in budgets:
            merged: dict[int, hm.DTITerms] = {}
            for f in range(N_FOLDS):
                for blk, t in per_block[m][b][f].items():
                    key = blk * 10 + f           # fold-block = independent resampling unit
                    merged[key] = t
            r = hm.pooled_dti_with_ci(merged)
            report["results"][m][str(b)] = r
            log(f"  {m:10s} n={b:6d}  pooled HOLDOUT-DTI={r['dti']:.5f} "
                f"CI[{r['ci'][0]:.5f},{r['ci'][1]:.5f}] truth={r['n_truth']}")
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
