"""Feature stack for hidden-fault discovery.

Two strictly separated groups:

* `static_features`  — geophysics, radiometrics, lidar-scarp morphometry and
  third-party point data.  None of them touches the competition fault
  catalogue, so they are identical in every holdout fold (no leakage path).
* `catalogue_features` — everything derived from mapped faults.  It takes the
  *visible* fault mask as an argument and is therefore recomputed from scratch
  in every fold, which is what makes the hide-and-recover holdout honest.

All rasters are returned as 2-D float32 on the competition grid
(3730 x 3292, EPSG:32611, 100 m).
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import (convolve, distance_transform_edt, gaussian_filter,
                           maximum_filter, minimum_filter, sobel, uniform_filter)

CACHE = Path(".cache/gems_data")


def _read(path: Path, band: int = 1) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(band).astype("float32")
        nod = ds.nodata
    if nod is not None and np.isfinite(nod):
        a = np.where(a == nod, np.nan, a)
    return a


def _grad_mag(a: np.ndarray) -> np.ndarray:
    a = np.nan_to_num(a, nan=0.0)
    return np.hypot(sobel(a, 0, mode="nearest"), sobel(a, 1, mode="nearest")).astype("float32")


def _local_relief(a: np.ndarray, size: int) -> np.ndarray:
    a = np.nan_to_num(a, nan=0.0)
    return (maximum_filter(a, size=size, mode="nearest")
            - minimum_filter(a, size=size, mode="nearest")).astype("float32")


def static_features(cache: Path = CACHE) -> tuple[list[str], list[np.ndarray]]:
    names: list[str] = []
    arrs: list[np.ndarray] = []

    with rasterio.open(cache / "training_features.tif") as ds:
        descs = [d.split(" - ")[0] if d else f"b{i+1}" for i, d in enumerate(ds.descriptions)]
        nod = ds.nodata
        for i, nm in enumerate(descs):
            a = ds.read(i + 1).astype("float32")
            if nod is not None:
                a = np.where(a == nod, np.nan, a)
            names.append(f"gd_{nm}")
            arrs.append(a)

    # derived edge / roughness transforms on the most structure-bearing bands
    by = {n: a for n, a in zip(names, arrs)}
    for src, tag in [("gd_rtp", "rtp"), ("gd_iso_grav_anom", "grav"),
                     ("gd_det_elev", "dem"), ("gd_depth_to_base_surf", "dbs"),
                     ("gd_cond_surf", "cond")]:
        if src in by:
            names.append(f"grad_{tag}")
            arrs.append(_grad_mag(by[src]))
    if "gd_det_elev" in by:
        names.append("relief_7")
        arrs.append(_local_relief(by["gd_det_elev"], 7))
        names.append("relief_21")
        arrs.append(_local_relief(by["gd_det_elev"], 21))

    for fname, prefix in [("lidar_scarp_features_u8.tif", "lid"),
                          ("geodawn_rad_u8.tif", "rad"),
                          ("geodawn_extensions_u8.tif", "ext")]:
        p = cache / "external" / fname
        with rasterio.open(p) as ds:
            for i, d in enumerate(ds.descriptions):
                names.append(f"{prefix}_{d or i+1}")
                arrs.append(ds.read(i + 1).astype("float32"))

    # SGMC geologic-map faults: an independent fault compilation
    sgmc = _read(cache / "external" / "derived_sgmc_faults_100m_u8.tif") > 0
    names.append("sgmc_dist")
    arrs.append(distance_transform_edt(~sgmc).astype("float32"))
    names.append("sgmc_den_25")
    arrs.append(uniform_filter(sgmc.astype("float32"), 25, mode="nearest"))

    # GDR 1391 thermal wells / springs (CC BY 4.0) — label-derived columns unused
    shape = arrs[0].shape
    hot = np.zeros(shape, "float32")
    allpt = np.zeros(shape, "float32")
    tmax = np.zeros(shape, "float32")
    with (cache / "external" / "gdr_wellspring_in_footprint.csv").open() as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(row["row"]), int(row["col"])
            except (TypeError, ValueError):
                continue
            if not (0 <= r < shape[0] and 0 <= c < shape[1]):
                continue
            allpt[r, c] += 1.0
            try:
                t = float(row["temp_c"])
            except (TypeError, ValueError):
                t = np.nan
            if np.isfinite(t):
                tmax[r, c] = max(tmax[r, c], t)
                if t >= 37.0:
                    hot[r, c] += 1.0
    names.append("well_den")
    arrs.append(gaussian_filter(allpt, 25.0).astype("float32"))
    names.append("hotwell_den")
    arrs.append(gaussian_filter(hot, 25.0).astype("float32"))
    names.append("hotwell_dist")
    arrs.append(distance_transform_edt(hot == 0).astype("float32"))
    names.append("wel_tmax_sm")
    arrs.append(gaussian_filter(tmax, 15.0).astype("float32"))

    # INGENIOUS Quaternary-fault trace attributes (centroids only in the mirror)
    qs = np.zeros(shape, "float32")
    with (cache / "external" / "gdr_qfaults_traces.csv").open() as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(row["centroid_row"]), int(row["centroid_col"])
                sr = float(row["slip_rate"]) if row["slip_rate"] else 0.0
            except (TypeError, ValueError):
                continue
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                qs[r, c] += max(sr, 0.0)
    names.append("qfault_sliprate_den")
    arrs.append(gaussian_filter(qs, 40.0).astype("float32"))

    vents = np.zeros(shape, "float32")
    with (cache / "external" / "gdr_volcanic_vents_in_footprint.csv").open() as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(row["row"]), int(row["col"])
            except (TypeError, ValueError):
                continue
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                vents[r, c] = 1.0
    names.append("vent_dist")
    arrs.append(distance_transform_edt(vents == 0).astype("float32"))
    return names, arrs


def orientation(visible: np.ndarray, sigma: float = 3.0) -> np.ndarray:
    """Local strike (radians) of the mapped fault network via the structure tensor."""
    f = gaussian_filter(visible.astype("float32"), sigma)
    ix = sobel(f, 1, mode="nearest")
    iy = sobel(f, 0, mode="nearest")
    jxx = gaussian_filter(ix * ix, sigma)
    jyy = gaussian_filter(iy * iy, sigma)
    jxy = gaussian_filter(ix * iy, sigma)
    # principal gradient direction; the line runs perpendicular to it
    theta_grad = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    return (theta_grad + np.pi / 2).astype("float32")


def tip_continuation(visible: np.ndarray, reach: int = 35, decay: float = 18.0,
                     min_seg_px: int = 4) -> tuple[np.ndarray, np.ndarray]:
    """(corridor, tip_distance) beyond the ends of mapped fault segments.

    A newly mapped fault is frequently the along-strike continuation of a trace
    that the catalogue stops short of; this marks the ground just past each tip,
    inside a +-1.5 px smoothed corridor that decays with distance.
    """
    from scipy.ndimage import label as nd_label

    vis = np.asarray(visible, dtype=bool)
    nbr = convolve(vis.astype("uint8"), np.ones((3, 3), "uint8"), mode="constant")
    lab, n = nd_label(vis, structure=np.ones((3, 3), int))
    sizes = np.bincount(lab.ravel())
    big = sizes >= min_seg_px
    tips = vis & (nbr <= 2) & big[lab]
    th = orientation(vis)
    corridor = np.zeros(vis.shape, "float32")
    h, w = vis.shape
    tr, tc = np.nonzero(tips)
    for r, c in zip(tr, tc):
        a = float(th[r, c])
        for sgn in (1.0, -1.0):
            dy, dx = -sgn * np.sin(a), sgn * np.cos(a)
            for s in range(1, reach + 1):
                rr, cc = int(round(r + dy * s)), int(round(c + dx * s))
                if not (0 <= rr < h and 0 <= cc < w) or vis[rr, cc]:
                    break
                v = float(np.exp(-s / decay))
                if v > corridor[rr, cc]:
                    corridor[rr, cc] = v
    corridor = gaussian_filter(corridor, 1.2)
    d_tip = distance_transform_edt(~tips).astype("float32")
    return corridor.astype("float32"), d_tip


def catalogue_features(visible: np.ndarray) -> tuple[list[str], list[np.ndarray]]:
    """Every feature derived from mapped faults — rebuilt per fold from `visible`."""
    vis = np.asarray(visible, dtype=bool)
    d_cat = distance_transform_edt(~vis).astype("float32")
    corridor, d_tip = tip_continuation(vis)
    th = orientation(vis)
    names = ["cat_dist", "cat_logdist", "cat_tip_dist", "cat_corridor",
             "cat_den_25", "cat_den_75", "cat_den_151", "cat_strike_sin", "cat_strike_cos"]
    arrs = [d_cat,
            np.log1p(d_cat).astype("float32"),
            d_tip,
            corridor,
            uniform_filter(vis.astype("float32"), 25, mode="nearest"),
            uniform_filter(vis.astype("float32"), 75, mode="nearest"),
            uniform_filter(vis.astype("float32"), 151, mode="nearest"),
            np.sin(2 * th).astype("float32"),
            np.cos(2 * th).astype("float32")]
    return names, arrs
