import numpy as np, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.radedge import radiometric_surface, dotted_emission
from scripts.evaluate_holdout import make_holdout, score_pooled

def test_surface_range_and_catalogue_free():
    rng = np.random.default_rng(0)
    mask = np.ones((40, 40), bool)
    band = rng.random((40, 40)); band[:, 20:] += 2  # sharp contact edge
    s = radiometric_surface([band], mask)
    assert s.shape == band.shape and s.min() >= 0 and s.max() <= 1
    assert s[:, 19:22].mean() > s[:, :5].mean()  # edge lights up

def test_emission_separation_and_count():
    s = np.random.default_rng(1).random((60, 60)).astype(np.float32)
    dots = dotted_emission(s, np.ones_like(s, bool), 100, 2.8)
    assert dots.sum() == 100
    from scipy.ndimage import distance_transform_edt
    # no two dots closer than 2.8: check via distance transform trick on subset
    ys, xs = np.nonzero(dots)
    for i in range(len(ys)):
        d2 = (ys[i+1:]-ys[i])**2 + (xs[i+1:]-xs[i])**2
        assert (d2 >= 2.8**2 - 1e-9).all()

def test_holdout_whole_segments_and_scoring():
    cat = np.zeros((100, 200), bool); foot = np.ones_like(cat)
    cat[10:90, 20] = True; cat[10:90, 120] = True; cat[10:90, 60] = True; cat[10:90, 160] = True
    h = make_holdout(cat, foot, seed=1, block_px=50)
    assert not (h["visible"] & h["withheld"]).any()
    assert h["n_withheld_positives"] > 0
    dots = h["withheld"].copy()
    out = score_pooled({"truth_dots": dots, "empty": np.zeros_like(dots)}, h, n_boot=50, block_px=50)
    assert out["candidates"]["truth_dots"]["holdout_dti"] > out["candidates"]["empty"]["holdout_dti"]
