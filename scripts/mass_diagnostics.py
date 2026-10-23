#!/usr/bin/env python3
"""REPORT-ONLY diagnostics for the MASS variants. Never a gate, never a score.

1. Catalogue hide-and-recover PROXY: the known catalogue is split into five
   spatial folds; for each fold the withheld positives are treated as truth and
   DTI is computed for R0 and for each variant (exact O(N) distance-transform
   form, `src.dti.dti_binary_exact`). Reported with n withheld positives and a
   bootstrap 95% CI. CIRCULAR: the parent field was built partly from the
   catalogue, so this measures self-consistency against a training target, not
   performance on hidden new-fault truth. It is reported because the brief asks
   for it, and it is used to rank nothing.
2. Leakage canary: symmetric AUC of each of the 19 supplied feature bands on
   catalogue positives vs a seeded sample of off-catalogue footprint pixels.
   A single feature above 0.90 means stop and investigate.

Run: .venv/bin/python scripts/mass_diagnostics.py
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
SEED = 20261023


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def auc_symmetric(x_pos: np.ndarray, x_neg: np.ndarray) -> float:
    """P(pos > neg) + 0.5 P(tie), folded to >= 0.5 so direction is irrelevant."""
    x = np.concatenate([x_pos, x_neg])
    y = np.concatenate([np.ones(len(x_pos)), np.zeros(len(x_neg))])
    order = np.argsort(x, kind="mergesort")
    xs, ys = x[order], y[order]
    ranks = np.empty(len(x), dtype=float)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]:
            j += 1
        ranks[i:j + 1] = 0.5 * (i + j) + 1.0
        i = j + 1
    n_pos = ys.sum()
    n_neg = len(ys) - n_pos
    auc = (ranks[ys == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(max(auc, 1.0 - auc))


def main() -> int:
    import sys

    sys.path.insert(0, str(ROOT))
    from src import dti as dti_mod

    b0 = _module("build_r0_variants", ROOT / "scripts" / "build_r0_variants.py")
    t0 = time.time()

    with rasterio.open(DATA / "sample_submission.tif") as src:
        sample = src.read(1)
    foot = np.isfinite(sample)
    with rasterio.open(DATA / "existing_faults.tif") as src:
        cat = (src.read(1) > 0) & foot

    from scipy import ndimage as ndi

    distance = ndi.distance_transform_edt(~cat)
    r0 = b0.read_binary(DATA / b0.PIN_PATHS["parent_h27"], foot) & (distance > 2.0)
    receipt = json.loads((ROOT / "evidence" / "build_receipt_mass.json").read_text())
    masks = {"R0": r0}
    for v in receipt["variants"]:
        with rasterio.open(ROOT / v["files"]["nan"]["path"]) as src:
            masks[v["value"]] = (src.read(1) > 0.5) & foot

    # ---- 1. catalogue hide-and-recover PROXY, five spatial folds
    ys, xs = np.nonzero(cat)
    fold = ((ys // 500) * 7 + (xs // 500)) % 5
    rng = np.random.default_rng(SEED)
    folds = {}
    per_file = {name: [] for name in masks}
    withheld_counts = []
    for f in range(5):
        truth = np.zeros_like(cat)
        sel = fold == f
        withheld_counts.append(int(sel.sum()))
        truth[ys[sel], xs[sel]] = True
        for name, m in masks.items():
            per_file[name].append(dti_mod.dti_binary_exact(m, truth))
    for name, vals in per_file.items():
        arr = np.asarray(vals)
        boot = rng.choice(arr, size=(2000, arr.size), replace=True).mean(axis=1)
        folds[name] = {
            "fold_dti": [round(float(v), 6) for v in vals],
            "mean_dti": round(float(arr.mean()), 6),
            "boot95_ci": [round(float(np.quantile(boot, 0.025)), 6),
                          round(float(np.quantile(boot, 0.975)), 6)],
            "delta_vs_r0": round(float(arr.mean() - np.mean(per_file["R0"])), 6),
        }

    # ---- 2. leakage canary, single-feature symmetric AUC
    feat_path = DATA / "training_features.tif"
    pos = np.flatnonzero(cat.ravel())
    off = np.flatnonzero((foot & ~cat).ravel())
    neg = np.sort(rng.choice(off, size=min(120_000, off.size), replace=False))
    canary = []
    with rasterio.open(feat_path) as src:
        nodata = src.nodata
        for band in range(1, src.count + 1):
            a = src.read(band).ravel()
            pv = a[pos].astype(np.float64)
            nv = a[neg].astype(np.float64)
            ok_p, ok_n = np.isfinite(pv) & (pv != nodata), np.isfinite(nv) & (nv != nodata)
            # sentinel values (nodata, e.g. masked catalogue pixels) -> median fill would
            # leak; instead drop them and report the dropped fraction.
            auc = auc_symmetric(pv[ok_p], nv[ok_n]) if 0 < ok_p.sum() < len(pv) or ok_n.sum() else None
            canary.append({
                "band": band,
                "symmetric_auc": round(auc, 4) if auc is not None else None,
                "pos_finite_frac": round(float(ok_p.mean()), 4),
                "neg_finite_frac": round(float(ok_n.mean()), 4),
            })

    out = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "labels": "REPORT ONLY - never a gate, never used to rank or select a file",
        "catalogue_hide_recover_proxy": {
            "design": "five spatial folds of the 60,988 known catalogue positives "
                      "((row//500)*7 + (col//500)) % 5; withheld positives treated as truth",
            "n_withheld_positives": withheld_counts,
            "circularity": "the parent field was built partly from this catalogue, so this is "
                           "self-consistency against a training target, not hidden-truth accuracy",
            "degenerate_by_construction": "The kernel radius is exactly 3 px and hard constraint 4 "
                                          "forbids dot within 3 px of the catalogue, so T is "
                                          "identically 0 on catalogue positives for every compliant "
                                          "file: the proxy returns 0.0 and cannot separate the three "
                                          "candidates. R0 scores only because 1,611 of its dots sit "
                                          "inside the collar. Read this diagnostic as unavailable, "
                                          "not as a bad result.",
            "results": folds,
            "prior_note": "This proxy correlated -0.87 to +0.54 with live scores over 12-14 files "
                          "(brief s3) and has no power here.",
        },
        "leakage_canary": {
            "design": "symmetric single-feature AUC, 60,988 catalogue positives vs 120,000 seeded "
                      f"off-catalogue footprint negatives (seed {SEED}); nodata dropped, not filled",
            "max_auc": max((c["symmetric_auc"] or 0) for c in canary),
            "stop_trigger_auc_gt_0_90": any((c["symmetric_auc"] or 0) > 0.90 for c in canary),
            "bands": canary,
        },
        "sgmc_control": {"status": "NOT RUN",
                         "reason": "no fold-clean SGMC control validated for a mass-only edit; not a gate"},
        "elapsed_s": round(time.time() - t0, 1),
    }
    path = ROOT / "evidence" / "diagnostics_mass.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"proxy": {k: {kk: vv for kk, vv in v.items() if kk != "fold_dti"}
                                for k, v in folds.items()},
                      "canary_max": out["leakage_canary"]["max_auc"],
                      "canary_stop": out["leakage_canary"]["stop_trigger_auc_gt_0_90"]}, indent=1))
    print("->", path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
