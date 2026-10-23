import hashlib
import numpy as np
import rasterio
from pathlib import Path

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha8(path):
    return sha256_file(path)[:8]

def ensure_dir(p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)

def read_raster(path):
    with rasterio.open(path) as src:
        arr = src.read(1)
        profile = src.profile
        transform = src.transform
        crs = src.crs
    return arr, profile, transform, crs

def write_raster(path, arr, profile=None, transform=None, crs=None, nodata_outside="nan"):
    """
    nodata_outside: "nan" writes NaN outside footprint (spec primary),
                    "zero" writes 0 outside (fallback)
    arr is float32 with NaN outside.
    """
    from src.config import WIDTH, HEIGHT, TRANSFORM, CRS, DTYPE
    if profile is None:
        import rasterio
        profile = {
            "driver": "GTiff",
            "dtype": DTYPE,
            "width": WIDTH,
            "height": HEIGHT,
            "count": 1,
            "crs": CRS,
            "transform": TRANSFORM,
            "compress": "deflate",
            "tiled": False,
        }
    # Ensure float32
    arr = arr.astype(np.float32)
    if nodata_outside == "zero":
        out = np.where(np.isnan(arr), 0, arr).astype(np.float32)
        # rasterio will store 0 outside; keep nodata None to avoid confusion but 0 is valid inside too
        # For zeros variant we do NOT set nodata, values are in [0,1]
        profile["nodata"] = None
    else:
        out = arr  # NaN preserved
        profile["nodata"] = None  # NaN is implicit
    ensure_dir(path)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(out, 1)
    return path

def dilate_mask(mask, radius_px):
    """Binary dilation by radius (Chebyshev / max-norm) — approximates circular for small R."""
    from scipy.ndimage import binary_dilation
    if radius_px <= 0:
        return mask
    struct = np.ones((2*radius_px+1, 2*radius_px+1), dtype=bool)
    return binary_dilation(mask, structure=struct)

def footprint_valid_mask(arr):
    """Inside footprint = not NaN and not outside-mask sentinel."""
    return ~np.isnan(arr)

def count_dots(arr):
    """Dots are pixels ==1 inside footprint (value in [0,1], unit-mass dots =1)."""
    mask = footprint_valid_mask(arr)
    return int(np.sum((arr[mask] > 0.5)))

def parent_diff_stats(parent_arr, variant_arr):
    mask = footprint_valid_mask(parent_arr)  # same footprint
    # dots as bool
    p = (parent_arr > 0.5) & mask
    v = (variant_arr > 0.5) & mask
    n_parent = int(p.sum())
    n_variant = int(v.sum())
    intersection = int((p & v).sum())
    changed = n_parent - intersection + (n_variant - intersection)  # symmetric diff but counts same?
    # % changed relative to parent = (dots removed + dots added)/ n_parent *100? For fixed count = 2*removed/n_parent?
    # Brief: "record the exact percentage" — interpret as % of R0's dots that moved/changed.
    # For fixed-count variants, %changed = 100 * (n_parent - intersection)/n_parent
    # For mass variants with different count, %changed = 100*|n_parent - n_variant| + moved?
    # Use definition: % changed = 100 * (1 - Jaccard? Or symmetric diff /2 / n_parent)
    # Simplest: % moved = 100 * (n_parent - intersection)/ n_parent
    pct_changed = 100.0 * (n_parent - intersection) / n_parent if n_parent else 0
    # Alternative symmetric: 100*changed/(n_parent) but double counts? We'll report moved pct.
    # Also compute Jaccard
    union = int((p | v).sum())
    jaccard = intersection / union if union else 1.0
    return {
        "n_parent": n_parent,
        "n_variant": n_variant,
        "intersection": intersection,
        "union": union,
        "pct_changed": pct_changed,
        "jaccard": jaccard,
        "dots_added": int((v & ~p).sum()),
        "dots_removed": int((p & ~v).sum()),
    }
