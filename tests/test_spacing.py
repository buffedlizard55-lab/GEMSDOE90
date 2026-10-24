"""Unit tests for the SPACING local-respacing machinery (src/spacing.py)."""
from __future__ import annotations

import numpy as np
import pytest
from scipy.spatial import cKDTree

from src import spacing


def test_crowding_isolated_dot_is_zero_and_pair_is_symmetric():
    pts = np.array([[10.0, 10.0]])
    assert spacing.crowding_scores(pts) == pytest.approx([0.0])
    pair = np.array([[10.0, 10.0], [10.0, 13.0]])  # 3 px apart
    crowd = spacing.crowding_scores(pair)
    assert crowd[0] == pytest.approx(1.0 - 3.0 / 6.0)
    assert crowd[1] == pytest.approx(crowd[0])
    far = np.array([[10.0, 10.0], [10.0, 17.0]])  # outside the 6 px contest zone
    assert spacing.crowding_scores(far) == pytest.approx([0.0, 0.0])


def test_removal_order_puts_clustered_dot_first_and_is_deterministic():
    pts = np.array([
        [10.0, 10.0], [10.0, 13.0], [10.0, 16.0],  # a tight trio
        [40.0, 40.0],                              # isolated
    ])
    order = spacing.removal_order(pts)
    assert order[-1] == 3                     # isolated dot is respaced last
    assert set(order[:3].tolist()) == {0, 1, 2}
    assert (spacing.removal_order(pts) == order).all()


def _toy_setup():
    dots = np.zeros((40, 40), dtype=bool)
    # Crowded cluster (3 px apart) plus one isolated dot.
    for y, x in [(10, 10), (10, 13), (10, 16), (30, 30)]:
        dots[y, x] = True
    pool = np.zeros((40, 40), dtype=bool)
    pool[5:35, 5:35] = True
    pool &= ~dots
    pts = np.column_stack(np.nonzero(dots)).astype(float)
    return dots, pool, pts[spacing.removal_order(pts)]


def test_relocate_preserves_count_separation_and_locality():
    dots, pool, order_pts = _toy_setup()
    out = spacing.relocate(dots, pool, order_pts, doses=(1, 2))
    assert set(out["snapshots"]) == {1, 2}
    assert len(out["moves"]) == 2
    for dose, mask in out["snapshots"].items():
        assert int(mask.sum()) == int(dots.sum())          # fixed count
        assert not (mask & ~pool & ~dots).any()            # only pool additions
        pts = np.column_stack(np.nonzero(mask)).astype(float)
        nn, _ = cKDTree(pts).query(pts, k=2)
        assert nn[:, 1].min() >= spacing.MIN_SEP_PX - 1e-9  # parent spacing restored
    for (ry, rx), (ay, ax), win in out["moves"]:
        assert dots[ry, rx] and not dots[ay, ax] and pool[ay, ax]
        assert np.hypot(ay - ry, ax - rx) <= win <= 60       # local respacing
    # Nested doses: the 1-dose mask differs from the 2-dose mask only by
    # the second paired move.
    m1, m2 = out["snapshots"][1], out["snapshots"][2]
    (ry, rx), (ay, ax), _ = out["moves"][1]
    assert m1[ry, rx] and not m1[ay, ax] and m2[ay, ax] and not m2[ry, rx]


def test_relocate_is_deterministic():
    dots, pool, order_pts = _toy_setup()
    a = spacing.relocate(dots, pool, order_pts, doses=(2,))
    b = spacing.relocate(dots, pool, order_pts, doses=(2,))
    assert a["moves"] == b["moves"]
    assert (a["snapshots"][2] == b["snapshots"][2]).all()


def test_relocate_fails_closed_when_dose_unreachable():
    dots, pool, order_pts = _toy_setup()
    empty_pool = np.zeros_like(pool)
    with pytest.raises(ValueError, match="unreachable"):
        spacing.relocate(dots, empty_pool, order_pts, doses=(1,))


def test_spacing_stats_reports_kernel_contest():
    mask = np.zeros((30, 30), dtype=bool)
    mask[10, 10] = mask[10, 13] = mask[25, 25] = True
    stats = spacing.spacing_stats(mask)
    assert stats["n_dots"] == 3
    assert stats["nn_min_px"] == pytest.approx(3.0)
    assert stats["frac_with_neighbour_within_3px"] == pytest.approx(2 / 3)
