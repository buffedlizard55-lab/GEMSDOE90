"""Strike-aware (anisotropic) catalogue collar for AXIS = PRUNE.

Parent R0 (`h33-h33-2-b2`) applies an isotropic collar: keep a dot only where its
Euclidean distance to the known-fault catalogue is > 2 px. The collar is isotropic
because it treats positional error as direction-free. On a 400 m-line-spacing
aeromagnetic survey the *cross-strike* positional error is what matters; along strike,
a dot near a mapped trace is more plausibly the unmapped continuation of that trace,
which the organiser says is still scored ("newly mapped geometry of existing systems").

So this module builds one two-parameter collar family:

    inside collar  <=>  (along/L)^2 + (across/A)^2 <= 1      (an ellipse aligned to local strike)
    L = 2.0 px  -- the parent's own radius, retained along strike
    A = across-strike radius, the single rotated parameter of the experiment

Local strike comes from a structure tensor of the catalogue mask: gradients of a thin
binary trace run across the trace, so the *major* eigenvector is the across-strike
direction and the *minor* eigenvector is along strike. Where the tensor is incoherent
(junctions, terminations, isolated catalogue blobs) the along-strike exemption is not
granted and the collar falls back to isotropic A -- "do not claim continuity you cannot
see". Nothing here is a geological probability; it is a geometric exclusion rule.

All functions are pure and unit-tested in tests/test_aniso_prune.py.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

COHERENCE_MIN = 0.3
SMOOTH_SIGMA = 1.0
TENSOR_SIGMA = 3.0


@dataclass(frozen=True)
class StrikeField:
    """Per-pixel strike estimate plus the nearest-catalogue-pixel lookup."""

    along_dy: np.ndarray  # (H, W) float32: along-strike unit vector, row component
    along_dx: np.ndarray  # (H, W) float32: along-strike unit vector, col component
    across_dy: np.ndarray
    across_dx: np.ndarray
    coherence: np.ndarray  # (H, W) float32 in [0, 1]
    dist: np.ndarray  # (H, W) float64 Euclidean distance to nearest catalogue pixel
    nearest_row: np.ndarray  # (H, W) int32 row of nearest catalogue pixel
    nearest_col: np.ndarray  # (H, W) int32 col of nearest catalogue pixel


def build_strike_field(
    catalogue: np.ndarray,
    smooth_sigma: float = SMOOTH_SIGMA,
    tensor_sigma: float = TENSOR_SIGMA,
) -> StrikeField:
    """Structure-tensor strike field and Euclidean distance transform of `catalogue`.

    Convention (verified on synthetic horizontal / vertical / 45-degree traces in
    tests/test_aniso_prune.py): with theta = 0.5*atan2(2*Jxy, Jxx-Jyy),
        along-strike  = (dy, dx) = ( cos(theta), -sin(theta))
        across-strike = (dy, dx) = ( sin(theta),  cos(theta))
    """
    cat = np.asarray(catalogue, dtype=bool)
    if not cat.any():
        raise ValueError("catalogue mask is empty: strike is undefined")

    smooth = ndi.gaussian_filter(cat.astype(np.float32), smooth_sigma)
    grad_row, grad_col = np.gradient(smooth)
    jxx = ndi.gaussian_filter(grad_col * grad_col, tensor_sigma)
    jyy = ndi.gaussian_filter(grad_row * grad_row, tensor_sigma)
    jxy = ndi.gaussian_filter(grad_col * grad_row, tensor_sigma)

    trace = jxx + jyy
    anis = np.hypot(jxx - jyy, 2.0 * jxy)  # lambda1 - lambda2, both non-negative
    coherence = np.where(trace > 0, anis / np.maximum(trace, 1e-12), 0.0).astype(np.float32)
    theta = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy).astype(np.float32)

    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    dist, indices = ndi.distance_transform_edt(~cat, return_indices=True)
    return StrikeField(
        along_dy=cos_t,
        along_dx=-sin_t,
        across_dy=sin_t,
        across_dx=cos_t,
        coherence=np.clip(coherence, 0.0, 1.0),
        dist=dist,
        nearest_row=indices[0].astype(np.int32),
        nearest_col=indices[1].astype(np.int32),
    )


def offsets_to_catalogue(rows: np.ndarray, cols: np.ndarray, field: StrikeField) -> tuple[np.ndarray, np.ndarray]:
    """Vector from each pixel to its nearest catalogue pixel, as (d_row, d_col)."""
    rows = np.asarray(rows, dtype=np.int64)
    cols = np.asarray(cols, dtype=np.int64)
    return (
        rows - field.nearest_row[rows, cols].astype(np.int64),
        cols - field.nearest_col[rows, cols].astype(np.int64),
    )


def along_across(rows: np.ndarray, cols: np.ndarray, field: StrikeField) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Signed along-strike and across-strike distances (px) plus the local coherence."""
    rows = np.asarray(rows, dtype=np.int64)
    cols = np.asarray(cols, dtype=np.int64)
    d_row, d_col = offsets_to_catalogue(rows, cols, field)
    near_r = field.nearest_row[rows, cols].astype(np.int64)
    near_c = field.nearest_col[rows, cols].astype(np.int64)
    along = d_row * field.along_dy[near_r, near_c] + d_col * field.along_dx[near_r, near_c]
    across = d_row * field.across_dy[near_r, near_c] + d_col * field.across_dx[near_r, near_c]
    return along.astype(np.float64), across.astype(np.float64), field.coherence[near_r, near_c].astype(np.float64)


