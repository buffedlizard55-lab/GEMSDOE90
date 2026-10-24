"""Surface-ranked Poisson (unit-dot) emission for the 2026-10-24 H1 lane.

Same proven emission family as the incumbent lineage (greedy dots with a
2.8 px minimum separation, unit mass), but the *visit order is the learned
surface itself* (descending score, raster order breaks ties) instead of the
geographic FIFO-BFS order that IR90-20 showed to be an artefact.  The caller
supplies the eligible mask (footprint, catalogue collar, holdout blocks), so
this module never sees a label.
"""
from __future__ import annotations

import numpy as np


def poisson_emit(
    score: np.ndarray,
    eligible: np.ndarray,
    n_target: int,
    min_sep: float = 2.8,
    candidate_factor: int = 12,
) -> np.ndarray:
    """Greedy unit dots: descending ``score`` over ``eligible``, >= min_sep apart.

    Considers at most ``candidate_factor * n_target`` top-scored eligible pixels
    (enough that separation blocking cannot starve the budget at these densities;
    verified in tests at small scale and asserted at build time).
    """
    score = np.asarray(score, dtype=np.float64)
    eligible = np.asarray(eligible, dtype=bool) & np.isfinite(score)
    h, w = score.shape
    ys, xs = np.nonzero(eligible)
    if ys.size == 0 or n_target <= 0:
        return np.zeros((h, w), dtype=bool)
    vals = score[ys, xs]
    n_cand = min(ys.size, candidate_factor * int(n_target))
    if ys.size > n_cand:
        keep_idx = np.argpartition(-vals, n_cand - 1)[:n_cand]
        ys, xs, vals = ys[keep_idx], xs[keep_idx], vals[keep_idx]
    order = np.lexsort((xs, ys, -vals))  # score desc, then raster order
    ys, xs = ys[order], xs[order]

    pad = int(np.ceil(min_sep)) + 1
    wp = w + 2 * pad
    blocked = bytearray((h + 2 * pad) * wp)
    kept = bytearray((h + 2 * pad) * wp)
    r = int(np.ceil(min_sep))
    offsets = [
        dy * wp + dx
        for dy in range(-r, r + 1)
        for dx in range(-r, r + 1)
        if dy * dy + dx * dx < min_sep * min_sep
    ]
    n_kept = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        cur = (y + pad) * wp + (x + pad)
        if blocked[cur]:
            continue
        kept[cur] = 1
        n_kept += 1
        if n_kept >= n_target:
            break
        for off in offsets:
            blocked[cur + off] = 1
    out = np.frombuffer(bytes(kept), dtype=np.uint8).reshape(h + 2 * pad, wp).astype(bool)
    return out[pad : pad + h, pad : pad + w]
