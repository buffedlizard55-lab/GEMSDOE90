"""MASS axis, continuity-aware ranking: exclusive-credit removal that may not
split a kernel-continuous strand.

Why this ranking exists
-----------------------
The in-repo shadow ladder (`src/mass.py`) deletes dots in ascending exclusive
300 m kernel-credit order. That minimises the truth-free credit loss per dot,
but the measured side effect is structural: at the 40 % dose it leaves **0** of
R0's 838 strands of >= 10 dots at 5 px linking, while a credit-blind random
deletion of the same size leaves 136 (`evidence/mass_high_dose_receipt.json`).
The ranking preferentially eats densely sampled stretches -- exactly where
along-strike continuity lives -- because interior strand dots are the most
kernel-shadowed.

This module keeps the same credit ranking and adds one eligibility rule, so
the dose, the parent and the credit definition are unchanged and only the
continuity constraint varies:

* Link graph: dots within ``link_px = 6.0`` px (= 2R, the kernel diameter) are
  linked. Two alive dots 6 px apart still have touching kernel disks, so a
  strand that stays connected in this graph keeps unbroken kernel coverage
  along strike; a split here is a genuine > 600 m coverage gap.
* A component of the R0 link graph with >= ``min_strand_dots`` (10) dots is a
  protected strand (the same >= 10-dot / ~>= 1 km instrument the high-dose
  session reported). A dot in a protected strand is ineligible for removal
  while (a) it is an articulation point of the strand's alive subgraph
  (removing it would split the strand), or (b) the strand is already down to
  ``min_strand_dots`` alive dots (the floor stops tip-by-tip extinction,
  which articulation alone permits on a path).
* Dots in unprotected components (< 10 dots) are always eligible.

By construction every R0 protected strand survives at any feasible dose as a
single connected strand of >= 10 dots in the 6 px graph. The price is paid in
exclusive credit: the constrained greedy must sometimes pass over a cheap
interior dot and remove a dearer one. That price is measured exactly (the
credit sum at each dose) and reported against the unconstrained ladder at
matched count, so the live receipts can separate "credit saved" from
"continuity kept".

Everything here is a deterministic function of the parent dot coordinates:
no feature band, no catalogue distance, no label and no score is read.
"""
from __future__ import annotations

import heapq

import numpy as np
from scipy.spatial import cKDTree

from src import mass

LINK_PX_DEFAULT = 6.0  # 2R: kernel disks of linked dots touch or overlap
MIN_STRAND_DOTS_DEFAULT = 10  # >= 10 dots ~ >= 1 km at R0 spacing (repo instrument)


def link_graph(
    pts: np.ndarray, link_px: float = LINK_PX_DEFAULT
) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """Adjacency lists, component id per dot, and component sizes.

    Components are labelled 0..K-1 in order of their smallest dot index, so
    the result is deterministic for a fixed point order.
    """
    pts = np.asarray(pts, dtype=float)
    n = len(pts)
    tree = cKDTree(pts)
    pairs = tree.query_pairs(link_px)
    adjacency: list[list[int]] = [[] for _ in range(n)]
    for i, j in sorted(pairs):
        adjacency[i].append(j)
        adjacency[j].append(i)
    adjacency_arr = [np.asarray(sorted(a), dtype=np.int64) for a in adjacency]

    comp = np.full(n, -1, dtype=np.int64)
    sizes: list[int] = []
    for start in range(n):
        if comp[start] != -1:
            continue
        cid = len(sizes)
        stack = [start]
        comp[start] = cid
        size = 0
        while stack:
            u = stack.pop()
            size += 1
            for v in adjacency_arr[u].tolist():
                if comp[v] == -1:
                    comp[v] = cid
                    stack.append(v)
        sizes.append(size)
    return adjacency_arr, comp, np.asarray(sizes, dtype=np.int64)


def is_articulation(j: int, adjacency: list[np.ndarray], alive: np.ndarray) -> bool:
    """True iff removing dot j disconnects some pair of its alive neighbours.

    Exact for the alive induced subgraph: j is an articulation point iff two
    of its alive neighbours lie in different components of the graph without
    j. The search never leaves j's original component (edges only exist
    inside one), and components in R0 are small (max 325 dots at 6 px).
    """
    neighbours = [int(v) for v in adjacency[j].tolist() if alive[v]]
    if len(neighbours) <= 1:
        return False
    target = set(neighbours[1:])
    seen = {neighbours[0]}
    stack = [neighbours[0]]
    while stack and target:
        u = stack.pop()
        for v in adjacency[u].tolist():
            v = int(v)
            if v == j or not alive[v] or v in seen:
                continue
            seen.add(v)
            target.discard(v)
            stack.append(v)
    return bool(target)


