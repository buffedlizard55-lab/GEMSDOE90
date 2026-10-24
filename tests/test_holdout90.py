"""Unit tests for the 2026-10-24 H1 lane: holdout DTI identity + emission."""
import numpy as np
import pytest

from src.dti import components_from_arrays, dti_from_components
from src.emission90 import poisson_emit
from src.holdout import (
    auc_rank,
    binary_components,
    block_components,
    dot_overlap_within,
    make_blocks,
    pooled_dti,
)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_binary_components_matches_reference(seed):
    rng = np.random.default_rng(seed)
    dots = rng.random((60, 70)) < 0.02
    truth = rng.random((60, 70)) < 0.02
    T, S, M, G = binary_components(dots, truth)
    T2, S2, M2 = components_from_arrays(dots.astype(float), truth.astype(int))
    assert T == pytest.approx(T2, abs=1e-9)
    assert S == pytest.approx(S2)
    assert M == pytest.approx(M2, abs=1e-9)
    assert G == int(truth.sum())


def test_block_components_pool_to_binary():
    rng = np.random.default_rng(7)
    dots = rng.random((80, 90)) < 0.03
    truth = rng.random((80, 90)) < 0.03
    block_id, fold = make_blocks((80, 90), block_px=25, n_folds=5, seed=3)
    comp = block_components(dots, truth, block_id)
    T, S, M, G = binary_components(dots, truth)
    assert comp["T"].sum() == pytest.approx(T, abs=1e-9)
    assert comp["S"].sum() == S and comp["G"].sum() == G
    assert pooled_dti(comp) == pytest.approx(dti_from_components(T, S, M, G))
    assert set(np.unique(fold)) <= set(range(5))


def test_auc_and_overlap():
    assert auc_rank(np.array([0.1, 0.9]), np.array([False, True])) == 1.0
    assert auc_rank(np.array([0.9, 0.1]), np.array([False, True])) == 0.0
    a = np.zeros((10, 10), dtype=bool); a[5, 5] = True
    b = np.zeros((10, 10), dtype=bool); b[5, 7] = True
    assert dot_overlap_within(a, b, px=3.0) == 1.0
    assert dot_overlap_within(a, b, px=1.0) == 0.0


def test_poisson_emit_separation_and_budget():
    rng = np.random.default_rng(11)
    score = rng.random((120, 120))
    dots = poisson_emit(score, np.ones_like(score, dtype=bool), n_target=300, min_sep=2.8)
    assert int(dots.sum()) == 300
    ys, xs = np.nonzero(dots)
    # brute-force min pairwise distance on a subsample grid check via dilation:
    from scipy import ndimage as ndi
    dist = ndi.distance_transform_edt(~dots)
    # every dot's nearest *other* dot >= 2.8  <=>  removing itself keeps dist>=2.8;
    # cheaper exact check: no two dots inside any <2.8 neighbourhood.
    for y, x in zip(ys[:50], xs[:50]):
        sub = dots[max(0, y - 2): y + 3, max(0, x - 2): x + 3]
        yy, xx = np.nonzero(sub)
        for dy, dx in zip(yy - (y - max(0, y - 2)), xx - (x - max(0, x - 2))):
            if dy == 0 and dx == 0:
                continue
            assert dy * dy + dx * dx >= 2.8 * 2.8 - 1e-9
    # top-scored pixel overall must be selected
    top = np.unravel_index(np.argmax(score), score.shape)
    assert dots[top]


def test_poisson_emit_respects_eligibility():
    score = np.ones((30, 30))
    elig = np.zeros((30, 30), dtype=bool); elig[:15, :] = True
    dots = poisson_emit(score, elig, n_target=50)
    assert not dots[15:, :].any()
    assert int(dots.sum()) == 50
