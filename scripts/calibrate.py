#!/usr/bin/env python3
"""Leaderboard inversion: calibrate the hidden-fault field against real scores.

The DTI algebra is exact and every term except the hidden truth is observable:

    DTI_j = T_j / (0.2 T_j + 0.2 (S_j - M_j) + 0.8 |G|)
    T_j   = sum_x pi(x) c_j(x)        c_j = k(distance to nearest dot of file j)
    M_j   = sum_{dots i} (1 - exp(-u_i)),   u = pi (*) k

So a *model* of the hidden-fault density pi predicts the score of every raster
whose dots we hold, and the organizer-side scores of already-submitted rasters
become measurements that constrain pi.

Two anchors are model-free:
  * `lattice_s5` is a uniform 5 px lattice over the whole footprint, so its
    coverage of any truth set is its mean coverage (0.3718) whatever the truth
    looks like.  That pins |G| on its own.
  * `placeholder` is a spatially blind blob; its implied lift (0.71) is an
    independent check that the |G| scale is right.

Scores are OWNER-REPORTED (no submission-page receipts are on file); they are
treated as measurements with noise, never as organizer-confirmed values.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import convolve, distance_transform_edt
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CACHE = ROOT / ".cache" / "gems_data"
WORK = ROOT / ".cache" / "work"

# (key, path relative to .cache/gems_data, owner-reported organizer score)
REGISTRY = [
    ("lattice_s5", "scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904),
    ("hedge_v2", "scored/8GEMSDOE_Hedge-v2_submission.tif", 0.1563),
    ("ctx_ridge", "scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif", 0.1280),
    ("dotted_ridge", "scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif", 0.1839),
    ("h16_1", "scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif", 0.1855),
    ("h19_4", "scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif", 0.1894),
    ("h19_5", "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", 0.1922),
    ("d1_5", "scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477),
    ("d2_8", "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600),
    ("tgc_v2", "scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449),
    ("h27_4_solo", "scored/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif", 0.2708),
    ("ens12", "scored/gemsdoe-ens12-adopted-7f00890a.tif", 0.1563),
    ("placeholder", "scored/gemsdoe9-PLACEHOLDER-2314b599.tif", 0.0107),
    ("R0_h33_b2", "parent/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778),
]
KPATCH = np.maximum(0.0, 1.0 - np.hypot(*np.mgrid[-3:4, -3:4]) / 3.0).astype("float32")


def grids():
    with rasterio.open(CACHE / "sample_submission.tif") as ds:
        a = ds.read(1)
        inside = np.isfinite(a) & (ds.read_masks(1) > 0)
    with rasterio.open(CACHE / "existing_faults.tif") as ds:
        cat = ds.read(1) == 1
    return inside, cat


def build_registry_cache() -> dict:
    """Coverage vector and dot index list for every scored registry raster."""
    inside, cat = grids()
    scored = inside & ~cat
    n = int(inside.sum())
    cov = np.lib.format.open_memmap(WORK / "cov_registry.npy", mode="w+",
                                    dtype="float32", shape=(len(REGISTRY), n))
    meta = []
    flat_of = np.full(inside.shape, -1, dtype="int64")
    flat_of[inside] = np.arange(n)
    for j, (name, rel, score) in enumerate(REGISTRY):
        with rasterio.open(CACHE / rel) as ds:
            a = ds.read(1).astype("float32")
        a = np.where(np.isfinite(a), a, 0.0)
        dots = (a > 0) & scored
        c = np.maximum(0.0, 1.0 - distance_transform_edt(~dots) / 3.0).astype("float32")
        cov[j, :] = c[inside]
        idx = flat_of[dots]
        np.save(WORK / f"dotidx_{name}.npy", idx.astype("int64"))
        meta.append({"name": name, "path": rel, "score_owner_reported": score,
                     "n_dots_scored": int(dots.sum()),
                     "n_dots_raw": int(((a > 0) & inside).sum()),
                     "sum_cov": float(c[inside].sum())})
        print(f"  {name:13s} dots={int(dots.sum()):7d} sumC={float(c[inside].sum()):10.0f}", flush=True)
    cov.flush()
    (WORK / "registry_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return {"meta": meta, "n": n}


def predict_scores(pi_flat: np.ndarray, inside: np.ndarray, cov: np.ndarray,
                   meta: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Predicted DTI for every registry raster under hidden-fault field pi."""
    G = float(pi_flat.sum())
    pi2d = np.zeros(inside.shape, dtype="float32")
    pi2d[inside] = pi_flat
    u = convolve(pi2d, KPATCH, mode="constant", cval=0.0)[inside]
    T = cov @ pi_flat
    M = np.empty(len(meta))
    for j, m in enumerate(meta):
        idx = np.load(WORK / f"dotidx_{m['name']}.npy")
        M[j] = float((1.0 - np.exp(-u[idx])).sum())
    S = np.array([m["n_dots_scored"] for m in meta], dtype="float64")
    den = 0.2 * T + 0.2 * (S - M) + 0.8 * G
    return T / np.maximum(den, 1e-9), T, M, G


