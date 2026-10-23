"""PRUNE core operations on dot sets (pure arrays; unit-tested).

Distance definition is a REBUILD TARGET, not a free choice: whichever of
'euclidean' / 'chebyshev' reproduces R0 exactly from the pre-prune dots is the
parent recipe's definition. If neither does, the build stops (brief s5).
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt


def distance_field(catalogue: np.ndarray, metric: str = "euclidean") -> np.ndarray:
    """Distance (px) from every pixel to the nearest catalogue pixel."""
    cat = np.asarray(catalogue) > 0
    if metric == "euclidean":
        return distance_transform_edt(~cat)
    if metric == "chebyshev":
        # EDT with chessboard metric via repeated dilation-free transform:
        # scipy has no direct chessboard EDT; compute via distance_transform_edt
        # on the L-inf metric using the 'chamfer' trick of two passes is overkill
        # for a rebuild probe -- use brute dilation rings up to the needed radius.
        from scipy.ndimage import binary_dilation

        dist = np.full(cat.shape, np.inf)
        dist[cat] = 0.0
        ring = cat.copy()
        d = 0
        structure = np.ones((3, 3), dtype=bool)
        while not np.isfinite(dist).all():
            d += 1
            ring = binary_dilation(ring, structure=structure)
            dist[np.isinf(dist) & ring] = float(d)
            if d > max(cat.shape):  # safety
                break
        return dist
    raise ValueError(f"unknown metric {metric!r}")


def dots_of(raster: np.ndarray) -> set[tuple[int, int]]:
    a = np.asarray(raster)
    return {(int(r), int(c)) for r, c in zip(*np.nonzero(np.nan_to_num(a) > 0))}


def prune_le(dots: set[tuple[int, int]], dist: np.ndarray, threshold: float) -> set[tuple[int, int]]:
    """Keep dots whose distance to the catalogue is > threshold px."""
    return {(r, c) for (r, c) in dots if dist[r, c] > threshold}


def refill(
    dots: set[tuple[int, int]],
    ranked: list[tuple[int, int, int]],
    dist: np.ndarray,
    threshold: float,
    inside: np.ndarray,
    target_n: int,
) -> set[tuple[int, int]]:
    """Add highest-ranked candidates (rank asc) with dist > threshold, inside the
    footprint, not already present, until target_n is reached."""
    out = set(dots)
    for r, c, _rank in sorted(ranked, key=lambda t: t[2]):
        if len(out) >= target_n:
            break
        if (r, c) in out or not inside[r, c] or dist[r, c] <= threshold:
            continue
        out.add((r, c))
    return out


def drop_lowest_ranked(
    dots: set[tuple[int, int]], ranked: list[tuple[int, int, int]], target_n: int
) -> set[tuple[int, int]]:
    """Keep the target_n best-ranked dots. Every dot must be ranked."""
    rank = {(r, c): rk for r, c, rk in ranked}
    missing = dots - rank.keys()
    if missing:
        raise ValueError(f"{len(missing)} dots absent from ranked_candidates; cannot drop lowest-ranked")
    return set(sorted(dots, key=lambda rc: rank[rc])[:target_n])


def pct_changed(new: set[tuple[int, int]], parent: set[tuple[int, int]]) -> float:
    """Symmetric-difference share relative to the parent dot count, in percent."""
    return 100.0 * len(new ^ parent) / max(len(parent), 1)


def render(dots: set[tuple[int, int]], inside: np.ndarray, outside_nan: bool = True) -> np.ndarray:
    a = np.zeros(inside.shape, dtype="float32")
    for r, c in dots:
        a[r, c] = 1.0
    if outside_nan:
        a[~inside] = np.nan
    return a
