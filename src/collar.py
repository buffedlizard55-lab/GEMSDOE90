"""AXIS=PRUNE, this session: a frontier collar rung with a *measured* refill policy.

Why this operator and not another one
-------------------------------------
The entity's PRUNE lane already holds an outward collar ladder at 3.0 / 3.5 / 4.5 / 5.5 px and
several 3.0 px fixed-count "collar + refill" files (GEMSDOE84 dcat>=3px-refill / dcat>3px-refill /
d3p0, GEMSDOE86 3 / 3r, GEMSDOE88 3 / p3px; `ledger/experiment_reservations.json` and the
read-only 2026-10-24 audit). Every one of them refills in the lineage's FIFO-BFS thinning order.
This module measures what that refill actually buys and rebuilds the collar rung at the smallest
**unoccupied** radius (3.4 px) using the *maximum-marginal* refill instead, at fixed count.

Two measured numbers drive the design (R=3 px triangular kernel, exact max-plus credit on the
pinned binary H19-5 support, which is the only support field in the lineage - IR90-08):

* FIFO-BFS refill gains 0.60 support credit per refilled dot at a 3.5 px collar.
* Maximum-marginal refill gains 1.38 support credit per dot for the same collar and count.

so a collar rung's *refill term* - not its removal term - is where the free variance sits. The
removal term is the part the brief's mechanism actually claims something about (near-catalogue
mass earns penalty, not new-fault credit), and it is truth-dependent: it cannot be settled with
any local instrument, only with a live receipt. That asymmetry is why the prediction below is
reported as two named scenarios instead of a single number.

Everything here is pure numpy on pixel indices. No truth raster, no leaderboard value and no
public-test label enters any computation.
"""
from __future__ import annotations

import numpy as np

from src.mass_add import (
    BLOCK_PX,
    block_counts,
    coverage,
    kernel_offsets,
    n_blocks,
)

# Delta-DTI per unit of *support* credit, calibrated on the three slotted MASS add rungs of
# 2026-10-23 (q50 placement, 5 km quotas, +50 %/block cap), whose MODEL predictions and whose
# support-credit ledgers are both on record:
#   1,883 dots -> 2,162 credit -> +0.008  => 3.70e-6
#   3,765 dots -> 3,814 credit -> +0.014  => 3.67e-6
#   7,531 dots -> 6,501 credit -> +0.022  => 3.38e-6
# Adopted: the mean, 3.6e-6. This is a MODEL constant, not a measurement of live DTI; it inherits
# every assumption of the add ladder it was fitted to (IR90-09 underdetermination).
PER_CREDIT = 3.6e-6