def collar_membership(
    rows: np.ndarray,
    cols: np.ndarray,
    field: StrikeField,
    across_px: float,
    along_px: float,
    coherence_min: float = COHERENCE_MIN,
) -> tuple[np.ndarray, dict]:
    """True where a pixel lies inside the strike-aware collar.

    Coherent pixels use the ellipse (along/along_px)^2 + (across/across_px)^2 <= 1;
    incoherent pixels get no along-strike exemption and use dist <= across_px.
    """
    if across_px <= 0 or along_px <= 0:
        raise ValueError("collar radii must be positive")
    if across_px < along_px:
        raise ValueError("across_px must be >= along_px (the parent radius) for this family")
    rows = np.asarray(rows, dtype=np.int64)
    cols = np.asarray(cols, dtype=np.int64)
    along, across, coherence = along_across(rows, cols, field)
    coherent = coherence >= coherence_min
    ellipse = (along / along_px) ** 2 + (across / across_px) ** 2 <= 1.0
    euclid = field.dist[rows, cols]
    inside = np.where(coherent, ellipse, euclid <= across_px)
    diag = {
        "across_px": float(across_px),
        "along_px": float(along_px),
        "coherence_min": float(coherence_min),
        "n_candidates": int(rows.size),
        "n_inside": int(inside.sum()),
        "n_inside_coherent_ellipse": int((inside & coherent).sum()),
        "n_inside_incoherent_fallback": int((inside & ~coherent).sum()),
        "n_coherent": int(coherent.sum()),
        "coherence_median": float(np.median(coherence)) if rows.size else float("nan"),
        "euclid_min_inside": float(euclid[inside].min()) if inside.any() else None,
        "euclid_max_inside": float(euclid[inside].max()) if inside.any() else None,
        "along_abs_median_inside": float(np.median(np.abs(along[inside]))) if inside.any() else None,
        "across_abs_median_inside": float(np.median(np.abs(across[inside]))) if inside.any() else None,
    }
    return inside, diag


def isotropic_membership(rows: np.ndarray, cols: np.ndarray, field: StrikeField, radius_px: float) -> np.ndarray:
    """Comparator: the plain Euclidean collar used by earlier PRUNE rungs."""
    rows = np.asarray(rows, dtype=np.int64)
    cols = np.asarray(cols, dtype=np.int64)
    return field.dist[rows, cols] <= radius_px


def parent_diff_stats(
    parent: np.ndarray,
    candidate: np.ndarray,
    field: StrikeField,
) -> dict:
    """Parent-difference statistics for the ledger (removed / added / moved geometry)."""
    parent = np.asarray(parent, dtype=bool)
    candidate = np.asarray(candidate, dtype=bool)
    removed = parent & ~candidate
    added = candidate & ~parent
    r_rows, r_cols = np.nonzero(removed)
    a_rows, a_cols = np.nonzero(added)
    along, across, coherence = along_across(r_rows, r_cols, field) if r_rows.size else (
        np.zeros(0), np.zeros(0), np.zeros(0))
    stats = {
        "n_parent": int(parent.sum()),
        "n_candidate": int(candidate.sum()),
        "n_removed": int(removed.sum()),
        "n_added": int(added.sum()),
        "n_retained_parent": int((parent & candidate).sum()),
        "symmetric_difference_px": int((parent ^ candidate).sum()),
        "pct_changed_of_parent": 100.0 * float((parent ^ candidate).sum()) / float(parent.sum()),
        "removed_along_abs_median_px": float(np.median(np.abs(along))) if r_rows.size else None,
        "removed_across_abs_median_px": float(np.median(np.abs(across))) if r_rows.size else None,
        "removed_coherence_median": float(np.median(coherence)) if r_rows.size else None,
        "removed_dist_median_px": float(np.median(field.dist[r_rows, r_cols])) if r_rows.size else None,
        "removed_dist_max_px": float(field.dist[r_rows, r_cols].max()) if r_rows.size else None,
        "added_dist_median_px": float(np.median(field.dist[a_rows, a_cols])) if a_rows.size else None,
        "added_dist_min_px": float(field.dist[a_rows, a_cols].min()) if a_rows.size else None,
    }
    if r_rows.size:
        # Nearest-distance from every removed dot to its replacement set (px).
        added_mask = np.zeros_like(removed)
        added_mask[a_rows, a_cols] = True
        if added_mask.any():
            d_to_added = ndi.distance_transform_edt(~added_mask)
            stats["removed_to_nearest_added_median_px"] = float(np.median(d_to_added[r_rows, r_cols]))
            stats["removed_to_nearest_added_max_px"] = float(d_to_added[r_rows, r_cols].max())
        stats["removed_outside_kernel_of_any_added"] = int(
            (d_to_added[r_rows, r_cols] > 3.0).sum()) if added_mask.any() else None
    return stats


def refill_mask(
    pool: np.ndarray,
    rank: np.ndarray,
    n_refill: int,
) -> np.ndarray:
    """Deterministic FIFO-BFS-ordered refill: take the `n_refill` lowest-ranked pool pixels."""
    pool = np.asarray(pool, dtype=bool)
    rows, cols = np.nonzero(pool)
    if rows.size < n_refill:
        raise ValueError(f"refill pool has {rows.size} pixels, need {n_refill}")
    order = np.argsort(rank[rows, cols], kind="stable")[:n_refill]
    out = np.zeros_like(pool)
    out[rows[order], cols[order]] = True
    return out
