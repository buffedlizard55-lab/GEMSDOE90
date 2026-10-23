"""Deterministic, gain-gated SNAP assignment and raster validation.

The assignment changes position only: count, unit mass and the parent's inherited
near-catalogue pixels are fixed.  Moved dots must gain enough edge response and
may not degrade the parent's 2.8 px separation floor.  No truth labels are used.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class SnapResult:
    candidate: np.ndarray
    origins: np.ndarray
    destinations: np.ndarray
    gains: np.ndarray
    displacements: np.ndarray
    n_proposals: int


def offsets_within(radius: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Integer offsets in a Euclidean window, including the origin."""
    if not 0 < radius <= 2:
        raise ValueError("this session requires 0 < radius <= 2 px")
    r = int(np.ceil(radius))
    dy, dx = np.mgrid[-r : r + 1, -r : r + 1]
    distance = np.hypot(dy, dx)
    keep = distance <= radius + 1e-12
    return dy[keep].astype(int), dx[keep].astype(int), distance[keep]


def minimum_nearest_neighbour_distance(mask: np.ndarray) -> float:
    points = np.column_stack(np.nonzero(mask))
    if len(points) < 2:
        return float("inf")
    distances, _ = cKDTree(points).query(points, k=2)
    return float(distances[:, 1].min())


def snap_dots(
    parent: np.ndarray,
    response: np.ndarray,
    allowed_destination: np.ndarray,
    catalogue_distance: np.ndarray,
    *,
    radius: float = 2.0,
    min_gain: float = 0.10,
    min_separation: float = 2.8,
    fixed_collar: float = 3.0,
) -> SnapResult:
    """Move eligible dots to their strongest currently admissible local edge.

    Dots below ``fixed_collar`` stay byte-for-byte inherited from R0; destinations
    must be at least that far from the catalogue.  Thus no new near-collar mass is
    introduced and this function never disguises the parent's pre-existing collar
    as compliance with a general >=3 px rule.

    Proposals are processed by greatest available gain, then raster index.  Every
    unprocessed origin remains occupied, which reserves it and preserves a valid
    fallback.  Ties use response (descending), displacement, then row/column.
    """
    parent = np.asarray(parent, dtype=bool)
    response = np.asarray(response, dtype=np.float64)
    allowed_destination = np.asarray(allowed_destination, dtype=bool)
    catalogue_distance = np.asarray(catalogue_distance, dtype=np.float64)
    if not (parent.shape == response.shape == allowed_destination.shape == catalogue_distance.shape):
        raise ValueError("parent, response, allowed destination and distance must share a shape")
    if not 0 <= min_gain <= 1:
        raise ValueError("min_gain is a percentile-response gain in [0, 1]")
    if minimum_nearest_neighbour_distance(parent) + 1e-9 < min_separation:
        raise ValueError("parent does not meet the requested separation floor")

    dy, dx, distances = offsets_within(radius)
    height, width = parent.shape
    eligible_origin = parent & (catalogue_distance >= fixed_collar) & np.isfinite(response)
    allowed = allowed_destination & (catalogue_distance >= fixed_collar) & np.isfinite(response)
    origins_rc = np.column_stack(np.nonzero(eligible_origin))

    # Rank each dot by its best theoretical gain before collision/spacing checks.
    proposals: list[tuple[float, int]] = []
    for y, x in origins_rc:
        yy, xx = y + dy, x + dx
        inside = (yy >= 0) & (yy < height) & (xx >= 0) & (xx < width)
        if not inside.any():
            continue
        local_allowed = inside.copy()
        local_allowed[inside] &= allowed[yy[inside], xx[inside]]
        if not local_allowed.any():
            continue
        gains = np.full(len(dy), -np.inf)
        gains[local_allowed] = response[yy[local_allowed], xx[local_allowed]] - response[y, x]
        best_gain = float(gains.max())
        if best_gain + 1e-12 >= min_gain:
            proposals.append((best_gain, int(y * width + x)))
    proposals.sort(key=lambda item: (-item[0], item[1]))

    pad = 2  # all integer offsets closer than 2.8 px fit in a 5x5 neighbourhood
    occupied = np.pad(parent, pad, constant_values=False)
    sy, sx = np.mgrid[-pad : pad + 1, -pad : pad + 1]
    too_close = (sy * sy + sx * sx) < min_separation * min_separation - 1e-12

    moved_origins: list[tuple[int, int]] = []
    moved_destinations: list[tuple[int, int]] = []
    realised_gains: list[float] = []
    realised_displacements: list[float] = []

    for _, flat_index in proposals:
        y, x = divmod(flat_index, width)
        py, px = y + pad, x + pad
        if not occupied[py, px]:
            raise AssertionError("an unprocessed origin was not reserved")
        occupied[py, px] = False
        yy, xx = y + dy, x + dx
        inside = (yy >= 0) & (yy < height) & (xx >= 0) & (xx < width)
        candidate_order = []
        for j in np.flatnonzero(inside):
            ny, nx = int(yy[j]), int(xx[j])
            if not allowed[ny, nx]:
                continue
            gain = float(response[ny, nx] - response[y, x])
            if gain + 1e-12 < min_gain:
                continue
            candidate_order.append((-response[ny, nx], float(distances[j]), int(dy[j]), int(dx[j]), j, gain))
        candidate_order.sort()

        chosen = None
        for _, displacement, _, _, j, gain in candidate_order:
            ny, nx = int(yy[j]), int(xx[j])
            qy, qx = ny + pad, nx + pad
            neighbourhood = occupied[qy - pad : qy + pad + 1, qx - pad : qx + pad + 1]
            if np.any(neighbourhood & too_close):
                continue
            chosen = (ny, nx, gain, displacement)
            break
        if chosen is None:
            occupied[py, px] = True
            continue
        ny, nx, gain, displacement = chosen
        occupied[ny + pad, nx + pad] = True
        moved_origins.append((y, x))
        moved_destinations.append((ny, nx))
        realised_gains.append(gain)
        realised_displacements.append(displacement)

    candidate = occupied[pad : pad + height, pad : pad + width]
    origins = np.asarray(moved_origins, dtype=np.int32).reshape(-1, 2)
    destinations = np.asarray(moved_destinations, dtype=np.int32).reshape(-1, 2)
    gains = np.asarray(realised_gains, dtype=np.float64)
    displacements = np.asarray(realised_displacements, dtype=np.float64)

    if int(candidate.sum()) != int(parent.sum()):
        raise AssertionError("SNAP did not preserve dot count")
    if not np.array_equal(candidate & (catalogue_distance < fixed_collar),
                          parent & (catalogue_distance < fixed_collar)):
        raise AssertionError("near-catalogue pixels were not exactly inherited")
    if minimum_nearest_neighbour_distance(candidate) + 1e-9 < min_separation:
        raise AssertionError("SNAP degraded the separation floor")
    if len(origins):
        if np.any(displacements > radius + 1e-9) or np.any(gains + 1e-12 < min_gain):
            raise AssertionError("SNAP violated its displacement or gain cap")
        if int((parent & ~candidate).sum()) != len(origins) or int((candidate & ~parent).sum()) != len(origins):
            raise AssertionError("parent diff does not equal the number of moved dots")
    return SnapResult(candidate, origins, destinations, gains, displacements, len(proposals))


