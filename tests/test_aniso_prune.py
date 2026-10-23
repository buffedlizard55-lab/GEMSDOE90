"""Unit tests for the strike-aligned (anisotropic) PRUNE collar.

Synthetic geometry only: no competition data, no labels, no scores.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from aniso_prune import (  # noqa: E402
    COHERENCE_MIN,
    build_strike_field,
    collar_membership,
    isotropic_membership,
    parent_diff_stats,
    refill_mask,
)


def _trace(shape=(80, 80), kind="vertical", half_width=1):
    cat = np.zeros(shape, dtype=bool)
    if kind == "vertical":
        cat[20:60, 40 - half_width + 1:41 + half_width] = True
    elif kind == "horizontal":
        cat[40 - half_width + 1:41 + half_width, 20:60] = True
    elif kind == "diag":
        for t in range(20, 60):
            cat[t, t] = True
            cat[t, t + 1] = True
    else:
        raise ValueError(kind)
    return cat


def test_strike_is_perpendicular_to_trace_gradient():
    """The along-strike vector must follow the trace, not the gradient across it."""
    for kind, expected in (("vertical", (1.0, 0.0)), ("horizontal", (0.0, 1.0))):
        cat = _trace(kind=kind)
        field = build_strike_field(cat)
        all_rows, all_cols = np.nonzero(cat)
        middle = (all_rows > 34) & (all_rows < 46)  # mid-trace: away from the synthetic tips
        rows, cols = all_rows[middle][:4], all_cols[middle][:4]
        along, across, coherence = (
            field.along_dy[rows, cols], field.along_dx[rows, cols], field.coherence[rows, cols])
        assert np.all(coherence > 0.5)  # a 2 px wide synthetic trace is a pessimistic case
        assert np.allclose(np.abs(along), expected[0], atol=0.05)
        assert np.allclose(np.abs(across), expected[1], atol=0.05)


def test_diagonal_trace_along_vector_is_diagonal():
    cat = _trace(kind="diag")
    field = build_strike_field(cat)
    rows, cols = np.nonzero(cat)
    rows, cols = rows[10:20], cols[10:20]
    along_dy = np.abs(field.along_dy[rows, cols])
    along_dx = np.abs(field.along_dx[rows, cols])
    assert np.allclose(along_dy, along_dx, atol=0.05)
    assert np.all(along_dy > 0.6)


def test_collar_is_ellipse_across_strike_only():
    cat = _trace(kind="vertical")  # trace runs along rows at cols 40-41
    field = build_strike_field(cat)
    rows = np.array([40, 40, 40, 40])
    cols = np.array([44, 45, 40, 36])  # across 2.5/3.5, on-trace, across the other way
    inside, diag = collar_membership(rows, cols, field, across_px=5.0, along_px=2.0)
    assert inside.tolist() == [True, True, True, True]
    assert diag["n_inside"] == 4


def test_along_strike_continuation_is_preserved_and_isotropic_is_not():
    """A dot beyond a mapped tip is exempt under the ellipse but inside an isotropic collar."""
    cat = _trace(kind="vertical")
    field = build_strike_field(cat)
    rows = np.array([64, 62])  # beyond the trace end (rows 20-59)
    cols = np.array([40, 40])
    aniso, _ = collar_membership(rows, cols, field, across_px=5.0, along_px=2.0)
    iso = isotropic_membership(rows, cols, field, radius_px=5.0)
    assert iso.tolist() == [True, True]  # Euclidean distance 5 and 3 px
    assert aniso.tolist() == [False, False]  # along strike, so the parent's 2 px rule survives


def test_incoherent_catalogue_falls_back_to_isotropic():
    """A blob has no strike; no along-strike exemption may be granted there."""
    cat = np.zeros((60, 60), dtype=bool)
    cat[30, 30] = True  # an isolated catalogue pixel has no resolvable strike
    field = build_strike_field(cat)
    rows = np.array([34])
    cols = np.array([30])
    assert field.coherence[30, 30] < COHERENCE_MIN
    inside, diag = collar_membership(rows, cols, field, across_px=5.0, along_px=2.0)
    assert inside.tolist() == [True]
    assert diag["n_inside_incoherent_fallback"] >= 1
    isotropic_agrees = bool(isotropic_membership(rows, cols, field, 5.0)[0])
    assert isotropic_agrees


def test_radii_validation():
    cat = _trace()
    field = build_strike_field(cat)
    with pytest.raises(ValueError):
        collar_membership(np.array([40]), np.array([50]), field, across_px=2.0, along_px=4.0)
    with pytest.raises(ValueError):
        collar_membership(np.array([40]), np.array([50]), field, across_px=0.0, along_px=2.0)


def test_refill_is_deterministic_and_exact():
    pool = np.zeros((20, 20), dtype=bool)
    pool[2:12, 2:12] = True
    rank = np.arange(400, dtype=np.int32).reshape(20, 20)[::-1, ::-1].copy()
    first = refill_mask(pool, rank, 25)
    second = refill_mask(pool, rank, 25)
    assert np.array_equal(first, second)
    assert int(first.sum()) == 25
    assert not np.any(first & ~pool)
    with pytest.raises(ValueError):
        refill_mask(pool, rank, 1000)


def test_parent_diff_stats_counts_and_percentages():
    cat = _trace(kind="vertical")
    field = build_strike_field(cat)
    parent = np.zeros((80, 80), dtype=bool)
    parent[20:60, 45] = True  # 40 dots across strike
    candidate = parent.copy()
    candidate[20:30, 45] = False  # remove 10
    candidate[20:30, 60] = True  # add 10 elsewhere
    stats = parent_diff_stats(parent, candidate, field)
    assert stats["n_removed"] == 10 and stats["n_added"] == 10
    assert stats["n_candidate"] == 40
    assert stats["symmetric_difference_px"] == 20
    assert stats["pct_changed_of_parent"] == pytest.approx(50.0)
    assert stats["removed_across_abs_median_px"] == pytest.approx(4.0, abs=0.5)
