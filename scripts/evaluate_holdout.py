#!/usr/bin/env python3
"""Shared holdout evaluator: buffered whole-segment hide-and-recover, pooled DTI.

Compares, on identical folds and at identical dot budgets:

  ours      greedy DTI-optimal emission on the fold model's hidden-fault field
            (every catalogue feature rebuilt from the fold's VISIBLE faults)
  collar    the incumbent family's recipe rebuilt fold-honestly: every visible
            fault's 200-350 m collar, thinned to 2.8 px separation
  chance    uniform lattice at the same count
  R0        the incumbent raster as submitted (ORACLE-ADVANTAGED: it was built
            with the whole catalogue visible, including the withheld segments,
            so its number is an upper bound, not a like-for-like control)

Outputs pooled DTI with a 25 km spatial-block bootstrap CI and the per-feature
leakage canary.
"""
from __future__ import annotations

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