def result_statistics(result: SnapResult, parent: np.ndarray, response: np.ndarray) -> dict:
    candidate = result.candidate
    moved = len(result.origins)
    n_dots = int(parent.sum())
    before = float(np.mean(response[parent & np.isfinite(response)]))
    after = float(np.mean(response[candidate & np.isfinite(response)]))
    return {
        "n_dots": n_dots,
        "n_proposals": int(result.n_proposals),
        "n_moved": moved,
        "pct_changed": 100.0 * moved / n_dots,
        "removed_from_parent": int((parent & ~candidate).sum()),
        "added_to_parent": int((candidate & ~parent).sum()),
        "retained_parent": int((candidate & parent).sum()),
        "mean_displacement_px_all_dots": float(result.displacements.sum() / n_dots),
        "mean_displacement_px_moved": float(np.mean(result.displacements)) if moved else 0.0,
        "max_displacement_px": float(np.max(result.displacements)) if moved else 0.0,
        "mean_response_gain_moved": float(np.mean(result.gains)) if moved else 0.0,
        "median_response_gain_moved": float(np.median(result.gains)) if moved else 0.0,
        "mean_response_before": before,
        "mean_response_after": after,
        "minimum_nearest_neighbour_distance_px": minimum_nearest_neighbour_distance(candidate),
    }


def validate_snap_file(
    path: Path,
    *,
    expected: np.ndarray,
    parent: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    catalogue_distance: np.ndarray,
    sample_profile: dict,
    mode: str,
    min_separation: float = 2.8,
) -> dict:
    """Re-read and gate one written raster; never infer compliance from memory."""
    with rasterio.open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs = src.crs
        transform = src.transform
    observed = footprint & np.isfinite(a) & (a > 0.5)
    near = catalogue_distance < 3.0
    checks = {
        "crs_matches_sample": crs == sample_profile["crs"],
        "transform_matches_sample": transform == sample_profile["transform"],
        "shape_matches_sample": a.shape == (sample_profile["height"], sample_profile["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(a[footprint]).all()),
        "inside_foot_range_0_1": bool(np.all((a[footprint] >= 0) & (a[footprint] <= 1))),
        "outside_is_nan": bool(np.isnan(a[~footprint]).all()) if mode == "nan" else bool(np.all(a[~footprint] == 0)),
        "exact_expected_mask_after_disk_read": bool(np.array_equal(observed, expected)),
        "zero_catalogue_mass": not bool(np.any(observed & catalogue)),
        "count_matches_parent": int(observed.sum()) == int(parent.sum()),
        "parent_exclusion_d_cat_gt_2px": float(catalogue_distance[observed].min()) > 2.0,
        "near_collar_exactly_inherited_no_new_mass": bool(np.array_equal(observed & near, parent & near)),
        "minimum_separation_ge_2p8px": minimum_nearest_neighbour_distance(observed) + 1e-9 >= min_separation,
        "file_re_read_from_disk": True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"validator failed for {path.name}: {failed}")
    return {
        "path": str(path),
        "encoding": mode,
        "n_dots": int(observed.sum()),
        "min_catalogue_distance_px": float(catalogue_distance[observed].min()),
        "near_catalogue_dots_below_3px": int((observed & near).sum()),
        "general_3px_hard_constraint_passed": not bool(np.any(observed & near)),
        "upload_eligible": False,
        "checks": checks,
    }
