"""Unit tests for the emitter, the holdout evaluator and the submission writer."""
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from src import emit as emitmod
from src import holdout as hm
from src.metric import dti_terms
from src.submission_writer import validate_submission, write_submission


# ----------------------------------------------------------------- emitter --
def test_greedy_takes_the_densest_place_first():
    pi = np.zeros((40, 40), "float32")
    pi[10, 10] = 0.9          # isolated strong pixel
    pi[30, 30] = 0.1
    cand = np.ones((40, 40), bool)
    em = emitmod.greedy_emit(pi, cand, n_max=2)
    assert (em.rows[0], em.cols[0]) == (10, 10)


def test_greedy_spacing_adapts_to_density():
    """A confident line gets tight spacing; a faint line gets sparse spacing."""
    pi = np.zeros((60, 60), "float32")
    pi[10, 5:55] = 0.50
    pi[40, 5:55] = 0.01
    em = emitmod.greedy_emit(pi, np.ones((60, 60), bool), n_max=40)
    top = np.array(em.rows[:20])
    assert (top == 10).mean() > 0.9          # the strong line is served first
    strong = np.sort(np.array(em.cols)[np.array(em.rows) == 10])
    gaps = np.diff(strong)
    assert gaps.min() >= 1 and gaps.max() <= 4


def test_gains_are_non_increasing_and_curve_matches_algebra():
    rng = np.random.default_rng(0)
    pi = (rng.random((50, 50)) ** 4).astype("float32") * 0.2
    em = emitmod.greedy_emit(pi, np.ones((50, 50), bool), n_max=30)
    assert np.all(np.diff(em.gain) <= 1e-9)
    curve = emitmod.dti_curve(em, 100.0)
    n = 7
    den = 0.2 * em.cum_T[n - 1] + 0.2 * (n - em.cum_M[n - 1]) + 0.8 * 100.0
    assert curve[n - 1] == pytest.approx(em.cum_T[n - 1] / den)


def test_emitted_credit_matches_the_real_metric_on_a_known_truth():
    """cum_T is the exact coverage credit when pi is an indicator of the truth."""
    truth = np.zeros((40, 40), bool)
    truth[20, 5:35] = True
    pi = truth.astype("float32")
    em = emitmod.greedy_emit(pi, np.ones((40, 40), bool), n_max=12)
    pred = emitmod.dots_to_raster(em, (40, 40), 12)
    t = dti_terms(pred, truth, np.ones((40, 40), bool))
    assert t.tp_w == pytest.approx(float(em.cum_T[11]), abs=1e-6)


def test_overlap_cap_limits_duplicate_lane():
    pi = np.ones((40, 40), "float32") * 0.05
    guard = np.zeros((40, 40), bool)
    guard[:, :20] = True
    em = emitmod.greedy_emit(pi, np.ones((40, 40), bool), n_max=60,
                             forbid_within=guard, overlap_cap=0.5)
    share = guard[em.rows, em.cols].mean()
    assert share <= 0.51


# ----------------------------------------------------------------- holdout --
def _toy_catalogue():
    cat = np.zeros((300, 300), bool)
    cat[50, 20:60] = True          # segment A
    cat[150, 200:260] = True       # segment B
    cat[260, 40:90] = True         # segment C
    return cat


def test_folds_keep_whole_segments_together():
    cat = _toy_catalogue()
    inside = np.ones_like(cat)
    f = hm.make_folds(cat, inside, n_folds=3, block_px=100, seed=1)
    assert f.n_segments == 3
    for seg_rows in [(50, slice(20, 60)), (150, slice(200, 260)), (260, slice(40, 90))]:
        ids = np.unique(f.fold_id[seg_rows[0], seg_rows[1]])
        assert ids.size == 1 and ids[0] >= 0
    assert sum(f.seg_per_fold) == 3


