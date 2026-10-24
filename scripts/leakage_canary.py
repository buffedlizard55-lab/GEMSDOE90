#!/usr/bin/env python3
"""Leakage canary: score every feature ALONE against withheld truth.

A single feature that separates withheld fault pixels from background with
AUC > 0.90 is treated as leakage (a label-derived channel) until proven
otherwise.  The canary is run fold-honestly: catalogue-derived features come
from the fold's *visible* catalogue only, and the positives are that fold's
withheld segments.  AUC is reported symmetrically, max(a, 1-a), because a
perfectly anti-correlated feature leaks just as badly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.calibrate import grids, WORK  # noqa: E402

SEED = 20261024
N_NEG = 150_000


def auc(x: np.ndarray, y: np.ndarray) -> float:
    ok = np.isfinite(x)
    x, y = x[ok], y[ok]
    if y.sum() == 0 or y.sum() == y.size:
        return 0.5
    r = np.argsort(np.argsort(x, kind="stable"), kind="stable").astype("float64") + 1.0
    n1 = float(y.sum())
    n0 = float(y.size - n1)
    a = (r[y].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)
    return float(a)


def main() -> int:
    inside, cat = grids()
    names = json.loads((WORK / "static_names.json").read_text())
    cnames = json.loads((WORK / "cat_names.json").read_text())
    fold = np.load(WORK / "fold_id.npy")
    if fold.shape == inside.shape:
        fold = fold[inside]
    Xs = np.load(WORK / "X_static.npy", mmap_mode="r")
    rng = np.random.default_rng(SEED)
    catf = cat[inside]
    out: dict[str, float] = {}
    for g in range(int(fold.max()) + 1):
        # positives: this fold's WITHHELD catalogue pixels (the holdout's proxy truth)
        # negatives: background pixels that are not catalogue at all
        pos = np.flatnonzero(fold == g)
        neg_pool = np.flatnonzero((fold < 0) & ~catf)
        neg = rng.choice(neg_pool, size=min(N_NEG, neg_pool.size), replace=False)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos, assume_unique=True)
        Xc = np.load(WORK / f"X_cat_f{g}.npy", mmap_mode="r")
        blk = np.asarray(Xs[idx, :])
        cblk = np.asarray(Xc[idx, :])
        for j, nm in enumerate(names):
            a = auc(blk[:, j].astype("float64"), y)
            out[nm] = max(out.get(nm, 0.0), max(a, 1.0 - a))
        for j, nm in enumerate(cnames):
            a = auc(cblk[:, j].astype("float64"), y)
            out[nm] = max(out.get(nm, 0.0), max(a, 1.0 - a))
        print(f"  fold {g}: {len(pos)} withheld positives, {len(neg)} negatives", flush=True)
    top = dict(sorted(out.items(), key=lambda kv: -kv[1]))
    mx = max(out.values())
    mf = max(out, key=out.get)
    rep = {"rule": "single-feature symmetric AUC > 0.90 = leakage until proven otherwise",
           "folds": int(fold.max()) + 1, "negatives_per_fold": N_NEG,
           "max_auc": mx, "max_feature": mf, "n_features": len(out),
           "flagged": [k for k, v in out.items() if v > 0.90],
           "top_features": {k: round(v, 4) for k, v in list(top.items())[:15]},
           "all": {k: round(v, 4) for k, v in top.items()}}
    (ROOT / "evidence" / "leakage_canary.json").write_text(json.dumps(rep, indent=2) + "\n",
                                                           encoding="utf-8")
    print(f"\nmax symmetric AUC {mx:.4f} ({mf}); flagged: {rep['flagged'] or 'none'}")
    for k, v in list(top.items())[:12]:
        print(f"  {k:28s} {v:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
