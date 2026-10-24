#!/usr/bin/env python3
"""Where are the hidden faults?  A model-free inversion of the 14 scored rasters.

Write the hidden-fault occupancy field as

    pi(x) = rho_b(x) * [ (1-eta) + eta * w(x)/mean_b(w) ]      0 <= pi <= 1

`rho_b` is the mean hidden-fault density in distance-to-catalogue band b and the
bracket is a within-band reweighting by the hide-and-recover learner (w =
p_model), normalised to average 1 inside each band, so `eta` is literally "how
much does the learner's ranking help explain real scores" — eta = 0 means the
learner adds nothing beyond distance, eta = 1 means full strength.

Because coverage credit is linear in pi,

    T_j = sum_b rho_b [ (1-eta) C_jb + eta D_jb ]
    C_jb = sum_{x in b} c_j(x)          D_jb = sum_{x in b} c_j(x) w(x)/mean_b(w)

so for a fixed eta the design matrix is known exactly and rho follows from
non-negative least squares against the T implied by the owner-reported scores.
No gradient descent, no unphysical densities: rho is bounded in [0,1] and |G| is
an output, not an assumption.

T_j is recovered from the exact DTI identity
    T = s (0.2 S + 0.8 |G|) / (1 - 0.2 s + 0.2 s M/T)
with M computed by convolving the current field (self-consistent, 3 sweeps).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import convolve, distance_transform_edt
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.calibrate import grids, KPATCH, WORK, build_registry_cache  # noqa: E402

EDGES = [0.0, 1.5, 2.5, 3.5, 4.5, 6.0, 8.0, 11.0, 16.0, 25.0, 1e9]
NB = len(EDGES) - 1
ETAS = (0.0, 0.25, 0.5, 0.75, 1.0)


def main() -> int:
    inside, cat = grids()
    scored = inside & ~cat
    if not (WORK / "registry_meta.json").exists():
        build_registry_cache()
    meta = json.loads((WORK / "registry_meta.json").read_text())
    cov = np.asarray(np.load(WORK / "cov_registry.npy", mmap_mode="r"))
    obs = np.array([m["score_owner_reported"] for m in meta])
    S = np.array([m["n_dots_scored"] for m in meta], float)
    nf = len(meta)

    d_cat = distance_transform_edt(~cat).astype("float32")
    b_flat = np.digitize(d_cat[inside], EDGES[1:-1], right=False).astype("int8")
    sc_flat = scored[inside]
    w = np.load(WORK / "p_deploy.npy").astype("float64") * sc_flat

    N_b = np.array([float((sc_flat & (b_flat == b)).sum()) for b in range(NB)])
    C = np.zeros((nf, NB))
    D = np.zeros((nf, NB))
    vnorm = np.zeros_like(w)
    for b in range(NB):
        m = sc_flat & (b_flat == b)
        if not m.any():
            continue
        wb = w[m]
        mean_w = wb.mean() if wb.mean() > 0 else 1.0
        vnorm[m] = wb / mean_w
        C[:, b] = cov[:, m].sum(axis=1)
        D[:, b] = cov[:, m] @ (wb / mean_w)
        print(f"  band {b} d in [{EDGES[b]:.1f},{EDGES[b+1]:.1f}) px: "
              f"N={int(N_b[b]):8d}  mean_w={mean_w:.5f}", flush=True)

    dotidx = [np.load(WORK / f"dotidx_{m['name']}.npy") for m in meta]
    pi2d = np.zeros(inside.shape, "float32")

    def M_of(pi_flat: np.ndarray) -> np.ndarray:
        pi2d[:] = 0.0
        pi2d[inside] = pi_flat
        u = convolve(pi2d, KPATCH, mode="constant", cval=0.0)[inside]
        return np.array([float((1.0 - np.exp(-u[i])).sum()) for i in dotidx])

    best = None
    for eta in ETAS:
        A = (1.0 - eta) * C + eta * D
        rho = np.full(NB, 12545.0 / max(N_b.sum(), 1.0))
        fM = np.full(nf, 0.35)
        for sweep in range(4):
            G = float(rho @ N_b)
            T = obs * (0.2 * S + 0.8 * G) / (1.0 - 0.2 * obs + 0.2 * obs * fM)
            rho, _ = nnls(A, T)
            rho = np.minimum(rho, 1.0)
            G = float(rho @ N_b)
            pi_flat = (rho[b_flat] * ((1.0 - eta) + eta * vnorm)) * sc_flat
            pi_flat = np.minimum(pi_flat, 1.0)
            Mv = M_of(pi_flat)
            Tv = A @ rho
            fM = np.clip(Mv / np.maximum(Tv, 1e-9), 0.0, 0.95)
        pred = Tv / np.maximum(0.2 * Tv + 0.2 * (S - Mv) + 0.8 * G, 1e-9)
        rmse = float(np.sqrt(np.mean((pred - obs) ** 2)))
        loo = []
        for k in range(nf):
            keep = np.ones(nf, bool)
            keep[k] = False
            rk, _ = nnls(A[keep], T[keep])
            rk = np.minimum(rk, 1.0)
            Gk = float(rk @ N_b)
            Tk = A @ rk
            pk = Tk / np.maximum(0.2 * Tk + 0.2 * (S - fM * Tk) + 0.8 * Gk, 1e-9)
            loo.append(float(pk[k] - obs[k]))
        loo_rmse = float(np.sqrt(np.mean(np.square(loo))))
        print(f"eta={eta:4.2f}  |G|={G:8.0f}  rmse={rmse:.4f}  loo={loo_rmse:.4f}  "
              f"rho={np.round(rho, 5).tolist()}", flush=True)
        rec = {"eta": eta, "G": G, "rmse": rmse, "loo_rmse": loo_rmse, "rho": rho.tolist(),
               "pred": pred.tolist(), "T": Tv.tolist(), "M": Mv.tolist(),
               "pi_sum": float(pi_flat.sum()), "pi_max": float(pi_flat.max()),
               "pi_saturated": int((pi_flat >= 0.999).sum())}
        if best is None or loo_rmse < best["loo_rmse"]:
            best = rec
            np.save(WORK / "pi_band.npy", pi_flat.astype("float32"))

    out = {"model": "pi = rho_band * [(1-eta) + eta * w/mean_w]  (occupancy capped at 1)",
           "edges_px": EDGES, "band_px": N_b.tolist(),
           "eta_grid": [{k: r[k] for k in ("eta", "G", "rmse", "loo_rmse")}
                        for r in [best]] if best else [],
           "best": {k: v for k, v in best.items() if k != "pred"},
           "rho_by_band": [{"band": b, "d_lo_px": EDGES[b], "d_hi_px": EDGES[b + 1],
                            "n_px": int(N_b[b]), "rho": best["rho"][b],
                            "expected_truth_px": best["rho"][b] * N_b[b]}
                           for b in range(NB)],
           "observations": [{"name": m["name"], "n_dots": int(S[j]),
                             "score_owner_reported": float(obs[j]),
                             "predicted": float(best["pred"][j]),
                             "residual": float(best["pred"][j] - obs[j])}
                            for j, m in enumerate(meta)]}
    (ROOT / "evidence" / "band_profile.json").write_text(json.dumps(out, indent=2) + "\n",
                                                         encoding="utf-8")
    print("\nBEST", json.dumps({k: best[k] for k in ("eta", "G", "rmse", "loo_rmse",
                                                     "pi_sum", "pi_max", "pi_saturated")}, indent=1))
    print(f"\n{'band (px)':>14s} {'pixels':>9s} {'rho':>9s} {'truth px':>9s}")
    for r in out["rho_by_band"]:
        print(f"{r['d_lo_px']:6.1f}-{r['d_hi_px']:6.1f} {r['n_px']:9d} {r['rho']:9.5f} "
              f"{r['expected_truth_px']:9.0f}")
    print(f"\n{'file':14s} {'dots':>8s} {'observed':>9s} {'predicted':>10s} {'resid':>8s}")
    for o in out["observations"]:
        print(f"{o['name']:14s} {o['n_dots']:8d} {o['score_owner_reported']:9.4f} "
              f"{o['predicted']:10.4f} {o['residual']:+8.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