def test_buffer_drops_truth_that_touches_a_visible_fault():
    cat = np.zeros((60, 60), bool)
    cat[30, 10:40] = True        # withheld
    cat[32, 10:40] = True        # visible, 2 px away
    inside = np.ones_like(cat)
    folds = hm.make_folds(cat, inside, n_folds=2, block_px=30, seed=0)
    folds.fold_id[:] = np.where(cat, 1, -1)
    folds.fold_id[30, 10:40] = 0
    vis, truth, scored = hm.fold_masks(folds, 0, inside, buffer_px=3.0, buffered=True)
    assert vis[32, 20] and not vis[30, 20]
    assert truth.sum() == 0                                   # all within 3 px of visible
    vis2, truth2, _ = hm.fold_masks(folds, 0, inside, buffer_px=0.0, buffered=False)
    assert truth2.sum() == 30
    assert not scored[32, 20]                                 # visible faults are masked out


def test_pooled_dti_equals_direct_dti_for_one_block():
    rng = np.random.default_rng(5)
    pred = (rng.random((40, 40)) < 0.06).astype(float)
    truth = rng.random((40, 40)) < 0.03
    scored = np.ones((40, 40), bool)
    block = np.zeros((40, 40), "int32")
    pb = hm.block_terms(pred, truth, scored, block)
    direct = dti_terms(pred, truth, scored)
    assert pb[0].dti == pytest.approx(direct.dti, abs=1e-9)
    ci = hm.pooled_dti_with_ci(pb, n_boot=20)
    assert ci["dti"] == pytest.approx(direct.dti, abs=1e-9)


def test_leakage_canary_detects_a_perfect_feature():
    truth = np.zeros((40, 40), bool)
    truth[10:15, 10:15] = True
    scored = np.ones((40, 40), bool)
    assert hm.leakage_auc(truth.astype(float), truth, scored) == pytest.approx(1.0)
    rng = np.random.default_rng(0)
    assert 0.4 < hm.leakage_auc(rng.random((40, 40)), truth, scored) < 0.75


# ------------------------------------------------------------------ writer --
def _toy_sample(tmp_path):
    p = tmp_path / "sample.tif"
    a = np.zeros((20, 20), "float32")
    a[5:15, 5:15] = 0.0
    a[:5, :] = np.nan
    prof = dict(driver="GTiff", height=20, width=20, count=1, dtype="float32",
                crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100),
                nodata=np.float32("nan"))
    with rasterio.open(p, "w", **prof) as ds:
        ds.write(a, 1)
    return p


def test_writer_emits_all_finite_file_and_validates(tmp_path):
    sample = _toy_sample(tmp_path)
    vals = np.zeros((20, 20), "float32")
    vals[10, 10] = 1.0
    rep = write_submission(vals, tmp_path / "cand.tif", sample, outside="zeros")
    assert rep["pass"] and rep["nonfinite_total"] == 0
    assert rep["min_inside"] >= 0.0 and rep["max_inside"] <= 1.0
    with rasterio.open(tmp_path / "cand.tif") as ds:
        assert ds.crs.to_epsg() == 32611 and ds.count == 1 and ds.dtypes[0] == "float32"


def test_writer_rejects_out_of_range_and_nan(tmp_path):
    sample = _toy_sample(tmp_path)
    bad = np.zeros((20, 20), "float32")
    bad[10, 10] = 1.5
    with pytest.raises(ValueError):
        write_submission(bad, tmp_path / "x.tif", sample)
    nan = np.zeros((20, 20), "float32")
    nan[10, 10] = np.nan
    with pytest.raises(ValueError):
        write_submission(nan, tmp_path / "y.tif", sample)


def test_validator_flags_nan_outside_for_the_upload_form(tmp_path):
    sample = _toy_sample(tmp_path)
    vals = np.zeros((20, 20), "float32")
    vals[10, 10] = 1.0
    write_submission(vals, tmp_path / "nanver.tif", sample, outside="nan")
    rep = validate_submission(tmp_path / "nanver.tif", sample, outside="zeros")
    assert not rep["pass"]
    assert any("non-finite" in f or "Predicted values" in f for f in rep["fails"])