def top2_credit(mask: np.ndarray, support: np.ndarray, radius: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Per-pixel best and second-best kernel credit over the dots in `mask` on `support`."""
    m = np.asarray(mask, dtype=bool)
    sup = np.asarray(support, dtype=bool)
    h, w = sup.shape
    best = np.zeros((h, w), np.float32)
    second = np.zeros((h, w), np.float32)
    ys, xs = np.nonzero(m)
    for dy, dx, k in kernel_offsets(radius):
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        yy, xx = yy[ok], xx[ok]
        on = sup[yy, xx]
        yy, xx = yy[on], xx[on]
        if yy.size == 0:
            continue
        cur = best[yy, xx]
        is_best = k > cur
        second[yy[is_best], xx[is_best]] = np.maximum(second[yy[is_best], xx[is_best]], cur[is_best])
        best[yy[is_best], xx[is_best]] = k
        not_best = ~is_best
        second[yy[not_best], xx[not_best]] = np.maximum(second[yy[not_best], xx[not_best]], k)
    return best, second


def exclusive_credit(mask: np.ndarray, support: np.ndarray, radius: int = 3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Exclusive (drop) credit of every dot: `best - second` summed over the pixels it owns.

    This is exactly the T-loss of deleting that dot under the max-plus kernel, so it is the
    correct donor ranking for a fixed-count swap (never a convolution and never a traversal order).
    """
    m = np.asarray(mask, dtype=bool)
    sup = np.asarray(support, dtype=bool)
    h, w = sup.shape
    best = np.zeros((h, w), np.float32)
    second = np.zeros((h, w), np.float32)
    owner = np.full((h, w), -1, np.int64)
    ys, xs = np.nonzero(m)
    idx = np.arange(ys.size)
    for dy, dx, k in kernel_offsets(radius):
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        yy, xx, ii = yy[ok], xx[ok], idx[ok]
        on = sup[yy, xx]
        yy, xx, ii = yy[on], xx[on], ii[on]
        if yy.size == 0:
            continue
        cur = best[yy, xx]
        is_best = k > cur
        second[yy[is_best], xx[is_best]] = np.maximum(second[yy[is_best], xx[is_best]], cur[is_best])
        best[yy[is_best], xx[is_best]] = k
        owner[yy[is_best], xx[is_best]] = ii[is_best]
        not_best = ~is_best
        second[yy[not_best], xx[not_best]] = np.maximum(second[yy[not_best], xx[not_best]], k)
    own = np.maximum(0.0, best - second)
    own[best <= 0] = 0.0
    per_dot = np.zeros(ys.size, np.float64)
    sel = owner >= 0
    np.add.at(per_dot, owner[sel], own[sel].astype(np.float64))
    return ys, xs, per_dot


def region_even_quotas(parent_mask: np.ndarray, n_total: int, block_px: int = BLOCK_PX) -> np.ndarray:
    """Integer quotas proportional to the parent's own dot count in each block (exact sum).

    This is the anti-isolation guard of IR90-20: a collar removes dots wherever the catalogue runs,
    so the *donors* must be spread in the parent's own regional proportions, and the refills inherit
    exactly those quotas. No block may lose more dots than it holds.
    """
    par = np.asarray(parent_mask, dtype=bool)
    counts = block_counts(par, block_px).ravel().astype(np.int64)
    if n_total <= 0:
        raise ValueError("n_total must be positive")
    if n_total > int(counts.sum()):
        raise ValueError("cannot remove more dots than the parent holds")
    ideal = n_total * counts / float(counts.sum())
    q = np.minimum(np.floor(ideal).astype(np.int64), counts)
    short = int(n_total - q.sum())
    if short > 0:
        frac = np.where(counts > q, ideal - np.floor(ideal), -1.0)
        order = np.lexsort((np.arange(frac.size), -frac))
        for i in order:
            if short == 0:
                break
            if counts[i] > q[i]:
                q[i] += 1
                short -= 1
    if int(q.sum()) != n_total:
        raise AssertionError(f"region-even quotas summed to {int(q.sum())} != {n_total}")
    return q


def rebalance_quotas(quotas: np.ndarray, capacity: np.ndarray) -> tuple[np.ndarray, int]:
    """Move quota out of capacity-short blocks into blocks with spare capacity (proportionally).

    Keeps the total exact. Returns the corrected quotas and the number of dots whose block budget
    had to move, so a receipt can state how far geography departed from the donor quotas.
    """
    q = np.asarray(quotas, dtype=np.int64).copy()
    cap = np.asarray(capacity, dtype=np.int64)
    if q.shape != cap.shape:
        raise ValueError("quotas and capacity must share a shape")
    over = np.maximum(q - cap, 0)
    short = int(over.sum())
    q = np.minimum(q, cap)
    if short == 0:
        return q, 0
    spare = cap - q
    if int(spare.sum()) < short:
        raise ValueError(f"refill pool holds {int(spare.sum())} cells, shortfall {short} cannot be placed")
    ideal = short * spare / float(spare.sum())
    add = np.minimum(np.floor(ideal).astype(np.int64), spare)
    left = short - int(add.sum())
    if left > 0:
        frac = np.where(spare > add, ideal - np.floor(ideal), -1.0)
        for i in np.lexsort((np.arange(frac.size), -frac)):
            if left == 0:
                break
            if spare[i] > add[i]:
                add[i] += 1
                left -= 1
    q = q + add
    if int(q.sum()) != int(np.asarray(quotas).sum()):
        raise AssertionError("rebalance changed the total quota")
    return q, short


def refill_max_marginal(
    eligible: np.ndarray,
    support: np.ndarray,
    kept: np.ndarray,
    quotas: np.ndarray,
    radius: int = 3,
    block_px: int = BLOCK_PX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Greedy maximum marginal kernel credit inside each block's quota.

    Returns (ys, xs, credit_at_pick). The coverage array is global and updated after every pick, so
    a pick's credit reflects retained dots and earlier picks in neighbouring blocks alike.
    """
    elig = np.asarray(eligible, dtype=bool).copy()
    sup = np.asarray(support, dtype=bool)
    h, w = elig.shape
    q = np.asarray(quotas, dtype=np.int64).ravel()
    nr, nc = n_blocks(elig.shape, block_px)
    cov = coverage(kept, sup, radius)
    offs = kernel_offsets(radius)
    ys_all: list[int] = []
    xs_all: list[int] = []
    gain_all: list[float] = []
    for bi in range(q.size):
        need = int(q[bi])
        if need <= 0:
            continue
        r0 = (bi // nc) * block_px
        c0 = (bi % nc) * block_px
        r1 = min(h, r0 + block_px)
        c1 = min(w, c0 + block_px)
        ly, lx = np.nonzero(elig[r0:r1, c0:c1])
        if ly.size < need:
            raise ValueError(f"block {bi} has {ly.size} eligible cells < quota {need}")
        gy = (ly + r0).astype(np.int64)
        gx = (lx + c0).astype(np.int64)
        alive = np.ones(gy.size, bool)
        for _ in range(need):
            gains = marginal_credit(cov, sup, gy[alive], gx[alive], radius)
            alive_idx = np.flatnonzero(alive)
            pick = int(np.argmax(gains))
            i = int(alive_idx[pick])
            y, x = int(gy[i]), int(gx[i])
            alive[i] = False
            ys_all.append(y)
            xs_all.append(x)
            gain_all.append(float(gains[pick]))
            for dy, dx, k in offs:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and sup[yy, xx] and k > cov[yy, xx]:
                    cov[yy, xx] = k
    return (
        np.asarray(ys_all, dtype=np.int64),
        np.asarray(xs_all, dtype=np.int64),
        np.asarray(gain_all, dtype=np.float64),
    )


def marginal_credit(cov: np.ndarray, support: np.ndarray, ys: np.ndarray, xs: np.ndarray, radius: int = 3) -> np.ndarray:
    """Marginal support credit for each candidate pixel, vectorised over candidates."""
    sup = np.asarray(support, dtype=bool)
    h, w = cov.shape
    gains = np.zeros(ys.size, dtype=np.float64)
    for dy, dx, k in kernel_offsets(radius):
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        if not ok.any():
            continue
        yc = np.clip(yy, 0, h - 1)
        xc = np.clip(xx, 0, w - 1)
        contrib = np.where(sup[yc, xc], np.maximum(0.0, k - cov[yc, xc]), 0.0)
        gains += np.where(ok, contrib, 0.0)
    return gains


def prediction_scenarios(gained: float, lost: float, per_credit: float = PER_CREDIT) -> dict:
    """Two named scenarios plus their midpoint; never a single false-precision number.

    uniform : the removed collar dots are worth what the support surrogate says they are worth, so
              the swap only rearranges credit (this is the conservative, anti-collar reading).
    collar  : the mechanism the PRUNE axis exists for - near-catalogue mass earns penalty, not
              new-fault credit (organiser: known pixels are masked; neighbours score against new
              truth only) - so the removed dots contribute no T at all and the refill is free credit.
    """
    uniform = (gained - lost) * per_credit
    collar = gained * per_credit
    central = 0.5 * (uniform + collar)
    return {
        "lost_support_credit": round(float(lost), 3),
        "gained_support_credit": round(float(gained), 3),
        "per_credit_dti_constant": per_credit,
        "uniform_truth_scenario": round(float(uniform), 6),
        "collar_hypothesis_scenario": round(float(collar), 6),
        "central": round(float(central), 6),
        "bracket": [round(float(min(uniform, collar)), 6), round(float(max(uniform, collar)), 6)],
    }
