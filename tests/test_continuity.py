"""Synthetic tests for the continuity-aware MASS ranking (src/continuity.py).

No competition data: every case is a hand-built dot geometry whose link graph
(path / ring / skip-linked chain / small fragment) has a known articulation
structure, so the protected greedy's behaviour is checkable exactly.
"""
import numpy as np
import pytest

from src import continuity, mass


def _setup(pts, link_px=6.0):
    pts = np.asarray(pts, dtype=float)
    adjacency, comp, sizes = continuity.link_graph(pts, link_px=link_px)
    neighbours = mass.neighbour_lists(pts)
    return pts, neighbours, adjacency, comp, sizes


def _alive_after(n, removed_mask):
    return ~removed_mask


def test_path_interior_dots_are_articulations_endpoints_are_not():
    # 12 dots in a line, 4 px apart: linked to immediate neighbours only.
    x = np.arange(12, dtype=float) * 4.0
    pts = np.column_stack([np.zeros(12), x])
    _, _, adjacency, comp, sizes = _setup(pts)
    assert sizes.tolist() == [12]
    alive = np.ones(12, dtype=bool)
    assert not continuity.is_articulation(0, adjacency, alive)
    assert not continuity.is_articulation(11, adjacency, alive)
    assert all(continuity.is_articulation(j, adjacency, alive) for j in range(1, 11))


def test_path_greedy_removes_only_endpoints_down_to_floor():
    # A protected 12-dot path can shed exactly 2 dots (floor = 10), and both
    # must be endpoints: every interior removal would split the strand.
    x = np.arange(12, dtype=float) * 4.0
    pts = np.column_stack([np.zeros(12), x])
    for _ in range(2):  # determinism: identical repeat run
        p, nb, adj, comp, sizes = _setup(pts)
    res = continuity.greedy_continuity_removal(
        p, nb, adj, comp, sizes, n_remove=2, snapshots=(1, 2)
    )
    # Only path endpoints are ever eligible, so the strand erodes tip-inward
    # and the 10 survivors stay one contiguous run (here {0, 1} leave first:
    # equal endpoint credit breaks to the lower index, exposing dot 1).
    survivors = np.flatnonzero(~res["removed_masks"][2])
    assert len(survivors) == 10
    assert survivors.tolist() == list(range(int(survivors.min()), int(survivors.min()) + 10))
    assert res["removed_masks"][1].sum() == 1
    assert res["removed_masks"][2].sum() == 2
    assert res["blocks"]["articulation"] > 0
    alive = _alive_after(12, res["removed_masks"][2])
    surv = continuity.strand_survival(adj, comp, sizes, alive)
    assert surv["strands_surviving_whole"] == 1
    assert surv["min_alive_dots_in_a_strand"] == 10
    # A third removal from this strand alone is beyond continuity capacity.
    with pytest.raises(ValueError):
        continuity.greedy_continuity_removal(p, nb, adj, comp, sizes, n_remove=3)


def test_skip_linked_chain_allows_interior_thinning():
    # 20 dots 2.8 px apart (R0's own spacing): at 6 px linking each dot also
    # links its second neighbour (5.6 px), so interior dots are NOT
    # articulations and the greedy may thin the strand without splitting it.
    x = np.arange(20, dtype=float) * 2.8
    pts = np.column_stack([np.zeros(20), x])
    p, nb, adj, comp, sizes = _setup(pts)
    assert sizes.tolist() == [20]
    alive = np.ones(20, dtype=bool)
    assert not continuity.is_articulation(10, adj, alive)
    res = continuity.greedy_continuity_removal(
        p, nb, adj, comp, sizes, n_remove=6, snapshots=(6,)
    )
    assert res["removed_masks"][6].sum() == 6
    alive = _alive_after(20, res["removed_masks"][6])
    surv = continuity.strand_survival(adj, comp, sizes, alive)
    assert surv["strands_surviving_whole"] == 1
    assert surv["max_alive_pieces_in_a_strand"] == 1
    assert surv["min_alive_dots_in_a_strand"] == 14


def test_ring_has_no_articulation_until_cut():
    # 12 dots on a circle of radius 9 px: neighbours ~4.7 px apart, so the
    # link graph is a cycle and the first removal may be any (interior) dot.
    theta = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    pts = np.column_stack([9.0 * np.cos(theta), 9.0 * np.sin(theta)])
    p, nb, adj, comp, sizes = _setup(pts)
    assert sizes.tolist() == [12]
    alive = np.ones(12, dtype=bool)
    assert not any(continuity.is_articulation(j, adj, alive) for j in range(12))
    res = continuity.greedy_continuity_removal(
        p, nb, adj, comp, sizes, n_remove=2, snapshots=(2,)
    )
    alive = _alive_after(12, res["removed_masks"][2])
    surv = continuity.strand_survival(adj, comp, sizes, alive)
    assert surv["strands_surviving_whole"] == 1
    assert surv["min_alive_dots_in_a_strand"] == 10


def test_small_fragment_is_unprotected_even_at_articulation():
    # A 3-dot path (< 10 dots) is not a strand: its middle dot, although an
    # articulation point of its fragment, stays eligible.
    line = np.column_stack([np.zeros(12), np.arange(12, dtype=float) * 4.0])
    frag = np.array([[100.0, 0.0], [100.0, 4.0], [100.0, 8.0]])
    pts = np.vstack([line, frag])
    p, nb, adj, comp, sizes = _setup(pts)
    assert sorted(sizes.tolist()) == [3, 12]
    res = continuity.greedy_continuity_removal(
        p, nb, adj, comp, sizes, n_remove=5, snapshots=(5,)
    )
    removed = set(res["order"].tolist())
    # Capacity here is 3 (fragment) + 2 (path tip erosion) = 5, so all five
    # removals are forced in membership: the whole fragment, including its
    # articulation middle dot (index 13), plus a 2-dot tip of the path.
    assert {12, 13, 14} <= removed
    path_survivors = sorted(set(range(12)) - removed)
    assert path_survivors == list(range(path_survivors[0], path_survivors[0] + 10))
    alive = _alive_after(15, res["removed_masks"][5])
    surv = continuity.strand_survival(adj, comp, sizes, alive)
    assert surv["strands_surviving_whole"] == 1


def test_survival_instrument_counts_a_split_strand():
    # Removing the middle of a 12-dot path by hand (what protection forbids)
    # must register as 2 pieces and 0 whole strands.
    x = np.arange(12, dtype=float) * 4.0
    pts = np.column_stack([np.zeros(12), x])
    _, _, adj, comp, sizes = _setup(pts)
    alive = np.ones(12, dtype=bool)
    alive[6] = False
    surv = continuity.strand_survival(adj, comp, sizes, alive)
    assert surv["protected_strands"] == 1
    assert surv["strands_surviving_whole"] == 0
    assert surv["max_alive_pieces_in_a_strand"] == 2


def test_snapshots_are_nested_and_credits_recorded():
    x = np.arange(20, dtype=float) * 2.8
    pts = np.column_stack([np.zeros(20), x])
    p, nb, adj, comp, sizes = _setup(pts)
    res = continuity.greedy_continuity_removal(
        p, nb, adj, comp, sizes, n_remove=5, snapshots=(2, 5)
    )
    m2, m5 = res["removed_masks"][2], res["removed_masks"][5]
    assert m2.sum() == 2 and m5.sum() == 5
    assert not np.any(m2 & ~m5)  # nested
    assert len(res["order"]) == len(res["credit_at_removal"]) == 5
    assert np.all(res["credit_at_removal"] >= 0)
    assert res["protected_strands"] == 1 and res["protected_dots"] == 20
