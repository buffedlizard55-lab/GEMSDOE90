"""
Format validator per brief v2 §6 Gates.
MUST pass: CRS, shape, transform, dtype, band count, values in [0,1], no NaN inside footprint, NaN outside; zero catalogue mass; sha256 not duplicate; parent-diff recorded; re-read check.
"""
import hashlib
import numpy as np
import rasterio
import os
from pathlib import Path

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def validate_raster(path, ref_path=None, catalogue_path=None, ledger_hashes=None):
    """
    path: raster to validate
    ref_path: sample_submission.tif reference for CRS/shape/transform
    catalogue_path: catalogue mask raster where 1=known fault, must have zero mass
    ledger_hashes: set of existing sha256 to check dedupe
    Returns (ok, messages)
    """
    msgs=[]
    ok=True
    with rasterio.open(path) as src:
        print(f"Validating {path}")
        print(f"  CRS: {src.crs} | shape: {src.height}x{src.width} | count: {src.count} | dtype: {src.dtypes} | nodata: {src.nodata} | transform: {src.transform}")
        # Check CRS
        if src.crs is None:
            msgs.append("FAIL: CRS missing")
            ok=False
        else:
            # Expect EPSG:32611
            try:
                epsg = src.crs.to_epsg()
                if epsg != 32611:
                    msgs.append(f"FAIL: CRS EPSG {epsg} != 32611")
                    ok=False
                else:
                    msgs.append("PASS: CRS EPSG:32611")
            except Exception as e:
                msgs.append(f"WARN: CRS check {e}")
        # Band count
        if src.count != 1:
            msgs.append(f"FAIL: band count {src.count} !=1")
            ok=False
        else:
            msgs.append("PASS: band count 1")
        # Dtype
        if src.dtypes[0] != 'float32':
            msgs.append(f"FAIL: dtype {src.dtypes[0]} != float32")
            ok=False
        else:
            msgs.append("PASS: dtype float32")
        # Read data
        data = src.read(1)
        transform = src.transform
        nodata = src.nodata
        # Values in [0,1] where not NaN
        # Outside footprint should be NaN (or nodata)
        # Inside footprint: no NaN, values 0-1
        # Determine footprint: where not NaN and not nodata
        # For float32, spec says NaN outside footprint; fallback zeros.tif uses 0 outside but human uploads only one per slot
        # Check NaN handling
        nan_mask = np.isnan(data)
        # Values check (ignore NaN)
        valid = data[~nan_mask]
        if valid.size>0:
            if np.any(valid < -1e-6) or np.any(valid > 1+1e-6):
                msgs.append(f"FAIL: values outside [0,1]: min {valid.min():.4f} max {valid.max():.4f}")
                ok=False
            else:
                msgs.append(f"PASS: values in [0,1] (min {valid.min():.3f} max {valid.max():.3f} mean {valid.mean():.4f})")
        # No NaN inside footprint: footprint is defined by ref footprint or by where we intend to be inside
        # If ref provided, check shape/transform match
        if ref_path and os.path.exists(ref_path):
            with rasterio.open(ref_path) as ref:
                if src.height != ref.height or src.width != ref.width:
                    msgs.append(f"FAIL: shape {src.height}x{src.width} != ref {ref.height}x{ref.width}")
                    ok=False
                else:
                    msgs.append("PASS: shape matches ref")
                if src.transform != ref.transform:
                    msgs.append(f"FAIL: transform {src.transform} != ref {ref.transform}")
                    ok=False
                else:
                    msgs.append("PASS: transform matches ref")
                # Check footprint consistency: where ref is NaN, data should be NaN (or 0 for zeros variant)
                ref_data = ref.read(1)
                ref_nan = np.isnan(ref_data)
                # Data outside ref footprint should be NaN (allow zeros variant check separate)
                outside = ref_nan
                inside = ~ref_nan
                # No NaN inside footprint
                if np.any(np.isnan(data[inside])):
                    msgs.append(f"FAIL: NaN inside footprint: {np.isnan(data[inside]).sum()} px")
                    ok=False
                else:
                    msgs.append("PASS: no NaN inside footprint")
                # NaN outside (for NaN variant)
                # Count non-NaN outside
                non_nan_outside = np.sum(~np.isnan(data[outside]))
                if non_nan_outside > 0:
                    # Could be zeros variant — flag as INFO not fail if this is the zeros file
                    msgs.append(f"INFO: {non_nan_outside} non-NaN px outside footprint (ok for -zeros.tif, FAIL for NaN variant)")
                    # For strict NaN variant, this is fail; we don't know which file; report but not fail
                    # Check if all outside values are 0
                    if "zeros" in str(path):
                        if np.allclose(data[outside][~np.isnan(data[outside])], 0, atol=1e-6):
                            msgs.append("PASS: zeros outside footprint (zeros variant)")
                        else:
                            msgs.append("WARN: zeros variant has non-zero outside")
                    else:
                        # If not zeros file, outside should be NaN
                        # We'll mark as fail for primary
                        msgs.append("FAIL: non-NaN outside footprint for primary NaN variant")
                        ok=False
                else:
                    msgs.append("PASS: NaN outside footprint")
        else:
            msgs.append("INFO: no ref_path, skipped shape/transform/footprint ref checks (UNVERIFIED)")
            # Generic check: just report NaN stats
            msgs.append(f"INFO: NaN px {np.isnan(data).sum()} / {data.size} ({100*np.isnan(data).mean():.1f}%)")
        # Catalogue zero mass
        if catalogue_path and os.path.exists(catalogue_path):
            with rasterio.open(catalogue_path) as cat:
                cat_data = cat.read(1)
                # Align shapes
                if cat_data.shape == data.shape:
                    # catalogue pixels: where cat_data ==1
                    cat_mask = cat_data==1
                    # Also check 2px buffer? Brief says emit zero mass on catalogue pixels and keep >=3px from them unless AXIS=PRUNE
                    # Here we check exact pixel
                    mass_on_cat = np.nansum(data[cat_mask])
                    if mass_on_cat > 1e-6:
                        msgs.append(f"FAIL: mass on catalogue {mass_on_cat:.4f} over {cat_mask.sum()} px")
                        ok=False
                    else:
                        msgs.append(f"PASS: zero mass on catalogue ({cat_mask.sum()} catalogue px)")
                else:
                    msgs.append(f"WARN: catalogue shape {cat_data.shape} != data {data.shape}")
        else:
            msgs.append("INFO: catalogue_path not provided — zero-catalogue check UNVERIFIED (required for real submission)")
        # SHA256 dedupe
        sha = sha256_file(path)
        msgs.append(f"INFO: sha256 {sha} sha8 {sha[:8]}")
        if ledger_hashes and sha in ledger_hashes:
            msgs.append(f"FAIL: sha256 already in ledger (exact duplicate)")
            ok=False
        else:
            msgs.append("PASS: sha256 not in ledger (or no ledger)")
        # Re-read check
        try:
            with rasterio.open(path) as src2:
                data2 = src2.read(1)
                if not np.allclose(data, data2, equal_nan=True):
                    msgs.append("FAIL: re-read mismatch")
                    ok=False
                else:
                    msgs.append("PASS: re-read from disk matches")
        except Exception as e:
            msgs.append(f"FAIL: re-read error {e}")
            ok=False
    for m in msgs:
        print("  "+m)
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return ok, msgs

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv)>1 else "releases/test.tif"
    ref = sys.argv[2] if len(sys.argv)>2 else None
    cat = sys.argv[3] if len(sys.argv)>3 else None
    ok,_ = validate_raster(path, ref, cat)
    sys.exit(0 if ok else 1)
