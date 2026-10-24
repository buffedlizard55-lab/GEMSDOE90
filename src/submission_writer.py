"""Single submission writer + fail-closed format gate.

The DrivenData upload form rejects a file with *"Predicted values must be in
range [0, 1]"* when any pixel is NaN — NaN is not in [0, 1].  This writer
therefore defaults to the **all-finite encoding**: zeros outside the footprint,
finite values inside, exactly the sample grid.  It re-reads the file from disk
and re-validates before returning, and refuses to return a path that fails.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def footprint_mask(sample_path: str | Path) -> np.ndarray:
    with rasterio.open(sample_path) as ds:
        a = ds.read(1).astype("float64")
        inside = np.isfinite(a) & (ds.read_masks(1) > 0)
        if ds.nodata is not None and np.isfinite(ds.nodata):
            inside &= a != ds.nodata
    return inside


def write_submission(values: np.ndarray, out_path: str | Path, sample_path: str | Path,
                     outside: str = "zeros") -> dict:
    """Write a competition-format GeoTIFF and validate it from disk.

    values   float array on the sample grid, finite and in [0,1] inside the footprint
    outside  'zeros' (all-finite, what the upload form accepts) or 'nan'
    """
    if outside not in ("zeros", "nan"):
        raise ValueError("outside must be 'zeros' or 'nan'")
    with rasterio.open(sample_path) as ref:
        profile = ref.profile.copy()
        shape = (ref.height, ref.width)
    if tuple(np.shape(values)) != shape:
        raise ValueError(f"values shape {np.shape(values)} != sample grid {shape}")

    inside = footprint_mask(sample_path)
    arr = np.asarray(values, dtype="float32").copy()
    if not np.isfinite(arr[inside]).all():
        raise ValueError("non-finite value inside the footprint — refusing to write")
    if float(arr[inside].min()) < 0.0 or float(arr[inside].max()) > 1.0:
        raise ValueError("values outside [0,1] inside the footprint — refusing to write")
    arr[~inside] = 0.0 if outside == "zeros" else np.nan

    profile.update(dtype="float32", count=1, compress="deflate", zlevel=9,
                   predictor=3, tiled=False, nodata=(None if outside == "zeros" else np.float32("nan")))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(arr, 1)

    report = validate_submission(out_path, sample_path, outside=outside)
    if not report["pass"]:
        raise RuntimeError(f"written file failed its own format gate: {report['fails']}")
    report["sha256"] = sha256_file(out_path)
    report["bytes"] = out_path.stat().st_size
    return report


def validate_submission(path: str | Path, sample_path: str | Path,
                        outside: str = "zeros", catalogue_path: str | Path | None = None) -> dict:
    """Re-read a candidate from disk and check every upload requirement."""
    fails: list[str] = []
    with rasterio.open(sample_path) as ref:
        ref_crs, ref_tr, ref_shape = ref.crs, ref.transform, (ref.height, ref.width)
    with rasterio.open(path) as ds:
        if ds.count != 1:
            fails.append(f"band_count={ds.count} != 1")
        if str(ds.dtypes[0]) != "float32":
            fails.append(f"dtype={ds.dtypes[0]} != float32")
        if ds.crs != ref_crs:
            fails.append(f"crs={ds.crs} != {ref_crs}")
        if ds.crs is None or ds.crs.to_epsg() != 32611:
            fails.append(f"crs epsg={None if ds.crs is None else ds.crs.to_epsg()} != 32611")
        if (ds.height, ds.width) != ref_shape:
            fails.append(f"shape={(ds.height, ds.width)} != {ref_shape}")
        if ds.transform != ref_tr:
            fails.append("transform != sample transform")
        a = ds.read(1).astype("float64")

    inside = footprint_mask(sample_path)
    n_nan_in = int((~np.isfinite(a[inside])).sum())
    if n_nan_in:
        fails.append(f"{n_nan_in} non-finite pixels inside the footprint")
    fin = a[inside][np.isfinite(a[inside])]
    vmin = float(fin.min()) if fin.size else float("nan")
    vmax = float(fin.max()) if fin.size else float("nan")
    if fin.size and (vmin < 0.0 or vmax > 1.0):
        fails.append(f"values outside [0,1]: min={vmin} max={vmax}")
    out = a[~inside]
    n_nonfinite_total = int((~np.isfinite(a)).sum())
    if outside == "zeros":
        if not np.all(out == 0):
            fails.append("non-zero values outside the footprint")
        if n_nonfinite_total:
            fails.append(f"{n_nonfinite_total} non-finite pixels in the raster "
                         "(the upload form rejects NaN: 'Predicted values must be in range [0, 1]')")
    else:
        if not np.all(np.isnan(out)):
            fails.append("non-NaN values outside the footprint")

    cat_mass = None
    if catalogue_path is not None:
        with rasterio.open(catalogue_path) as ds:
            cat = ds.read(1) == 1
        cat_mass = float(np.nansum(a[cat]))

    return {"file": str(path), "pass": not fails, "fails": fails,
            "n_positive_inside": int((a[inside] > 0).sum()),
            "mass_inside": float(np.nansum(a[inside])),
            "min_inside": vmin, "max_inside": vmax,
            "nonfinite_total": n_nonfinite_total,
            "crs": "EPSG:32611", "shape": list(ref_shape),
            "catalogue_mass": cat_mass}


def write_receipt(report: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
