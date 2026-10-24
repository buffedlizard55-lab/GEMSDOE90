"""Radiometric edge-persistence surface (GEMSDOE90 new lane).

Hypothesis: hydrothermal alteration / lithologic juxtaposition along concealed
faults produces aligned K-Th-U radiometric boundaries that persist across
spatial scales, whereas regolith noise does not. Surface = per-band multiscale
gradient magnitude combined by geometric mean across scales (persistence),
then rank-fused across bands. Catalogue-free: no fault labels are used, so the
surface is fold-clean by construction in a hide-and-recover holdout.
Named non-fault mimic: lithologic contacts and transported alluvium edges.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi


def _robust01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    x = np.where(mask, a, np.nan).astype(np.float64)
    lo, hi = np.nanpercentile(x[mask], [1, 99]) if mask.any() else (0.0, 1.0)
    y = np.clip((x - lo) / max(hi - lo, 1e-9), 0, 1)
    return np.where(mask, y, 0.0)


def _rank01(a: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros(a.shape, dtype=np.float64)
    v = a[mask]
    order = v.argsort()
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(len(v), dtype=np.float64) / max(len(v) - 1, 1)
    out[mask] = ranks
    return out


def edge_persistence(band: np.ndarray, mask: np.ndarray, sigmas=(1.0, 2.0, 4.0)) -> np.ndarray:
    """Geometric-mean gradient magnitude across scales (0 outside mask)."""
    x = _robust01(band, mask)
    x = np.where(mask, x, 0.0)
    grads = []
    for s in sigmas:
        gx = ndi.gaussian_filter(x, s, order=(0, 1), mode="nearest")
        gy = ndi.gaussian_filter(x, s, order=(1, 0), mode="nearest")
        grads.append(np.hypot(gx, gy))
    g = np.exp(np.mean([np.log(np.maximum(gr, 1e-12)) for gr in grads], axis=0))
    return np.where(mask, g, 0.0)


def radiometric_surface(bands: list[np.ndarray], mask: np.ndarray) -> np.ndarray:
    """Rank-fuse edge persistence of each radiometric band; result in [0,1]."""
    if not bands:
        raise ValueError("need at least one band")
    fused = None
    for b in bands:
        r = _rank01(edge_persistence(b, mask), mask)
        fused = r if fused is None else fused + r
    fused = fused / len(bands)
    return np.where(mask, fused, 0.0).astype(np.float32)


def dotted_emission(surface: np.ndarray, eligible: np.ndarray, n_dots: int,
                     min_sep_px: float = 2.8) -> np.ndarray:
    """Greedy top-surface dots with minimum Euclidean separation (grid hash)."""
    surf = np.asarray(surface, dtype=np.float64)
    elig = np.asarray(eligible, dtype=bool) & np.isfinite(surf)
    cand = np.argwhere(elig)
    if len(cand) == 0:
        raise ValueError("no eligible pixels")
    vals = surf[elig]
    order = cand[np.argsort(-vals)]
    cell = max(int(np.ceil(min_sep_px)), 1)
    grid: dict[tuple[int, int], list[tuple[int, int]]] = {}
    chosen = []
    r2 = min_sep_px * min_sep_px
    for r, c in order:
        r, c = int(r), int(c)
        key = (r // cell, c // cell)
        ok = True
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                for (pr, pc) in grid.get((key[0] + dr, key[1] + dc), ()): 
                    if (pr - r) ** 2 + (pc - c) ** 2 < r2:
                        ok = False; break
                if not ok: break
            if not ok: break
        if ok:
            chosen.append((r, c))
            grid.setdefault(key, []).append((r, c))
            if len(chosen) >= n_dots:
                break
    out = np.zeros(surf.shape, dtype=bool)
    if chosen:
        idx = np.array(chosen)
        out[idx[:, 0], idx[:, 1]] = True
    return out
