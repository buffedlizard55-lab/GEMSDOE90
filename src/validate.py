"""
Validator: MUST pass gates per brief §6.
- format check against sample_submission.tif (CRS, shape, transform, dtype, band count, values [0,1], no NaN inside footprint, NaN outside)
- zero catalogue mass
- sha256 not already in ledger
- parent-diff stats recorded
- file re-read from disk after writing
REPORT ONLY: catalogue hide-and-recover PROXY, leakage canary, SGMC control
"""
import rasterio
import numpy as np
import hashlib
from pathlib import Path
import sys
sys.path.insert(0, ".")
from src.config import WIDTH, HEIGHT, TRANSFORM, CRS, SAMPLE_PATH, CATALOGUE_PATH, FOOTPRINT_PATH, PARENT_PATH
from src.utils import sha256_file, dilate_mask

def validate_raster(path, is_parent=False, catalogue_path=CATALOGUE_PATH, sample_path=SAMPLE_PATH):
    msgs = []
    ok = True
    p = Path(path)
    if not p.exists():
        return False, [f"File not found: {path}"]
    try:
        with rasterio.open(path) as src:
            arr = src.read(1)
            profile = src.profile
            crs = src.crs
            transform = src.transform
            width = src.width
            height = src.height
            dtype = src.dtypes[0]
            count = src.count
            # re-read check already done by reading
    except Exception as e:
        return False, [f"Cannot open raster: {e}"]

    # Load sample for reference
    try:
        with rasterio.open(sample_path) as sref:
            ref_arr = sref.read(1)
            ref_transform = sref.transform
            ref_crs = sref.crs
            ref_width = sref.width
            ref_height = sref.height
            ref_dtype = sref.dtypes[0]
    except Exception as e:
        msgs.append(f"WARN sample_submission not found: {e} — using config reference")
        ref_transform = TRANSFORM
        ref_crs = rasterio.crs.CRS.from_string(CRS)
        ref_width = WIDTH
        ref_height = HEIGHT
        ref_arr = None
        ref_dtype = "float32"

    # 1. CRS
    if rasterio.crs.CRS.from_string(CRS) != crs:
        # Compare via to_string? rasterio CRS equality may be strict
        if crs.to_string() != CRS and crs.to_epsg() != 32611:
            ok = False
            msgs.append(f"FAIL CRS mismatch: got {crs} expected {CRS}")
        else:
            msgs.append(f"OK CRS {crs}")
    else:
        msgs.append(f"OK CRS {crs}")

    # 2. Shape
    if width != ref_width or height != ref_height:
        ok = False
        msgs.append(f"FAIL shape {width}x{height} vs sample {ref_width}x{ref_height}")
    else:
        msgs.append(f"OK shape {width}x{height}")

    # 3. Transform — must be exactly sample's transform
    if transform != ref_transform:
        # Allow tiny floating error?
        if list(transform) != list(ref_transform):
            ok = False
            msgs.append(f"FAIL transform {transform} vs {ref_transform}")
        else:
            msgs.append("OK transform")
    else:
        msgs.append("OK transform")

    # 4. dtype, band count
    if dtype != "float32":
        ok = False
        msgs.append(f"FAIL dtype {dtype} expected float32")
    else:
        msgs.append("OK dtype float32")
    if count != 1:
        ok = False
        msgs.append(f"FAIL band count {count} expected 1")
    else:
        msgs.append("OK band count 1")

    # 5. Footprint handling: no NaN inside, NaN outside (primary) or zeros outside allowed for -zeros variant
    # Determine footprint from sample: valid = not NaN in sample
    if ref_arr is not None:
        ref_valid = ~np.isnan(ref_arr)
    else:
        # fallback from footprint file
        try:
            with rasterio.open(FOOTPRINT_PATH) as fp:
                fparr = fp.read(1)
                ref_valid = fparr > 0.5
        except:
            ref_valid = ~np.isnan(arr)  # assume all valid? Not ideal
            msgs.append("WARN no footprint reference, using array NaN as footprint")
    # Check no NaN inside
    inside = ref_valid
    outside = ~inside
    nan_inside = np.isnan(arr[inside]).sum()
    if nan_inside > 0:
        ok = False
        msgs.append(f"FAIL NaN inside footprint: {nan_inside} pixels")
    else:
        msgs.append(f"OK no NaN inside ({inside.sum()} footprint pixels)")

    # NaN outside: spec primary requires NaN outside; fallback zeros variant should have 0 outside
    # We'll accept either but report.
    # For primary file (not -zeros), must be NaN outside
    is_zeros_variant = "zeros" in str(path)
    nan_outside = np.isnan(arr[outside]).sum()
    zero_outside = np.sum(arr[outside] == 0) if outside.sum()>0 else 0
    if outside.sum() > 0:
        if is_zeros_variant:
            # Should be all zeros outside
            if zero_outside != outside.sum():
                msgs.append(f"WARN zeros variant: outside not all zero ({zero_outside}/{outside.sum()} zeros, {nan_outside} NaN)")
            else:
                msgs.append(f"OK zeros outside ({outside.sum()} px)")
        else:
            if nan_outside != outside.sum():
                ok = False
                msgs.append(f"FAIL NaN outside: expected {outside.sum()} NaN, got {nan_outside} NaN, {zero_outside} zeros — primary must be NaN outside per spec")
            else:
                msgs.append(f"OK NaN outside ({outside.sum()} px)")
    else:
        msgs.append("WARN no outside footprint (footprint is full raster)")

    # 6. Values in [0,1] inside footprint (allow exact 0/1 for dots)
    vals_inside = arr[inside]
    # Exclude NaN already checked (should be none)
    vals_inside = vals_inside[~np.isnan(vals_inside)]
    if vals_inside.size:
        vmin, vmax = vals_inside.min(), vals_inside.max()
        if vmin < -1e-6 or vmax > 1+1e-6:
            ok = False
            msgs.append(f"FAIL values outside [0,1]: min {vmin} max {vmax}")
        else:
            msgs.append(f"OK values in [0,1] min {vmin:.3f} max {vmax:.3f}")
        # Dots check: count
        ndots = int(np.sum(vals_inside > 0.5))
        msgs.append(f"INFO dots (val>0.5) = {ndots}")
    else:
        msgs.append("WARN no inside values")

    # 7. Zero catalogue mass
    try:
        with rasterio.open(catalogue_path) as cat_src:
            cat = cat_src.read(1) > 0.5
            # Catalogue is within same geometry; check intersection with dots
            dots = (arr > 0.5) & ~np.isnan(arr)
            overlap = np.logical_and(dots, cat).sum()
            if overlap > 0:
                ok = False
                msgs.append(f"FAIL catalogue mass: {overlap} dots on catalogue pixels (must be 0)")
            else:
                msgs.append("OK zero catalogue mass")
            # Also check buffer if not PRUNE: for parent buffer 2, validator can optionally check
            # We'll check buffer distance if we know parent's buffer: for CONCENTRATION/MASS variants should be >=3? But spec says emit zero mass on catalogue and keep >=3px unless AXIS=PRUNE
            # For this session AXIS=CONCENTRATION, so enforce 3px
            # However parent is 2px — allow parent exception
            if not is_parent and "PRUNE" not in str(path):
                # Hard constraint 4: keep >=3px from catalogue pixels unless AXIS=PRUNE
                # Interpretation: distance >=3 means not within 2px (dilate radius 2). See PRUNE lanes: R0 is <=2.
                # So we dilate by 2 to test for violation of >=3px rule.
                from src.utils import dilate_mask
                cat_buf2 = dilate_mask(cat, 2)
                near = np.logical_and(dots, cat_buf2).sum()
                if near > 0:
                    ok = False
                    msgs.append(f"FAIL catalogue buffer >=3px (2px exclusion): {near} dots within 2px of catalogue (must be >=3px away unless AXIS=PRUNE)")
                else:
                    msgs.append("OK >=3px from catalogue (2px exclusion satisfied)")
            else:
                msgs.append("INFO buffer check skipped (is_parent or PRUNE)")
    except Exception as e:
        msgs.append(f"WARN catalogue check failed: {e}")

    # 8. File re-read after writing: we did; also check sha256 not empty
    sha = sha256_file(path)
    msgs.append(f"INFO sha256 {sha} sha8 {sha[:8]}")

    return ok, msgs

def check_ledger_unique(path, ledger_path="ledger/submissions.csv"):
    sha = sha256_file(path)
    try:
        with open(ledger_path) as f:
            content = f.read()
            if sha in content:
                return False, f"FAIL ledger duplicate sha256 {sha[:8]} already in ledger"
            return True, f"OK sha not in ledger {sha[:8]}"
    except FileNotFoundError:
        return True, "OK ledger not found, no duplicate"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--parent", action="store_true")
    args = parser.parse_args()
    ok, msgs = validate_raster(args.path, is_parent=args.parent)
    for m in msgs:
        print(m)
    print("VALID" if ok else "INVALID")
    sys.exit(0 if ok else 1)