def greedy_continuity_removal(
    pts: np.ndarray,
    credit_neighbours: list[np.ndarray],
    link_adjacency: list[np.ndarray],
    comp: np.ndarray,
    comp_sizes: np.ndarray,
    n_remove: int,
    radius: float = mass.R_DEFAULT,
    min_strand_dots: int = MIN_STRAND_DOTS_DEFAULT,
    snapshots: tuple[int, ...] = (),
) -> dict:
    """Remove dots in ascending exclusive-credit order under strand protection.

    Same lazy-heap greedy as `src.mass.greedy_shadow_removal` (removing a dot
    can only raise neighbours' exclusive credit), plus parking: a popped dot
    that is currently ineligible (articulation or strand floor) is parked and
    re-queued whenever another dot of its strand is removed, the only event
    that can change its eligibility. Ties break on dot index (raster order),
    exactly as in the unconstrained ladder, so the two rankings differ only
    where protection binds.
    """
    n = len(pts)
    if not 0 < n_remove <= n:
        raise ValueError(f"n_remove={n_remove} outside 1..{n}")
    for k in snapshots:
        if not 0 < k <= n_remove:
            raise ValueError(f"snapshot {k} outside 1..{n_remove}")
    protected_comp = comp_sizes >= min_strand_dots
    max_removable = int(n - min_strand_dots * int(protected_comp.sum()))
    if n_remove > max_removable:
        raise ValueError(
            f"n_remove={n_remove} exceeds the continuity capacity {max_removable} "
            f"({int(protected_comp.sum())} protected strands keep >= {min_strand_dots} dots)"
        )

    offsets, patch_credit = mass.disk_patch(radius)
    alive = np.ones(n, dtype=bool)
    alive_in_comp = comp_sizes.astype(np.int64).copy()
    credit = mass.all_exclusive_credit(pts, credit_neighbours, alive, radius)
    parked = np.zeros(n, dtype=bool)
    parked_in_comp: dict[int, set[int]] = {}
    heap = [(float(credit[j]), int(j)) for j in range(n)]
    heapq.heapify(heap)

    def eligibility(j: int) -> str | None:
        """None if removable now, else the blocking reason."""
        cid = int(comp[j])
        if not protected_comp[cid]:
            return None
        if alive_in_comp[cid] <= min_strand_dots:
            return "floor"
        if is_articulation(j, link_adjacency, alive):
            return "articulation"
        return None

    order: list[int] = []
    credit_at_removal: list[float] = []
    masks: dict[int, np.ndarray] = {}
    blocks = {"articulation": 0, "floor": 0}
    while len(order) < n_remove:
        if not heap:
            raise RuntimeError(
                f"continuity greedy stalled at {len(order)}/{n_remove} removals "
                f"with {int(parked.sum())} dots parked"
            )
        value, j = heapq.heappop(heap)
        if not alive[j] or parked[j] or value != credit[j]:
            continue  # stale entry
        reason = eligibility(j)
        if reason is not None:
            blocks[reason] += 1
            parked[j] = True
            parked_in_comp.setdefault(int(comp[j]), set()).add(j)
            continue
        order.append(j)
        credit_at_removal.append(value)
        alive[j] = False
        alive_in_comp[int(comp[j])] -= 1
        if len(order) in snapshots:
            masks[len(order)] = ~alive.copy()
        # Credit can only rise for credit-neighbours; re-queue the changed ones.
        touched = credit_neighbours[j][alive[credit_neighbours[j]]]
        for i in touched.tolist():
            new = mass.exclusive_credit(
                pts, credit_neighbours, alive, int(i), radius, offsets, patch_credit
            )
            if new != credit[i]:
                credit[i] = new
                if not parked[i]:
                    heapq.heappush(heap, (float(new), int(i)))
        # A removal inside a strand is the only event that can unblock its
        # parked dots (their credit updates above already landed in `credit`).
        waiting = parked_in_comp.pop(int(comp[j]), None)
        if waiting:
            for i in sorted(waiting):
                parked[i] = False
                heapq.heappush(heap, (float(credit[i]), int(i)))
    for k in snapshots:
        if k not in masks:
            masks[k] = ~alive.copy() if k == n_remove else np.zeros(n, dtype=bool)
    return {
        "order": np.asarray(order, dtype=np.int64),
        "credit_at_removal": np.asarray(credit_at_removal, dtype=float),
        "removed_masks": masks,
        "final_credit": credit,
        "blocks": blocks,
        "parked_at_end": int(parked.sum()),
        "max_removable": max_removable,
        "protected_strands": int(protected_comp.sum()),
        "protected_dots": int(comp_sizes[protected_comp].sum()),
    }


def strand_survival(
    link_adjacency: list[np.ndarray],
    comp: np.ndarray,
    comp_sizes: np.ndarray,
    alive: np.ndarray,
    min_strand_dots: int = MIN_STRAND_DOTS_DEFAULT,
) -> dict:
    """Per protected R0 strand: alive dots and alive pieces after removal.

    Computed on the same link graph the protection used. A strand "survives
    whole" when its alive dots still form one connected piece of at least
    ``min_strand_dots`` dots -- guaranteed by construction for
    `greedy_continuity_removal`, and measured (not assumed) here so any other
    removal set (shadow, random) can be scored on the identical instrument.
    """
    alive = np.asarray(alive, dtype=bool)
    n_strands = 0
    whole = 0
    min_alive = None
    max_pieces = 0
    total_alive = 0
    for cid in range(len(comp_sizes)):
        if comp_sizes[cid] < min_strand_dots:
            continue
        n_strands += 1
        members = np.flatnonzero((comp == cid) & alive)
        total_alive += int(len(members))
        min_alive = int(len(members)) if min_alive is None else min(min_alive, int(len(members)))
        member_set = set(members.tolist())
        pieces = 0
        seen: set[int] = set()
        for start in members.tolist():
            if start in seen:
                continue
            pieces += 1
            stack = [start]
            seen.add(start)
            while stack:
                u = stack.pop()
                for v in link_adjacency[u].tolist():
                    v = int(v)
                    if v in member_set and v not in seen:
                        seen.add(v)
                        stack.append(v)
        max_pieces = max(max_pieces, pieces)
        if pieces == 1 and len(members) >= min_strand_dots:
            whole += 1
    return {
        "protected_strands": int(n_strands),
        "strands_surviving_whole": int(whole),
        "min_alive_dots_in_a_strand": int(min_alive) if min_alive is not None else 0,
        "max_alive_pieces_in_a_strand": int(max_pieces),
        "alive_dots_in_protected_strands": int(total_alive),
    }
