"""Feature stack for the 2026-10-24 H1 lane (see docs/HYPOTHESES_20261024.md).

Every layer comes from a SHA-256-pinned input in ``registry/data_manifest.json``:
the 19 competition bands, the 12-band USGS-3DEP lidar-scarp stack, and the
GeoDAWN radiometric + extension (ratios / upward-continued TMI) stacks.
Plus label-agnostic derivatives (gradient magnitude, |Laplacian|, 3 px-smoothed
ridges, magnetic high-pass).  **No catalogue-derived feature is built here**:
no distance-to-catalogue, no catalogue density -- so the stack itself cannot
leak the withheld faults in the blocked holdout.  Sentinel/nodata handling:
values <= -1e30 or non-finite (and 0 where a GeoTIFF declares nodata=0) become
NaN, then each band is median-filled inside the footprint *before* any filter;
the fill value is a label-agnostic global median, recorded in the run receipt.
The stack is written once to a float32 memmap under ``.cache/lane90/`` so the
5-fold training/prediction can stream row chunks instead of holding 51 full
float64 planes in RAM.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
CACHE = ROOT / ".cache" / "lane90"
STACK_PATH = CACHE / "features_f32.dat"
NAMES_PATH = CACHE / "features_names.json"


def _clean(band: np.ndarray, foot: np.ndarray, zero_is_nodata: bool = False) -> tuple[np.ndarray, float]:
    a = np.asarray(band, dtype=np.float64)
    bad = ~np.isfinite(a) | (a <= -1e30)
    if zero_is_nodata:
        bad |= a == 0
    vals = a[foot & ~bad]
    fill = float(np.median(vals)) if vals.size else 0.0
    out = np.where(bad, fill, a).astype(np.float32)
    return out, fill


def _gradmag(a: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    s = ndi.gaussian_filter(a.astype(np.float32), sigma=sigma, mode="nearest")
    gy, gx = np.gradient(s)
    return np.hypot(gx, gy).astype(np.float32)


def build_stack(force: bool = False) -> tuple[np.ndarray, list[str], list[float]]:
    """Return (memmap (n_feat, H, W) float32, names, fill values). Builds if absent."""
    import json

    with rasterio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        shape = (ds.height, ds.width)

    if STACK_PATH.is_file() and NAMES_PATH.is_file() and not force:
        meta = json.loads(NAMES_PATH.read_text())
        names, fills = meta["names"], meta["fills"]
        mm = np.memmap(STACK_PATH, dtype=np.float32, mode="r", shape=(len(names), *shape))
        return mm, names, fills

    feats: list[tuple[str, np.ndarray, float]] = []

    def add(name: str, arr: np.ndarray, fill: float = 0.0) -> None:
        feats.append((name, np.asarray(arr, dtype=np.float32), float(fill)))

    with rasterio.open(DATA / "training_features.tif") as ds:
        descs = list(ds.descriptions)
        raw: dict[int, np.ndarray] = {}
        for b in range(1, 20):
            name = (descs[b - 1] or f"band_{b}").split(" - ")[0].strip()
            clean, fill = _clean(ds.read(b), foot)
            raw[b] = clean
            add(f"feat_{name}", clean, fill)
        # Derivatives (label-agnostic). Band key: 2 rtp, 3 tmi_hg, 12 det_elev,
        # 13 iso_grav_anom, 14 tmi, 15 depth_to_base_surf, 17 cond_surf,
        # 18 iso_grav_anom_hg, 19 det_elev_slope.
        for b, tag in ((14, "tmi"), (2, "rtp"), (13, "grav"), (15, "basement"), (12, "detelev"), (17, "cond")):
            add(f"grad_{tag}", _gradmag(raw[b]))
        for b, tag in ((15, "basement"), (14, "tmi")):
            add(f"lapabs_{tag}", np.abs(ndi.laplace(ndi.gaussian_filter(raw[b], 1.0, mode="nearest"))))
        for b, tag in ((3, "tmi_hg"), (19, "detelev_slope"), (18, "grav_hg")):
            add(f"smooth3_{tag}", ndi.gaussian_filter(raw[b], 3.0, mode="nearest"))
        hp = raw[14] - ndi.gaussian_filter(raw[14], 3.0, mode="nearest")
        add("grad_tmi_highpass", _gradmag(hp, sigma=0.5))

    with rasterio.open(DATA / "external" / "lidar_scarp_features_u8.tif") as ds:
        valid = ds.read(12) > 0
        for b in range(1, 12):
            name = (ds.descriptions[b - 1] or f"lidar_{b}").strip()
            clean, fill = _clean(ds.read(b), foot & valid, zero_is_nodata=False)
            clean = np.where(valid, clean, fill).astype(np.float32)
            add(f"lidar_{name}", clean, fill)
        add("lidar_valid", valid.astype(np.float32))

    for fname, prefix in (("geodawn_rad_u8.tif", "rad"), ("geodawn_extensions_u8.tif", "radext")):
        with rasterio.open(DATA / "external" / fname) as ds:
            for b in range(1, ds.count + 1):
                name = (ds.descriptions[b - 1] or f"{prefix}_{b}").strip()
                clean, fill = _clean(ds.read(b), foot, zero_is_nodata=True)
                add(f"{prefix}_{name}", clean, fill)

    CACHE.mkdir(parents=True, exist_ok=True)
    names = [n for n, _, _ in feats]
    fills = [f for _, _, f in feats]
    mm = np.memmap(STACK_PATH, dtype=np.float32, mode="w+", shape=(len(names), *shape))
    for i, (_, arr, _) in enumerate(feats):
        mm[i] = arr
    mm.flush()
    NAMES_PATH.write_text(__import__("json").dumps({"names": names, "fills": fills}, indent=2) + "\n")
    return np.memmap(STACK_PATH, dtype=np.float32, mode="r", shape=(len(names), *shape)), names, fills


RANK_PATH = CACHE / "features_rank_u8.npy"


def build_rank_u8(force: bool = False) -> tuple[np.ndarray, list[str]]:
    """Per-band percentile-rank uint8 copy of the float stack, loaded into RAM.

    The sandbox has ~3 GB RAM; the float32 stack is 2.5 GB on disk and thrashes
    as a memmap.  Rank-quantising each band to 256 levels (627 MB) is a strictly
    monotone per-feature transform, so tree-based models (and ROC-AUC up to
    ties) see the same ordering information.  Ranks are computed over footprint
    pixels only, one band at a time.
    """
    stack, names, _ = build_stack()
    if RANK_PATH.is_file() and not force:
        return np.load(RANK_PATH), names
    import rasterio as _rio

    with _rio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    ys, xs = np.nonzero(foot)
    out = np.zeros(stack.shape, dtype=np.uint8)
    for i in range(stack.shape[0]):
        vals = stack[i][ys, xs].astype(np.float32)
        order = np.argsort(vals, kind="stable")
        ranks = np.empty(vals.size, dtype=np.float64)
        ranks[order] = np.arange(vals.size)
        out[i][ys, xs] = (ranks / max(vals.size - 1, 1) * 255).astype(np.uint8)
    np.save(RANK_PATH, out)
    return out, names


def load_masks() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """(footprint, catalogue, h19_5 support, sample profile)."""
    with rasterio.open(DATA / "sample_submission.tif") as ds:
        profile = ds.profile.copy()
        foot = np.isfinite(ds.read(1))
    with rasterio.open(DATA / "existing_faults.tif") as ds:
        cat = (ds.read(1) > 0) & foot
    with rasterio.open(
        DATA / "scored" / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
    ) as ds:
        a = ds.read(1)
        h19 = foot & np.isfinite(a) & (a > 0.5)
    return foot, cat, h19, profile
