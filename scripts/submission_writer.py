#!/usr/bin/env python3
"""Shared submission writer: emit a float32 single-band GeoTIFF on the exact
sample grid, zeros outside the footprint (encoding that the organizer accepts:
values in [0,1] everywhere; the earlier 'Predicted values must be in range
[0, 1]' failure was caused by NaN outside the footprint), then re-open and run
src.validate. Never uploads anything."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import rasterio
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.validate import validate, footprint_mask


def write_submission(dots_or_values: np.ndarray, sample_path: str, out_path: str,
                     catalogue_path: str | None = None) -> dict:
    with rasterio.open(sample_path) as ref:
        profile = ref.profile.copy()
    inside = footprint_mask(sample_path)
    a = np.asarray(dots_or_values, dtype=np.float32)
    if a.shape != inside.shape:
        raise ValueError(f"shape {a.shape} != sample {inside.shape}")
    if not np.isfinite(a[inside]).all():
        raise ValueError("non-finite values inside footprint; refusing to clip blindly")
    if a[inside].min() < 0 or a[inside].max() > 1:
        raise ValueError(f"values outside [0,1] inside footprint: {a[inside].min()}..{a[inside].max()}")
    out = np.zeros(a.shape, dtype=np.float32)
    out[inside] = a[inside]
    profile.update(count=1, dtype="float32", nodata=0.0, compress="deflate")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as ds:
        ds.write(out, 1)
    report = validate(out_path, sample_path, catalogue_path, zeros_outside=True)
    return report
