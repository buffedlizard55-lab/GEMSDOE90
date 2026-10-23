"""Format MUST-pass gate (brief s6): check a candidate raster against
sample_submission.tif -- CRS EPSG:32611, shape, transform, float32, 1 band,
values in [0,1], no NaN inside the footprint, NaN outside it; zero catalogue
mass when a catalogue raster is given. Re-reads the file from disk.

Usage: python -m src.validate CANDIDATE.tif SAMPLE.tif [--catalogue CAT.tif] [--zeros-outside]
Exit 0 = PASS, 1 = FAIL (reasons printed as JSON).
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import rasterio


def footprint_mask(sample_path: str) -> np.ndarray:
    """Inside-footprint = sample band is finite and not nodata."""
    with rasterio.open(sample_path) as ds:
        a = ds.read(1).astype("float64")
        inside = np.isfinite(a)
        if ds.nodata is not None and np.isfinite(ds.nodata):
            inside &= a != ds.nodata
    return inside


def validate(candidate: str, sample: str, catalogue: str | None = None, zeros_outside: bool = False) -> dict:
    fails: list[str] = []
    with rasterio.open(sample) as ref, rasterio.open(candidate) as ds:
        if ds.count != 1:
            fails.append(f"band_count={ds.count} != 1")
        if str(ds.dtypes[0]) != "float32":
            fails.append(f"dtype={ds.dtypes[0]} != float32")
        if ds.crs is None or ds.crs.to_epsg() != 32611:
            fails.append(f"crs={ds.crs} != EPSG:32611")
        if (ds.height, ds.width) != (ref.height, ref.width):
            fails.append(f"shape={(ds.height, ds.width)} != sample {(ref.height, ref.width)}")
        if ds.transform != ref.transform:
            fails.append("transform != sample transform")
        a = ds.read(1).astype("float64")

    inside = footprint_mask(sample)
    if a.shape != inside.shape:
        fails.append("array shape != footprint shape")
    else:
        if np.isnan(a[inside]).any():
            fails.append(f"NaN inside footprint: {int(np.isnan(a[inside]).sum())} px")
        finite_in = a[inside][np.isfinite(a[inside])]
        if finite_in.size and (finite_in.min() < 0 or finite_in.max() > 1):
            fails.append(f"values outside [0,1]: min={finite_in.min()} max={finite_in.max()}")
        outside = a[~inside]
        if zeros_outside:
            if not np.all(outside == 0):
                fails.append("non-zero outside footprint in -zeros fallback")
        elif not np.all(np.isnan(outside)):
            fails.append(f"non-NaN outside footprint: {int((~np.isnan(outside)).sum())} px")

    n_dots = int((a[inside] > 0).sum()) if a.shape == inside.shape else -1
    cat_mass = None
    if catalogue is not None:
        with rasterio.open(catalogue) as ds:
            cat = ds.read(1)
        if cat.shape != a.shape:
            fails.append("catalogue shape != candidate shape")
        else:
            cat_mass = float(np.nansum(a[cat > 0]))
            if cat_mass != 0.0:
                fails.append(f"catalogue mass = {cat_mass} != 0")

    return {"file": candidate, "pass": not fails, "fails": fails, "n_dots": n_dots, "catalogue_mass": cat_mass}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("sample")
    ap.add_argument("--catalogue")
    ap.add_argument("--zeros-outside", action="store_true")
    args = ap.parse_args()
    report = validate(args.candidate, args.sample, args.catalogue, args.zeros_outside)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["pass"] else 1)
