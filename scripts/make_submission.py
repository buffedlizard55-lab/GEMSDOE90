#!/usr/bin/env python3
"""Emit the candidate, screen it against the registry, validate it, write it.

Pipeline: calibrated hidden-fault field pi  ->  greedy DTI-optimal emission
->  budget chosen at the maximum of the exact predicted-DTI curve  ->  lane
(duplicate) screen against every registry raster  ->  format gate  ->  GeoTIFF.

Nothing here uploads anything.
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
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import emit as emitmod            # noqa: E402
from src.submission_writer import write_submission, validate_submission, sha256_file  # noqa: E402
from scripts.calibrate import REGISTRY, grids  # noqa: E402

CACHE = ROOT / ".cache" / "gems_data"
WORK = ROOT / ".cache" / "work"


def registry_dot_masks(scored: np.ndarray) -> dict[str, np.ndarray]:
    out = {}
    for name, rel, _ in REGISTRY:
        with rasterio.open(CACHE / rel) as ds:
            a = ds.read(1).astype("float32")
        a = np.where(np.isfinite(a), a, 0.0)
        out[name] = (a > 0) & scored
    return out


def lane_report(dots: np.ndarray, surface: np.ndarray, scored: np.ndarray,
                reg: dict[str, np.ndarray], sample_frac: float = 0.25) -> dict:
    """Duplicate screen: dot overlap within 3 px and surface rank correlation.

    Raw overlap alone is not a duplicate test.  A registry raster that blankets
    the domain (the 5 px lattice probe covers 98 % of scored pixels within 3 px)
    makes *every* candidate look like a copy of it.  The screen therefore also
    reports the overlap a blind placement would achieve against that raster —
    the share of scored pixels within 3 px of its dots — and the excess over it,
        excess = (overlap - chance) / (1 - chance),
    which is 0 for an unrelated placement and 1 for an exact copy.  A candidate
    is a duplicate when it is both absolutely close (> 0.70) and far above
    chance (excess > 0.30), or when the surfaces correlate above rho = 0.90.
    """
    rows = []
    dr, dc = np.nonzero(dots)
    rng = np.random.default_rng(11)
    sub = scored & (rng.random(scored.shape) < sample_frac)
    for name, m in reg.items():
        near = distance_transform_edt(~m) <= 3.0
        overlap = float(near[dr, dc].mean()) if dr.size else 0.0
        chance = float(near[scored].mean())
        excess = (overlap - chance) / max(1.0 - chance, 1e-9)
        rho = float(spearmanr(surface[sub], m[sub].astype("float32")).statistic)
        rows.append({"registry": name, "dot_overlap_within_3px": overlap,
                     "chance_overlap": chance, "excess_over_chance": excess,
                     "spearman_surface": rho,
                     "duplicate": bool((overlap > 0.70 and excess > 0.30) or rho > 0.90)})
    worst = max(rows, key=lambda r: r["excess_over_chance"])
    return {"per_registry": rows,
            "max_overlap": max(r["dot_overlap_within_3px"] for r in rows),
            "max_excess_over_chance": worst["excess_over_chance"],
            "worst_registry": worst["registry"],
            "max_spearman": max(r["spearman_surface"] for r in rows),
            "duplicate": any(r["duplicate"] for r in rows)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-max", type=int, default=70_000)
    ap.add_argument("--overlap-cap", type=float, default=0.62)
    ap.add_argument("--name", default=None)
    ap.add_argument("--n-fixed", type=int, default=None,
                    help="dot budget; default = argmax of the holdout DTI curve if "
                         "evidence/holdout_budget_curve.json exists, else the model curve")
    ap.add_argument("--outdir", default=str(ROOT / "releases"))
    args = ap.parse_args()

    inside, cat = grids()
    scored = inside & ~cat
    pi_flat = np.load(WORK / "pi_calibrated.npy")
    pi = np.zeros(inside.shape, dtype="float32")
    pi[inside] = pi_flat
    pi[~scored] = 0.0
    G = float(pi.sum())
    print(f"calibrated field: |G| = {G:.0f}, max pi = {pi.max():.4f}, "
          f"pi>1% on {int((pi > 0.01).sum())} px", flush=True)

    reg = registry_dot_masks(scored)
    worst_name = "R0_h33_b2"
    guard = distance_transform_edt(~reg[worst_name]) <= 3.0

    t0 = time.time()
    em = emitmod.greedy_emit(pi, scored, n_max=args.n_max, overlap_cap=args.overlap_cap,
                             forbid_within=guard)
    print(f"greedy: {em.rows.size} dots in {time.time()-t0:.0f}s "
          f"(pool floor gain {em.min_pool_gain:.5f})", flush=True)
    curve = emitmod.dti_curve(em, G)
    n_model = int(np.argmax(curve) + 1)
    budget_src = "model-curve argmax"
    n_star = n_model
    hb = ROOT / "evidence" / "holdout_budget_curve.json"
    if args.n_fixed:
        n_star, budget_src = args.n_fixed, "operator-fixed"
    elif hb.exists():
        rep = json.loads(hb.read_text())["results"]["ours"]
        best_b = max(rep, key=lambda b: rep[b]["dti"])
        n_star, budget_src = int(best_b), "HOLDOUT-DTI curve argmax"
        print(f"budget from holdout curve: n={n_star} "
              f"(HOLDOUT-DTI {rep[best_b]['dti']:.4f} "
              f"CI[{rep[best_b]['ci'][0]:.4f},{rep[best_b]['ci'][1]:.4f}])")
    n_star = min(n_star, em.rows.size)
    print(f"model self-curve: max {curve.max():.4f} at n={n_model} (SELF-REFERENTIAL, "
          f"not a projection); budget chosen = {n_star} via {budget_src}; "
          f"marginal gain there {em.gain[n_star-1]:.4f}")

    dots = emitmod.dots_to_raster(em, inside.shape, n_star)
    lane = lane_report(dots.astype(bool), pi, scored, reg)
    print(json.dumps({k: v for k, v in lane.items() if k != "per_registry"}, indent=1))
    for r in lane["per_registry"]:
        print(f"   vs {r['registry']:13s} overlap={r['dot_overlap_within_3px']:.3f} "
              f"spearman={r['spearman_surface']:+.3f} duplicate={r['duplicate']}")
    if lane["duplicate"]:
        print("STOP: duplicate lane — candidate not written")
        return 2

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    base = args.name or f"gems90-cnc-{n_star}dots-{stamp}"
    outdir = Path(args.outdir)
    rep = write_submission(dots, outdir / f"{base}.tif", CACHE / "sample_submission.tif",
                           outside="zeros")
    rep.update({
        "candidate": base, "n_dots": n_star, "G_calibrated": G,
        "budget_source": budget_src,
        "self_referential_curve_value": float(curve[n_star - 1]),
        "self_referential_curve_max": float(curve.max()),
        "self_referential_curve_argmax": n_model,
        "predicted_dti_at_parent_count": float(curve[min(37653, curve.size - 1)]),
        "cum_T": float(em.cum_T[n_star - 1]), "cum_M": float(em.cum_M[n_star - 1]),
        "last_marginal_gain": float(em.gain[n_star - 1]),
        "break_even_credit_at_holdout_theta": float(0.2 * 0.30 / (1 - 0.2 * 0.30)),
        "lane": lane, "pool_floor_gain": em.min_pool_gain,
        "catalogue_mass": float(dots[cat].sum()),
    })
    dr, dc = np.nonzero(dots)
    d_cat = distance_transform_edt(~cat)
    dd = d_cat[dr, dc]
    blk = (dr // 250) * 100 + (dc // 250)
    _, cnt = np.unique(blk, return_counts=True)
    rep["geometry"] = {
        "d_to_catalogue_px": {"min": float(dd.min()), "median": float(np.median(dd)),
                              "p90": float(np.percentile(dd, 90)), "max": float(dd.max())},
        "share_within_3px_of_catalogue": float((dd < 3).mean()),
        "share_3_to_6px": float(((dd >= 3) & (dd < 6)).mean()),
        "share_beyond_6px": float((dd >= 6).mean()),
        "occupied_25km_blocks": int(cnt.size),
        "max_single_block_share": float(cnt.max() / dr.size),
    }
    val = validate_submission(outdir / f"{base}.tif", CACHE / "sample_submission.tif",
                              outside="zeros", catalogue_path=CACHE / "existing_faults.tif")
    rep["format_gate"] = val
    np.save(WORK / "candidate_dots.npy", np.vstack([em.rows[:n_star], em.cols[:n_star]]))
    np.save(WORK / "dti_curve.npy", curve)
    (ROOT / "evidence" / "candidate_receipt.json").write_text(json.dumps(rep, indent=2) + "\n",
                                                              encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("lane", "format_gate")}, indent=2))
    print("format gate:", "PASS" if val["pass"] else f"FAIL {val['fails']}")
    print("sha256", rep["sha256"])
    return 0 if val["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