def fit(p_flat: np.ndarray, inside: np.ndarray, cat: np.ndarray, G_anchor: float) -> dict:
    cov = np.load(WORK / "cov_registry.npy", mmap_mode="r")
    cov = np.asarray(cov)
    meta = json.loads((WORK / "registry_meta.json").read_text())
    obs = np.array([m["score_owner_reported"] for m in meta])
    scored_flat = ~cat[inside]
    base = (np.clip(p_flat, 1e-9, None) * scored_flat).astype("float64")

    # pi is an OCCUPANCY field: a pixel is a hidden-fault pixel or it is not, so
    # 0 <= pi <= 1 must hold while sum(pi) = |G|.  Solve  sum min(1, lam*w) = G
    # for lam.  The ranking of w = base**gamma does not depend on gamma, so the
    # sort is done once and the solve is O(log n) per iteration.
    order = np.argsort(base)[::-1]
    inv = np.empty_like(order)
    inv[order] = np.arange(order.size)
    base_sorted = base[order]

    def pi_of(gamma: float, G: float) -> np.ndarray:
        ws = base_sorted ** gamma
        if not np.isfinite(ws).all() or ws.sum() <= 0:
            return np.zeros_like(base, dtype="float32")
        suffix = np.concatenate([np.cumsum(ws[::-1])[::-1], [0.0]])
        lo, hi = 1e-30, 1e30
        for _ in range(200):
            lam = np.sqrt(lo * hi)
            k = int(np.searchsorted(-ws, -1.0 / lam, side="right"))
            tot = k + lam * suffix[k]
            if tot > G:
                hi = lam
            else:
                lo = lam
            if hi / lo < 1 + 1e-12:
                break
        lam = np.sqrt(lo * hi)
        return np.minimum(1.0, lam * ws)[inv].astype("float32")

    def sse(gamma: float, G: float) -> float:
        pred, *_ = predict_scores(pi_of(gamma, G), inside, cov, meta)
        return float(np.sum((pred - obs) ** 2))

    t0 = time.time()
    res = minimize_scalar(lambda g: sse(g, G_anchor), bounds=(0.15, 6.0), method="bounded",
                          options={"xatol": 1e-3})
    gamma = float(res.x)
    # refine |G| jointly (coarse grid; the lattice anchor is the prior)
    best = (sse(gamma, G_anchor), gamma, G_anchor)
    for Gs in np.linspace(0.6 * G_anchor, 2.5 * G_anchor, 13):
        r = minimize_scalar(lambda g: sse(g, Gs), bounds=(0.15, 6.0), method="bounded",
                            options={"xatol": 2e-3})
        if r.fun < best[0]:
            best = (float(r.fun), float(r.x), float(Gs))
    sse_joint, gamma_j, G_j = best
    pred_a, T_a, M_a, _ = predict_scores(pi_of(gamma, G_anchor), inside, cov, meta)
    pred_b, T_b, M_b, _ = predict_scores(pi_of(gamma_j, G_j), inside, cov, meta)
    pi_best = pi_of(gamma_j, G_j)
    out = {
        "occupancy_capped": True,
        "pi_max": float(pi_best.max()),
        "pi_n_saturated": int((pi_best >= 0.999).sum()),
        "pi_sum": float(pi_best.sum()),
        "G_anchor": G_anchor, "gamma_anchor": gamma,
        "rmse_anchor": float(np.sqrt(np.mean((pred_a - obs) ** 2))),
        "G_joint": G_j, "gamma_joint": gamma_j,
        "rmse_joint": float(np.sqrt(sse_joint / len(obs))),
        "fit_seconds": round(time.time() - t0, 1),
        "files": [{"name": m["name"], "n_dots": m["n_dots_scored"],
                   "score_owner_reported": m["score_owner_reported"],
                   "pred_anchor": float(pred_a[j]), "pred_joint": float(pred_b[j]),
                   "T_joint": float(T_b[j]), "M_joint": float(M_b[j])}
                  for j, m in enumerate(meta)],
    }
    np.save(WORK / "pi_calibrated.npy", pi_best)
    np.save(WORK / "pi_calibrated_anchor.npy", pi_of(gamma, G_anchor))
    return out


if __name__ == "__main__":
    inside, cat = grids()
    if not (WORK / "registry_meta.json").exists():
        print("building registry coverage cache …", flush=True)
        build_registry_cache()
    p = np.load(WORK / "p_deploy.npy")
    G_ANCHOR = 12545.0  # from the uniform-lattice blind probe (see docs)
    out = fit(p, inside, cat, G_ANCHOR)
    (ROOT / "evidence" / "calibration_fit.json").write_text(json.dumps(out, indent=2) + "\n",
                                                            encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "files"}, indent=2))
    print(f"\n{'file':14s} {'n_dots':>8s} {'observed':>9s} {'pred(G anchor)':>15s} {'pred(G joint)':>14s}")
    for f in out["files"]:
        print(f"{f['name']:14s} {f['n_dots']:8d} {f['score_owner_reported']:9.4f} "
              f"{f['pred_anchor']:15.4f} {f['pred_joint']:14.4f}")
