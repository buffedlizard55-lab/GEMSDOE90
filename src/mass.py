"""MASS axis: metric-marginal (kernel-shadow) dot removal.

Why this ranking exists
-----------------------
The brief's algebra is DTI = T / (0.2T + 0.2(S - M) + 0.8|G|) with
T = kernel credit, S = sum p, M = sum over dots of p * max_g k(dot, g),
|G| = truth pixel count. Two consequences are used here and unit-tested:

1. With truth fixed, removing a dot that changes neither T nor M strictly
   decreases the denominator by 0.2(1 - c) and therefore *increases* DTI
   (c = that dot's credit to its nearest truth pixel).
2. Therefore the exact first-order value of deleting dot j is
       dDTI_j ~= [ 0.2 * (1 - c_j)  -  rho * E_j ] / D
   where E_j is dot j's *exclusive credit*, i.e. the credit it supplies at
   pixels where every other kept dot supplies less, and rho is truth pixels
   per footprint pixel. E_j is truth-free and purely geometric; c_j and rho
   are not observable locally. Dropping the dot with the smallest E_j is the
   truth-free greedy that minimises the unobservable T loss per unit mass.

The discarded alternative is the parent's recorded ranking: the 8-connected
FIFO-BFS visit order of the thinning recipe. That is a traversal tie-break,
not a probability (the brief forbids inferring a mass effect from it), and it
removes spatially contiguous runs of dots, which maximises T loss per dot.

All functions are pure numpy and operate on pixel-centre coordinates.
"""
from __future__ import annotations

import heapq

import numpy as np
from scipy.spatial import cKDTree

R_DEFAULT = 3.0  # triangular kernel radius, brief s2


def disk_patch(radius: float = R_DEFAULT) -> tuple[np.ndarray, np.ndarray]:
    """Integer offsets strictly inside the kernel disk and their credit 1 - d/R."""
    r = int(np.ceil(radius))
    grid = np.arange(-r, r + 1)
    dy, dx = np.meshgrid(grid, grid, indexing="ij")
    offsets = np.column_stack([dy.ravel(), dx.ravel()]).astype(float)
    dist = np.hypot(offsets[:, 0], offsets[:, 1])
    keep = dist < radius
    return offsets[keep], 1.0 - dist[keep] / radius


def credit_disk_area(radius: float = R_DEFAULT) -> float:
    """Continuous credit area of an isolated unit dot: integral of k over its disk."""
    return float(np.pi * radius**2 / 3.0)


def neighbour_lists(pts: np.ndarray, radius: float = R_DEFAULT) -> list[np.ndarray]:
    """Indices within 2R (a dot can only contest credit inside 2R)."""
    tree = cKDTree(pts)
    return [np.asarray(nb, dtype=np.int64) for nb in tree.query_ball_point(pts, r=2.0 * radius)]


def exclusive_credit(
    pts: np.ndarray,
    neighbours: list[np.ndarray],
    alive: np.ndarray,
    j: int,
    radius: float = R_DEFAULT,
    offsets: np.ndarray | None = None,
    patch_credit: np.ndarray | None = None,
) -> float:
    """Credit dot j supplies at pixels where no other alive dot supplies more.

    Exact for the metric's max-over-dots credit, assuming A1 (triangular kernel,
    d in pixel units) and A2 (T = sum over truth of the best dot's credit).
    """
    if not alive[j]:
        return 0.0
    if offsets is None or patch_credit is None:
        offsets, patch_credit = disk_patch(radius)
    query = pts[j] + offsets
    others = neighbours[j][alive[neighbours[j]]]
    others = others[others != j]
    if others.size == 0:
        return float(patch_credit.sum())
    delta = query[:, None, :] - pts[others][None, :, :]
    d_other = np.hypot(delta[:, :, 0], delta[:, :, 1])
    best_other = np.maximum(0.0, 1.0 - d_other.min(axis=1) / radius)
    return float(np.maximum(0.0, patch_credit - best_other).sum())


def all_exclusive_credit(
    pts: np.ndarray, neighbours: list[np.ndarray], alive: np.ndarray, radius: float = R_DEFAULT
) -> np.ndarray:
    offsets, patch_credit = disk_patch(radius)
    return np.array(
        [exclusive_credit(pts, neighbours, alive, j, radius, offsets, patch_credit) for j in range(len(pts))]
    )


def greedy_shadow_removal(
    pts: np.ndarray,
    neighbours: list[np.ndarray],
    n_remove: int,
    radius: float = R_DEFAULT,
    snapshots: tuple[int, ...] = (),
) -> dict:
    """Remove dots in ascending exclusive-credit order, recomputing locally.

    Removing a dot can only raise the exclusive credit of its neighbours, so a
    lazy heap gives the exact greedy order. Returns the removal order, the
    exclusive credit each dot had when it was removed, and masks at the
    requested removal counts (nested by construction).
    """
    n = len(pts)
    if not 0 < n_remove <= n:
        raise ValueError(f"n_remove={n_remove} outside 1..{n}")
    offsets, patch_credit = disk_patch(radius)
    for k in snapshots:
        if not 0 < k <= n_remove:
            raise ValueError(f"snapshot {k} outside 1..{n_remove}")
    alive = np.ones(n, dtype=bool)
    credit = all_exclusive_credit(pts, neighbours, alive, radius)
    heap = [(float(credit[j]), int(j)) for j in range(n)]
    heapq.heapify(heap)
    order: list[int] = []
    credit_at_removal: list[float] = []
    masks: dict[int, np.ndarray] = {}
    while len(order) < n_remove:
        value, j = heapq.heappop(heap)
        if not alive[j] or value != credit[j]:
            continue  # stale entry
        order.append(j)
        credit_at_removal.append(value)
        alive[j] = False
        if len(order) in snapshots:
            masks[len(order)] = ~alive.copy()
        touched = neighbours[j][alive[neighbours[j]]]
        for i in touched.tolist():
            new = exclusive_credit(pts, neighbours, alive, i, radius, offsets, patch_credit)
            if new != credit[i]:
                credit[i] = new
                heapq.heappush(heap, (float(new), int(i)))
    for k in snapshots:
        if k not in masks:
            masks[k] = ~alive.copy() if k == n_remove else np.zeros(n, dtype=bool)
    return {
        "order": np.asarray(order, dtype=np.int64),
        "credit_at_removal": np.asarray(credit_at_removal, dtype=float),
        "removed_masks": masks,
        "final_credit": credit,
    }


def predicted_removal_delta(
    credit_sum: float,
    n_removed: int,
    n_parent: int,
    footprint_px: int,
    mean_dot_credit: float,
    truth_px: float,
) -> float:
    """First-order MODEL dDTI for the greedy removal set (never a score).

    delta ~= [0.2 * (1 - mean_dot_credit) * n_removed - rho * credit_sum] / D
    with rho = truth_px / footprint_px and D = 0.2*n_parent + 0.8*truth_px.
    """
    rho = truth_px / footprint_px
    D = 0.2 * n_parent + 0.8 * truth_px
    saving = 0.2 * (1.0 - mean_dot_credit) * n_removed
    cost = rho * credit_sum
    return (saving - cost) / D
