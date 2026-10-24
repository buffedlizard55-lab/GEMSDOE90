"""Exact, full-footprint lane checks; never use a sampled correlation to certify uniqueness."""
from __future__ import annotations
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr


def compare(surface, dots, registry_surface, registry_dots, footprint):
    arrays = [np.asarray(x) for x in (surface, dots, registry_surface, registry_dots, footprint)]
    if len({x.shape for x in arrays}) != 1 or arrays[0].ndim != 2:
        raise ValueError('all inputs must have the same 2D shape')
    a, d, b, r, mask = arrays
    mask = mask.astype(bool)
    if not mask.any() or not np.isfinite(a[mask]).all() or not np.isfinite(b[mask]).all():
        raise ValueError('empty footprint or non-finite surface')
    # Undefined constant-surface correlation cannot establish lane independence.
    if np.ptp(a[mask]) == 0 or np.ptp(b[mask]) == 0:
        rho = None
    else:
        rho = float(spearmanr(a[mask], b[mask]).statistic)
    d, r = (d > 0) & mask, (r > 0) & mask
    overlap = float((distance_transform_edt(~r)[d] <= 3).mean()) if d.any() and r.any() else (0.0 if d.any() else None)
    duplicate = (rho is not None and rho > .90) or (overlap is not None and overlap > .70)
    return {'spearman': rho, 'dot_overlap_within_3px': overlap,
            'duplicate': bool(duplicate), 'pass': bool(not duplicate and rho is not None and overlap is not None)}
