#!/usr/bin/env python3
"""Model-free inversion of |G| from spatially blind scored rasters.

A *blind* raster covers ground without knowing where the hidden faults are, so
its expected coverage credit is its mean coverage field times the number of
hidden-fault pixels, whatever the hidden faults look like:

    T = c_bar * |G|          c_bar = mean over the scored domain of
                              k(distance to that raster's nearest dot)

Substituting into the official identity DTI = T/(0.2T + 0.2(S-M) + 0.8|G|)
leaves one unknown, |G|.  `13gems…lattice-s5` is a uniform 5 px lattice over the
whole footprint (it covers 5,106,337 of 5,106,385 scored pixels), which makes it
the cleanest such probe available.  Every other scored raster then yields a
"lift" = implied T / blind-expectation T, i.e. how much better than chance its
dots were placed.

Scores are OWNER-REPORTED; no submission-page receipt is on file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.calibrate import REGISTRY, grids, CACHE  # noqa: E402


def main() -> int:
    inside, cat = grids()
    scored = inside & ~cat
    N = int(scored.sum())
    rows = []
    for name, rel, score in REGISTRY:
        with rasterio.open(CACHE / rel) as ds:
            a = ds.read(1).astype("float32")
        a = np.where(np.isfinite(a), a, 0.0)
        dots = (a > 0) & scored
        cov = np.maximum(0.0, 1.0 - distance_transform_edt(~dots) / 3.0)
        rows.append({"name": name, "path": rel, "score_owner_reported": score,
                     "n_dots_scored": int(dots.sum()),
                     "n_dots_on_catalogue": int(((a > 0) & cat).sum()),
                     "sum_coverage": float(cov[scored].sum()),
                     "mean_coverage": float(cov[scored].mean()),
                     "covered_px": int((cov[scored] > 0).sum())})
        print(f"  {name:13s} dots={rows[-1]['n_dots_scored']:7d} "
              f"c_bar={rows[-1]['mean_coverage']:.4f}", flush=True)

    lat = next(r for r in rows if r["name"] == "lattice_s5")

    def solve_G(cbar, S, s, m_frac):
        a = cbar - s * (0.2 * cbar - 0.2 * m_frac + 0.8)
        return 0.2 * s * S / a

    cbar, S, s = lat["mean_coverage"], lat["n_dots_scored"], lat["score_owner_reported"]
    gs = {f"M_eq_{m}G": solve_G(cbar, S, s, m) for m in (0.0, 0.112, 0.25)}
    G = solve_G(cbar, S, s, 0.112)
    rho = G / N
    for r in rows:
        y = 1.0 / r["score_owner_reported"] - 0.2
        T = (0.2 * r["n_dots_scored"] + 0.8 * G) / (y + 0.2 * 0.35)   # M ~ 0.35 T
        r["T_implied"] = T
        r["T_blind_expectation"] = rho * r["sum_coverage"]
        r["lift_vs_blind"] = T / max(r["T_blind_expectation"], 1e-9)
        r["credit_per_dot"] = T / max(r["n_dots_scored"], 1)
        r["share_of_available_credit"] = T / G

    out = {
        "note": "Owner-reported scores, not organizer receipts. |G| from the blind "
                "uniform-lattice probe; the 'placeholder' raster is the independent check.",
        "scored_domain_px": N, "catalogue_px": int(cat.sum()),
        "G_estimates": gs, "G_adopted": G, "global_density": rho,
        "break_even_credit_at_0.2778": 0.2 * 0.2778 / (1 - 0.2 * 0.2778),
        "files": rows,
    }
    (ROOT / "evidence" / "blind_probe_inversion.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "files"}, indent=2))
    print(f"\n{'file':14s} {'dots':>8s} {'obs':>7s} {'T_impl':>8s} {'lift':>6s} "
          f"{'cred/dot':>9s} {'T/|G|':>6s}")
    for r in rows:
        print(f"{r['name']:14s} {r['n_dots_scored']:8d} {r['score_owner_reported']:7.4f} "
              f"{r['T_implied']:8.0f} {r['lift_vs_blind']:6.2f} {r['credit_per_dot']:9.4f} "
              f"{r['share_of_available_credit']:6.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
