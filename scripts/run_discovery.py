#!/usr/bin/env python3
"""GEMSDOE90 discovery pipeline (stages; every intermediate cached under .cache/work).

  features : build the leak-free static feature matrix once
  folds    : buffered whole-segment hide-and-recover — per-fold catalogue
             features, per-fold model, per-fold hidden-fault probability
  deploy   : model trained on every fold's hidden segments, applied with the
             full catalogue visible -> p_hidden over the scored domain

Nothing here submits anything, and nothing here writes into docs/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import featstack, holdout  # noqa: E402

CACHE = ROOT / ".cache" / "gems_data"
WORK = ROOT / ".cache" / "work"
N_FOLDS = 4
SEED = 20261024


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def grids() -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(CACHE / "sample_submission.tif") as ds:
        a = ds.read(1)
        inside = np.isfinite(a) & (ds.read_masks(1) > 0)
    with rasterio.open(CACHE / "existing_faults.tif") as ds:
        cat = ds.read(1) == 1
    return inside, cat


def stage_features() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    inside, _ = grids()
    names, arrs = featstack.static_features(CACHE)
    log(f"static features: {len(names)}")
    n = int(inside.sum())
    X = np.lib.format.open_memmap(WORK / "X_static.npy", mode="w+",
                                  dtype="float32", shape=(n, len(names)))
    for j, (nm, a) in enumerate(zip(names, arrs)):
        X[:, j] = a[inside].astype("float32")
    X.flush()
    (WORK / "static_names.json").write_text(json.dumps(names), encoding="utf-8")
    log(f"X_static {X.shape} -> {WORK/'X_static.npy'}")


def stage_catfeat(fold_id: np.ndarray, inside: np.ndarray, cat: np.ndarray) -> None:
    n = int(inside.sum())
    for f in list(range(N_FOLDS)) + [-1]:
        tag = "full" if f < 0 else f"f{f}"
        out = WORK / f"X_cat_{tag}.npy"
        if out.exists():
            log(f"cat features {tag}: cached")
            continue
        visible = cat if f < 0 else ((fold_id >= 0) & (fold_id != f))
        t0 = time.time()
        names, arrs = featstack.catalogue_features(visible)
        X = np.lib.format.open_memmap(out, mode="w+", dtype="float32", shape=(n, len(names)))
        for j, a in enumerate(arrs):
            X[:, j] = a[inside].astype("float32")
        X.flush()
        (WORK / "cat_names.json").write_text(json.dumps(names), encoding="utf-8")
        log(f"cat features {tag}: {len(names)} cols in {time.time()-t0:.0f}s -> {out.name}")


def _load_X(tag: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    Xs = np.load(WORK / "X_static.npy", mmap_mode="r")
    Xc = np.load(WORK / f"X_cat_{tag}.npy", mmap_mode="r")
    names = json.loads((WORK / "static_names.json").read_text()) + \
        json.loads((WORK / "cat_names.json").read_text())
    return Xs, Xc, names


def _rows_for(mask_flat: np.ndarray, k: int, rng) -> np.ndarray:
    idx = np.flatnonzero(mask_flat)
    if idx.size > k:
        idx = rng.choice(idx, k, replace=False)
    return np.sort(idx)


def _gather(tag: str, idx: np.ndarray) -> np.ndarray:
    Xs, Xc, _ = _load_X(tag)
    return np.hstack([np.asarray(Xs[idx], dtype="float32"),
                      np.asarray(Xc[idx], dtype="float32")])


def _predict_full(model, tag: str, n: int, chunk: int = 600_000) -> np.ndarray:
    Xs, Xc, _ = _load_X(tag)
    out = np.empty(n, dtype="float32")
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        blk = np.hstack([np.asarray(Xs[s:e], dtype="float32"),
                         np.asarray(Xc[s:e], dtype="float32")])
        out[s:e] = model.predict_proba(blk)[:, 1].astype("float32")
    return out


def stage_folds(n_neg: int = 120_000, max_iter: int = 160) -> None:
    from sklearn.ensemble import HistGradientBoostingClassifier

    inside, cat = grids()
    folds = holdout.make_folds(cat, inside, n_folds=N_FOLDS, seed=SEED)
    np.save(WORK / "fold_id.npy", folds.fold_id)
    np.save(WORK / "block_id.npy", folds.block_id)
    log(f"folds: {folds.n_segments} segments, per fold {folds.seg_per_fold}, px {folds.px_per_fold}")
    stage_catfeat(folds.fold_id, inside, cat)

    n = int(inside.sum())
    flat_fold = folds.fold_id[inside]
    rng = np.random.default_rng(SEED)
    for f in range(N_FOLDS):
        out = WORK / f"p_fold{f}.npy"
        if out.exists():
            log(f"fold {f}: cached prediction")
            continue
        Xtr, ytr = [], []
        for g in range(N_FOLDS):
            if g == f:
                continue
            pos = _rows_for(flat_fold == g, 60_000, rng)
            # negatives: anywhere scored under fold g (not a visible fault, not hidden-g)
            negmask = (flat_fold != g)
            neg = _rows_for(negmask, n_neg, rng)
            idx = np.concatenate([pos, neg])
            y = np.concatenate([np.ones(pos.size), np.zeros(neg.size)])
            # drop rows that are visible faults in fold g (they are masked from scoring)
            vis_g = (flat_fold >= 0) & (flat_fold != g)
            keep = ~(vis_g[idx] & (y == 0))
            Xtr.append(_gather(f"f{g}", idx[keep]))
            ytr.append(y[keep])
            log(f"  fold {f}: train block from g={g}: {int(keep.sum())} rows "
                f"({int((y[keep]==1).sum())} pos)")
        X = np.vstack(Xtr)
        y = np.concatenate(ytr)
        del Xtr, ytr
        t0 = time.time()
        clf = HistGradientBoostingClassifier(max_iter=max_iter, learning_rate=0.08,
                                             max_leaf_nodes=31, min_samples_leaf=40,
                                             l2_regularization=1.0, early_stopping=False,
                                             random_state=0)
        clf.fit(X, y)
        log(f"  fold {f}: trained on {X.shape} in {time.time()-t0:.0f}s")
        del X, y
        t0 = time.time()
        p = _predict_full(clf, f"f{f}", n)
        np.save(out, p)
        log(f"  fold {f}: predicted in {time.time()-t0:.0f}s  p[max]={p.max():.4f}")


def stage_deploy(n_neg: int = 400_000, max_iter: int = 300) -> None:
    from sklearn.ensemble import HistGradientBoostingClassifier

    inside, cat = grids()
    fold_id = np.load(WORK / "fold_id.npy")
    n = int(inside.sum())
    flat_fold = fold_id[inside]
    rng = np.random.default_rng(SEED + 1)
    Xtr, ytr = [], []
    for g in range(N_FOLDS):
        pos = _rows_for(flat_fold == g, 60_000, rng)
        neg = _rows_for(flat_fold != g, n_neg // N_FOLDS, rng)
        idx = np.concatenate([pos, neg])
        y = np.concatenate([np.ones(pos.size), np.zeros(neg.size)])
        vis_g = (flat_fold >= 0) & (flat_fold != g)
        keep = ~(vis_g[idx] & (y == 0))
        Xtr.append(_gather(f"f{g}", idx[keep]))
        ytr.append(y[keep])
    X = np.vstack(Xtr)
    y = np.concatenate(ytr)
    del Xtr, ytr
    log(f"deploy training matrix {X.shape}, {int(y.sum())} positives")
    clf = HistGradientBoostingClassifier(max_iter=max_iter, learning_rate=0.06,
                                         max_leaf_nodes=31, min_samples_leaf=40,
                                         l2_regularization=1.0, early_stopping=False,
                                         random_state=0)
    t0 = time.time()
    clf.fit(X, y)
    log(f"deploy model trained in {time.time()-t0:.0f}s")
    del X, y
    p = _predict_full(clf, "full", n)
    np.save(WORK / "p_deploy.npy", p)
    log(f"deploy prediction saved, max={p.max():.4f} mean={p.mean():.5f}")
    import pickle
    with (WORK / "deploy_model.pkl").open("wb") as fh:
        pickle.dump(clf, fh)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["features", "folds", "deploy", "all"])
    a = ap.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    if a.stage in ("features", "all"):
        stage_features()
    if a.stage in ("folds", "all"):
        stage_folds()
    if a.stage in ("deploy", "all"):
        stage_deploy()
    log("done")
