#!/usr/bin/env python3
"""E3 (final experiment in budget): catalogue-free multi-physics edge fusion.
Edge-persistence (src.radedge) computed independently on radiometric, magnetic,
gravity, strain and topo band groups of the raw stacks, rank-fused. No H19-5
or other scored raster is used as input. Fold-clean dotted emission, pooled
HOLDOUT-DTI vs the fold-clean H19-5 dotted baseline from build_radedge_experiment.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi
sys.path.insert(0, str(Path(__file__).resolve().parents[1])); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from src.radedge import radiometric_surface, dotted_emission, _rank01
from evaluate_holdout import make_holdout, score_pooled

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
N_DOTS = 37_654

def load(p, band=1):
    with rasterio.open(p) as ds: return ds.read(band)

def main():
    t0 = time.time()
    with rasterio.open(DATA / "sample_submission.tif") as ds: s = ds.read(1)
    foot = np.isfinite(s)
    with rasterio.open(DATA / "labels.tif") as ds: cat = ds.read(1) == 1
    groups = {}
    rad = [load(DATA / "external/geodawn_rad_u8.tif", b).astype(float) for b in (1, 2, 3, 4)]
    ext = [load(DATA / "external/geodawn_extensions_u8.tif", b).astype(float) for b in (1, 2, 3)]
    groups["radiometric"] = radiometric_surface(rad + ext, foot)
    tf = {}
    def tfb(b):
        if b not in tf:
            a = load(DATA / "training_features.tif", b).astype(np.float64)
            a[~np.isfinite(a) | (a < -1e30)] = 0.0; tf[b] = a
        return tf[b]
    groups["magnetic"] = radiometric_surface([tfb(3), tfb(6), tfb(9)], foot)   # tmi_hg, tc, tmi_vg
    groups["gravity"] = radiometric_surface([tfb(5), tfb(11), tfb(18)], foot)  # slope, vg, hg
    groups["strain"] = radiometric_surface([tfb(4), tfb(7), tfb(8)], foot)     # 2ndinv, shear, dilat
    groups["topo"] = radiometric_surface([tfb(12), tfb(19)], foot)             # det_elev, slope
    print({k: "done" for k in groups}, time.time() - t0, flush=True)
    fused = np.mean([_rank01(g, foot) for g in groups.values()], axis=0)
    surf = np.where(foot, fused, 0).astype(np.float32)
    np.save("/tmp/e3_surface.npy", surf)

    hold = make_holdout(cat, foot)
    dist_vis = ndi.distance_transform_edt(~hold["visible"])
    elig = foot & (dist_vis >= 3.0)
    dots_e3 = dotted_emission(surf, elig, N_DOTS, 2.8)
    h19 = load(DATA / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") > 0
    jitter = np.random.default_rng(20261024).random(foot.shape, dtype=np.float32)
    base_dots = dotted_emission(np.where(h19 & elig, 1.0 + 1e-3 * jitter, 0).astype(np.float32), elig & h19, N_DOTS, 2.8)
    out = score_pooled({"BASE_h19_dotted_foldclean": base_dots, "E3_multiphysics_fusion": dots_e3}, hold)
    res = {"experiment": "E3_multiphysics_edge_fusion", "holdout": out,
           "gate_pass_vs_baseline": out["candidates"]["E3_multiphysics_fusion"]["holdout_dti"] > out["candidates"]["BASE_h19_dotted_foldclean"]["holdout_dti"],
           "elapsed_s": round(time.time() - t0, 1)}
    (ROOT / "evidence/fusion_e3_experiment.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2), flush=True)

if __name__ == "__main__":
    main()
