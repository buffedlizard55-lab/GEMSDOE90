import numpy as np, rasterio
from rasterio.transform import from_origin
COLS, ROWS = 2000, 2585
TRANSFORM = from_origin(360000, 4450000, 100, 100)
CRS="EPSG:32611"
# load footprint from synthetic_inputs
import pathlib
# Recreate footprint same as build script to avoid circular reading
# Instead read from footprint.tif we saved (contains 255 inside)
with rasterio.open("synthetic_inputs/footprint.tif") as src:
    fp = src.read(1)==255
# Create sample_submission: 0 inside, NaN outside
ref = np.where(fp, 0, np.nan).astype(np.float32)
with rasterio.open("synthetic_inputs/sample_submission.tif", 'w', driver='GTiff', height=ROWS, width=COLS, count=1, dtype='float32', crs=CRS, transform=TRANSFORM, nodata=np.nan, compress='lzw') as dst:
    dst.write(ref,1)
print("Wrote synthetic_inputs/sample_submission.tif")

# Validate again with ref+catalogue
import sys
sys.path.insert(0,'scripts')
from validate import validate_raster
import glob
# catalogue already exists
cat_path="synthetic_inputs/catalogue.tif"
ref_path="synthetic_inputs/sample_submission.tif"
ok_all=True
for p in sorted(glob.glob("releases/*.tif")):
    if "zeros" in p:
        # zeros variant expects 0 outside, so we need to allow that — validator INFO not FAIL for zeros, but we need to adjust check: for zeros file, outside 0 is PASS
        pass
    print(f"\n=== VALIDATE {p} with ref ===")
    ok,_ = validate_raster(p, ref_path=ref_path, catalogue_path=cat_path, ledger_hashes=None)
    ok_all &= ok
print("OVERALL", "PASS" if ok_all else "FAIL")
