"""Synthetic end-to-end tests: prune core, rebuild logic, format gate.
These use toy arrays only -- they are NOT competition data and prove nothing
about live scores (no PROXY claims)."""
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src.prune import distance_field, dots_of, drop_lowest_ranked, pct_changed, prune_le, refill, render
from src.validate import validate

CRS = "EPSG:32611"
TRANSFORM = from_origin(300000, 4500000, 100, 100)


def make_tif(path, array, nodata=np.nan):
    profile = dict(driver="GTiff", height=array.shape[0], width=array.shape[1],
                   count=1, dtype="float32", crs=CRS, transform=TRANSFORM, nodata=nodata)
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(array.astype("float32"), 1)
    return str(path)


@pytest.fixture()
def toy(tmp_path):
    cat = np.zeros((20, 20), dtype=int)
    cat[10, :] = 1  # catalogue line
    sample = np.zeros((20, 20), dtype=float)
    sample[:2, :] = np.nan  # outside footprint
    inside = np.isfinite(sample)
    return tmp_path, cat, make_tif(tmp_path / "sample.tif", sample), inside


def test_distance_and_prune_thresholds(toy):
    _, cat, _, _ = toy
    dist = distance_field(cat, "euclidean")
    assert dist[10, 5] == 0 and dist[12, 5] == 2 and dist[13, 5] == 3
    dots = {(11, 5), (12, 5), (13, 5), (18, 5)}
    assert prune_le(dots, dist, 1) == {(12, 5), (13, 5), (18, 5)}
    assert prune_le(dots, dist, 2) == {(13, 5), (18, 5)}
    assert prune_le(dots, dist, 3) == {(18, 5)}


def test_rebuild_r0_logic(toy):
    _, cat, _, _ = toy
    dist = distance_field(cat, "euclidean")
    pre = {(r, 5) for r in range(11, 19)}
    r0 = prune_le(pre, dist, 2)
    assert prune_le(pre, distance_field(cat, "euclidean"), 2) == r0  # exact reproduction
    assert (11, 5) not in r0 and (12, 5) not in r0 and (13, 5) in r0


def test_refill_and_drop_hold_count(toy):
    _, cat, _, inside = toy
    dist = distance_field(cat, "euclidean")
    ranked = [(18, 1, 1), (18, 2, 2), (11, 1, 3), (18, 3, 4)]  # (11,1) is dist 1
    out = refill({(18, 5)}, ranked, dist, 3, inside, target_n=3)
    assert out == {(18, 5), (18, 1), (18, 2)}
    ranked_all = [(18, 5, 1), (18, 1, 2), (18, 2, 3)]
    assert drop_lowest_ranked({(18, 5), (18, 1), (18, 2)}, ranked_all, 2) == {(18, 5), (18, 1)}
    with pytest.raises(ValueError):
        drop_lowest_ranked({(0, 0)}, ranked_all, 1)


def test_pct_changed_and_render(toy):
    _, _, _, inside = toy
    assert pct_changed({(5, 5)}, {(5, 5), (6, 5)}) == 50.0
    a = render({(5, 5)}, inside, outside_nan=True)
    assert a[5, 5] == 1.0 and np.isnan(a[0, 0]) and a.dtype == np.float32
    assert dots_of(a) == {(5, 5)}


def test_validate_pass_and_failures(toy):
    tmp, cat, sample, inside = toy
    cat_path = make_tif(tmp / "cat.tif", cat)
    good = render({(18, 5), (18, 6)}, inside, outside_nan=True)
    rep = validate(make_tif(tmp / "good.tif", good), sample, cat_path)
    assert rep["pass"] and rep["n_dots"] == 2 and rep["catalogue_mass"] == 0.0

    on_cat = render({(10, 5)}, inside, outside_nan=True)
    assert not validate(make_tif(tmp / "oncat.tif", on_cat), sample, cat_path)["pass"]

    nan_in = good.copy(); nan_in[15, 15] = np.nan
    assert not validate(make_tif(tmp / "nanin.tif", nan_in), sample)["pass"]

    too_big = good.copy(); too_big[15, 15] = 2.0
    assert not validate(make_tif(tmp / "big.tif", too_big), sample)["pass"]

    finite_out = good.copy(); finite_out[0, 0] = 0.0
    assert not validate(make_tif(tmp / "fout.tif", finite_out), sample)["pass"]
    # ...but the same all-zero-outside array passes as the -zeros fallback
    zeros = render({(18, 5)}, inside, outside_nan=False)
    assert validate(make_tif(tmp / "z.tif", zeros), sample, zeros_outside=True)["pass"]
