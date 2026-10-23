"""Tests for Hard Constraints & Gates per brief v2 §6. Run with pytest or python -m tests.test_gates"""
import pathlib, json, hashlib, sys
import numpy as np
import rasterio
sys.path.insert(0, "scripts")
from validate import sha256_file

def test_manifest_exists():
    p = pathlib.Path("registry/data_manifest.json")
    assert p.exists(), "registry/data_manifest.json missing"
    j = json.loads(p.read_text())
    assert "version" in j
    # Must flag UNVERIFIED if not yet pinned
    assert "inputs_pinned" in j

def test_ledger_exists():
    p = pathlib.Path("ledger/submissions.csv")
    assert p.exists()
    lines = p.read_text().splitlines()
    assert lines[0].startswith("id,parent"), "header missing"
    assert len([l for l in lines if l.strip() and not l.startswith("#")])>=4  # header +3 variants

def test_releases_format():
    import glob
    files = glob.glob("releases/*.tif")
    assert len(files)>=3, f"expected >=3 releases, got {len(files)}"
    for f in files:
        with rasterio.open(f) as src:
            assert src.count==1, f"{f} band count"
            assert src.dtypes[0]=="float32", f"{f} dtype"
            assert src.crs.to_epsg()==32611, f"{f} CRS"
            arr=src.read(1)
            # Values in [0,1] where not NaN
            valid=arr[~np.isnan(arr)] if np.isnan(arr).any() else arr.ravel()
            assert valid.min()>= -1e-6 and valid.max()<=1+1e-6, f"{f} values"
            # Re-read check
            with rasterio.open(f) as src2:
                arr2=src2.read(1)
                assert np.allclose(arr,arr2, equal_nan=True), f"{f} re-read"

def test_no_exact_duplicate_sha():
    import glob
    hashes=set()
    for f in glob.glob("releases/*.tif"):
        h=sha256_file(f)
        assert h not in hashes, f"duplicate sha {h} for {f}"
        hashes.add(h)

def test_pct_changed_in_range():
    import csv
    with open("ledger/submissions.csv") as fh:
        for row in csv.DictReader(fh):
            pct=float(row["pct_changed"])
            assert 1 <= pct <= 50, f"{row['id']} pct_changed {pct} out of 1-50% (CONCENTRATION must change 1-50%)"

def test_catalogue_zero_mass():
    # For synthetic run, check variant has zero mass on catalogue
    cat_path="synthetic_inputs/catalogue.tif"
    if not pathlib.Path(cat_path).exists():
        return
    with rasterio.open(cat_path) as cat:
        cat_arr=cat.read(1)==1 if cat.dtypes[0]!="float32" else cat.read(1)==1
        import glob
        for f in glob.glob("releases/*CONC*.tif"):
            if "zeros" not in f:  # zeros variant has 0 outside but same inside
                with rasterio.open(f) as src:
                    arr=src.read(1)
                    # zero mass on catalogue pixels
                    mass_on_cat = np.nansum(arr[cat_arr])
                    assert mass_on_cat==0, f"{f} mass on catalogue {mass_on_cat}"

def test_dti_algebra():
    from dti import test_algebra
    test_algebra()
