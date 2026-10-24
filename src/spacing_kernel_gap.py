"""AXIS=SPACING: fixed-count, block-local kernel-gap equalization.

The operator moves unit-mass dots from pixels whose *exclusive* R=3 px triangular
kernel credit is smallest to pixels whose *marginal* credit is largest.  It is
deliberately paired inside each 5 km block: the dot count and block-density CV of
R0 are unchanged, so the experiment isolates spacing rather than mass, relief,
concentration, collar or regional geography.

No label or leaderboard value enters placement.  The catalogue is used only as a
hard exclusion: donors are restricted to R0 dots at d_cat >= 3 px and additions
must also be at d_cat >= 3 px.  Untouched R0 dots keep the parent's 2.236 px
floor, as in the repo's other non-PRUNE fixed-count variants (IR90-07/18/21).
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

import numpy as np

R_PX = 3
BLOCK_PX = 50
MIN_ADDED_CAT_DIST = 3.0
MAX_BLOCK_DONOR_FRAC = 0.30


def kernel_offsets(radius: int = R_PX) -> tuple[np.ndarray, np.ndarray]:
    """Integer pixel offsets strictly inside the triangular kernel (centre included)."""
    out: list[tuple[int, int]] = []
    credit: list[float] = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            d = math.hypot(dy, dx)
            if d < radius:
                out.append((dy, dx))
                credit.append(1.0 - d / float(radius))
    return np.asarray(out, dtype=np.int64), np.asarray(credit, dtype=np.float64)


def block_index(shape: tuple[int, int], block_px: int = BLOCK_PX) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """Row-major fixed-grid block ids for each pixel, including partial edge blocks."""
    h, w = shape
    by = np.arange(h) // block_px
    bx = np.arange(w) // block_px
    ncols = int(bx.max()) + 1
    bid = by[:, None] * ncols + bx[None, :]
    return bid, np.arange(int(bid.max()) + 1), (int(by.max()) + 1, ncols)


def _proportional_exact(weights: np.ndarray, n_total: int) -> np.ndarray:
    """Largest-remainder integer apportionment with an exact sum."""
    w = np.asarray(weights, dtype=np.float64)
    if n_total < 0:
        raise ValueError("n_total must be non-negative")
    if n_total == 0:
        return np.zeros(w.shape, dtype=np.int64)
    if w.sum() <= 0:
        raise ValueError("weights sum to zero")
    exact = w * (float(n_total) / float(w.sum()))
    q = np.floor(exact).astype(np.int64)
    rem = int(n_total - q.sum())
    if rem > 0:
        order = np.lexsort((np.arange(w.size), -(exact - q)))
        q[order[:rem]] += 1
    if int(q.sum()) != n_total:
        raise AssertionError("proportional apportionment did not reach the requested total")
    return q


def allocate_move_quotas(
    donor_counts: np.ndarray,
    pool_counts: np.ndarray,
    n_move: int,
    max_block_donor_frac: float = MAX_BLOCK_DONOR_FRAC,
) -> np.ndarray:
    """Per-block move quotas proportional to eligible donors, capped twice.

    A block cannot lose more than `max_block_donor_frac` of its eligible donors
    or receive more dots than its own eligible pool.  Quota spilled by a capped
    block is deterministically redistributed to blocks with spare capacity.
    """
    donors = np.asarray(donor_counts, dtype=np.int64).ravel()
    pools = np.asarray(pool_counts, dtype=np.int64).ravel()
    if donors.shape != pools.shape:
        raise ValueError("donor_counts and pool_counts must have the same shape")
    if n_move <= 0:
        raise ValueError("n_move must be positive")
    cap = np.minimum(pools, np.ceil(max_block_donor_frac * donors).astype(np.int64))
    cap = np.maximum(cap, 0)
    active = np.flatnonzero(donors > 0)
    if int(cap[active].sum()) < n_move:
        raise ValueError(
            f"block capacity {int(cap[active].sum())} < requested moves {n_move}; "
            "reduce the dose or enlarge the eligible pool"
        )
    q = np.zeros(donors.size, dtype=np.int64)
    # Iterative water-fill: allocations are proportional to donor counts among blocks
    # that still have capacity.  This differs from a single global allocation because
    # a capped block's quota must be re-assigned while keeping the exact total.
    blocked = np.zeros(donors.size, dtype=bool)
    for _ in range(donors.size + 2):
        short = int(n_move - q.sum())
        if short == 0:
            break
        eligible = active[~blocked[active] & ((cap[active] - q[active]) > 0)]
        if eligible.size == 0:
            raise ValueError("no block has remaining capacity during quota allocation")
        weights = donors[eligible].astype(np.float64)
        add = _proportional_exact(weights, short)
        room = cap[eligible] - q[eligible]
        over = np.maximum(add - room, 0)
        add = np.minimum(add, room)
        q[eligible] += add
        for idx in eligible[over > 0]:
            q[idx] = cap[idx]
            blocked[idx] = True
    if int(q.sum()) != n_move:
        raise ValueError(f"quota allocation produced {int(q.sum())} != {n_move}")
    if np.any(q > cap):
        raise AssertionError("quota exceeds a donor or pool capacity")
    return q


@dataclass
class _CreditState:
    active: np.ndarray
    support: np.ndarray
    cover: np.ndarray
    second: np.ndarray
    owner: np.ndarray
    offsets: np.ndarray
    kernel: np.ndarray
    offset_flat: np.ndarray
    pad: int
    width_padded: int


def _build_state(dots: np.ndarray, support: np.ndarray, radius: int = R_PX) -> _CreditState:
    parent = np.asarray(dots, dtype=bool)
    sup = np.asarray(support, dtype=bool)
    if parent.shape != sup.shape:
        raise ValueError("dots and support must share a shape")
    pad = int(radius)
    active = np.pad(parent, pad, constant_values=False)
    supp = np.pad(sup, pad, constant_values=False)
    offs, kval = kernel_offsets(radius)
    hp, wp = active.shape
    cover = np.zeros(hp * wp, dtype=np.float64)
    second = np.zeros_like(cover)
    owner = np.full(hp * wp, -1, dtype=np.int64)
    offset_flat = offs[:, 0] * wp + offs[:, 1]
    st = _CreditState(active.ravel(), supp.ravel(), cover, second, owner,
                      offs, kval, offset_flat, pad, wp)
    for idx in np.flatnonzero(st.active).tolist():
        for j in range(offset_flat.size):
            nb = idx + int(offset_flat[j])
            if not st.support[nb]:
                continue
            kv = float(st.kernel[j])
            if kv > st.cover[nb]:
                st.second[nb] = st.cover[nb]
                st.cover[nb] = kv
                st.owner[nb] = idx
            elif kv > st.second[nb]:
                st.second[nb] = kv
    return st


def _exclusive_loss(st: _CreditState, idx: int) -> float:
    loss = 0.0
    for j in range(st.offset_flat.size):
        nb = idx + int(st.offset_flat[j])
        if st.owner[nb] == idx:
            loss += float(st.cover[nb] - st.second[nb])
    return round(loss, 9)


def _recompute_pixel(st: _CreditState, nb: int) -> None:
    if not st.support[nb]:
        return
    c1 = c2 = 0.0
    own = -1
    for k2 in range(st.offset_flat.size):
        src = nb - int(st.offset_flat[k2])
        if st.active[src]:
            kv = float(st.kernel[k2])
            if kv > c1:
                c2 = c1
                c1 = kv
                own = src
            elif kv > c2:
                c2 = kv
    st.cover[nb] = c1
    st.second[nb] = c2
    st.owner[nb] = own


def _remove_dot(st: _CreditState, idx: int) -> float:
    if not st.active[idx]:
        raise ValueError("attempted to remove an inactive dot")
    loss = _exclusive_loss(st, idx)
    st.active[idx] = False
    # Recompute every support neighbour, not only pixels this dot owned: the removed
    # dot may have been the SECOND-best contributor, in which case `second` is stale
    # and a later owner's exclusive loss would be overstated.
    for j in range(st.offset_flat.size):
        nb = idx + int(st.offset_flat[j])
        if st.support[nb]:
            _recompute_pixel(st, nb)
    return loss


def _marginal_gain(st: _CreditState, idx: int) -> float:
    gain = 0.0
    for j in range(st.offset_flat.size):
        nb = idx + int(st.offset_flat[j])
        if st.support[nb]:
            diff = float(st.kernel[j]) - float(st.cover[nb])
            if diff > 0.0:
                gain += diff
    return round(gain, 9)


def _add_dot(st: _CreditState, idx: int) -> float:
    if st.active[idx]:
        raise ValueError("attempted to add an already active dot")
    gain = _marginal_gain(st, idx)
    st.active[idx] = True
    for j in range(st.offset_flat.size):
        nb = idx + int(st.offset_flat[j])
        if not st.support[nb]:
            continue
        kv = float(st.kernel[j])
        if kv > st.cover[nb]:
            st.second[nb] = st.cover[nb]
            st.cover[nb] = kv
            st.owner[nb] = idx
        elif kv > st.second[nb]:
            st.second[nb] = kv
    return gain


def kernel_gap_reallocate(
    parent_mask: np.ndarray,
    support_mask: np.ndarray,
    dist_cat: np.ndarray,
    n_move: int,
    block_px: int = BLOCK_PX,
    min_added_cat_dist_px: float = MIN_ADDED_CAT_DIST,
    max_block_donor_frac: float = MAX_BLOCK_DONOR_FRAC,
) -> tuple[np.ndarray, dict]:
    """Move `n_move` dots within their own 5 km blocks at fixed count.

    Drops are the block's lowest exclusive R=3 support-credit parent dots;
    additions are the same block's highest marginal R=3 support-credit H19-5
    pixels.  Blocks are processed in row-major order, so earlier additions can
    only reduce the gain attributed to later additions (never inflate it).
    """
    parent = np.asarray(parent_mask, dtype=bool)
    support = np.asarray(support_mask, dtype=bool)
    dcat = np.asarray(dist_cat, dtype=np.float64)
    if parent.shape != support.shape or parent.shape != dcat.shape:
        raise ValueError("parent, support and dist_cat must share a shape")
    if not np.all(~parent | support):
        raise ValueError("every parent dot must lie on the declared support")
    if n_move <= 0:
        raise ValueError("n_move must be positive")

    H, W = parent.shape
    bid, block_ids, grid = block_index(parent.shape, block_px)
    donor_mask = parent & (dcat >= min_added_cat_dist_px)
    pool_mask = support & ~parent & (dcat >= min_added_cat_dist_px)
    donor_counts = np.bincount(bid[donor_mask], minlength=block_ids.size)
    pool_counts = np.bincount(bid[pool_mask], minlength=block_ids.size)
    if donor_counts.sum() < n_move:
        raise ValueError(f"only {int(donor_counts.sum())} eligible donors for {n_move} moves")
    quotas = allocate_move_quotas(donor_counts, pool_counts, n_move, max_block_donor_frac)

    pad = R_PX
    hp, wp = H + 2 * pad, W + 2 * pad
    state = _build_state(parent, support, R_PX)
    parent_padded = np.pad(parent, pad, constant_values=False).ravel()
    removed_idx: list[int] = []
    added_idx: list[int] = []
    lost_credit = 0.0
    gained_credit = 0.0
    remove_gain_list: list[float] = []
    add_gain_list: list[float] = []

    for blk in np.flatnonzero(quotas > 0):
        need = int(quotas[blk])
        by, bx = divmod(int(blk), int(grid[1]))
        y0, y1 = by * block_px, min(H, (by + 1) * block_px)
        x0, x1 = bx * block_px, min(W, (bx + 1) * block_px)
        block = np.zeros((H, W), dtype=bool)
        block[y0:y1, x0:x1] = True

        donors = np.argwhere(donor_mask & block)
        if donors.shape[0] < need:
            raise ValueError(f"block {blk} has {donors.shape[0]} donors < quota {need}")
        donor_flat = ((donors[:, 0] + pad) * wp + donors[:, 1] + pad).astype(np.int64)
        heap = [(_exclusive_loss(state, int(i)), int(i)) for i in donor_flat.tolist()]
        heapq.heapify(heap)
        taken = 0
        while taken < need:
            if not heap:
                raise RuntimeError(f"donor heap exhausted in block {blk}")
            stale_loss, idx = heapq.heappop(heap)
            if not state.active[idx] or parent_padded[idx] == 0:
                continue
            cur_loss = _exclusive_loss(state, idx)
            if cur_loss > stale_loss + 1e-12:
                heapq.heappush(heap, (cur_loss, idx))
                continue
            lost_credit += _remove_dot(state, idx)
            remove_gain_list.append(cur_loss)
            removed_idx.append(idx)
            taken += 1

        recipients = np.argwhere(pool_mask & block)
        recip_flat = ((recipients[:, 0] + pad) * wp + recipients[:, 1] + pad).astype(np.int64)
        recip_flat = np.asarray([i for i in recip_flat.tolist()
                                 if not state.active[i] and not parent_padded[i]], dtype=np.int64)
        if recip_flat.size < need:
            raise ValueError(f"block {blk} has {recip_flat.size} free recipient pixels < quota {need}")
        heap = [(-_marginal_gain(state, int(i)), int(i)) for i in recip_flat.tolist()]
        heapq.heapify(heap)
        placed = 0
        while placed < need:
            if not heap:
                raise RuntimeError(f"recipient heap exhausted in block {blk}")
            stale_neg, idx = heapq.heappop(heap)
            if state.active[idx] or parent_padded[idx]:
                continue
            cur_gain = _marginal_gain(state, idx)
            if cur_gain < -stale_neg - 1e-12:
                heapq.heappush(heap, (-cur_gain, idx))
                continue
            gained_credit += _add_dot(state, idx)
            add_gain_list.append(cur_gain)
            added_idx.append(idx)
            placed += 1

    active = state.active.reshape(hp, wp)[pad:pad + H, pad:pad + W].copy()
    removed = parent & ~active
    added = active & ~parent
    if int(active.sum()) != int(parent.sum()):
        raise AssertionError(f"fixed-count invariant violated: {int(active.sum())} != {int(parent.sum())}")
    if int(removed.sum()) != n_move or int(added.sum()) != n_move:
        raise AssertionError(f"move count invariant violated: removed={removed.sum()}, added={added.sum()}")
    if np.any(added & ~pool_mask) or np.any(removed & ~donor_mask):
        raise AssertionError("a moved dot lies outside its donor/pool mask")
    if np.any(added & (dcat < min_added_cat_dist_px)):
        raise AssertionError("an addition violates the catalogue collar")
    before_counts = np.bincount(bid[parent], minlength=block_ids.size)
    after_counts = np.bincount(bid[active], minlength=block_ids.size)
    if not np.array_equal(before_counts, after_counts):
        raise AssertionError("per-block dot count changed; the edit is not a pure spacing edit")
    moved_by_block = np.bincount(bid[removed], minlength=block_ids.size)
    if not np.array_equal(moved_by_block, quotas):
        raise AssertionError("actual per-block moves differ from the allocated quotas")

    eligible_blocks = donor_counts > 0
    shares = moved_by_block[eligible_blocks] / donor_counts[eligible_blocks]
    return active, {
        "n_move": int(n_move),
        "removed_dots": int(removed.sum()),
        "added_dots": int(added.sum()),
        "retained_dots": int((parent & active).sum()),
        "symmetric_difference_px": int((parent ^ active).sum()),
        "mass_shifted_pct_of_r0": 100.0 * float(n_move) / float(parent.sum()),
        "pct_changed_symmetric": 100.0 * float((parent ^ active).sum()) / float(parent.sum()),
        "block_px": int(block_px),
        "block_grid": [int(grid[0]), int(grid[1])],
        "n_eligible_donors": int(donor_counts.sum()),
        "n_eligible_pool_px": int(pool_counts.sum()),
        "blocks_with_moves": int((moved_by_block > 0).sum()),
        "max_moves_in_one_block": int(moved_by_block.max()),
        "move_share_p05": round(float(np.percentile(shares, 5)), 6) if shares.size else 0.0,
        "move_share_median": round(float(np.median(shares)), 6) if shares.size else 0.0,
        "move_share_p95": round(float(np.percentile(shares, 95)), 6) if shares.size else 0.0,
        "move_share_max": round(float(shares.max()), 6) if shares.size else 0.0,
        "lost_support_credit": round(float(lost_credit), 4),
        "gained_support_credit": round(float(gained_credit), 4),
        "net_support_credit": round(float(gained_credit - lost_credit), 4),
        "mean_loss_per_removed": round(float(np.mean(remove_gain_list)), 6) if remove_gain_list else 0.0,
        "mean_gain_per_added": round(float(np.mean(add_gain_list)), 6) if add_gain_list else 0.0,
        "quota": quotas,
        "block_counts_parent": before_counts,
        "block_counts_removed": moved_by_block,
        "block_counts_added": np.bincount(bid[added], minlength=block_ids.size),
        "block_counts_after": after_counts,
        "seed_used_in_variant_construction": None,
        "tie_break": "flat padded raster index ascending; block order row-major",
        "min_added_catalogue_distance_px": float(dcat[added].min()),
    }


def parent_fit(claimed_dti: float = 0.2778, mass: int = 37_654, truth_px: int = 65_000,
               mean_mass_credit: float = 0.44, alpha: float = 0.2) -> dict:
    """Solve the brief's DTI algebra at the CLAIMED parent score for one (G, M) guess."""
    m_sum = float(mean_mass_credit) * float(mass)
    beta = 1.0 - alpha
    t = claimed_dti * (alpha * (mass - m_sum) + beta * truth_px) / (1.0 - alpha * claimed_dti)
    d = alpha * t + alpha * (mass - m_sum) + beta * truth_px
    return {"T": float(t), "D": float(d), "S": float(mass), "M": float(m_sum), "G": float(truth_px)}


def fixed_count_delta(net_support_credit: float, support_precision: float, fit: dict,
                      claimed_dti: float = 0.2778) -> float:
    """Exact first-order DTI delta for dT only: S and M are held fixed.

    Removed and added dots both sit on the same support proxy, so their expected
    max-kernel-to-truth terms cancel (`dM=0`).  This is a MODEL bracket, not a score.
    """
    dt = float(support_precision) * float(net_support_credit)
    dm = 0.0
    ds = 0.0
    t, s, m, d = fit["T"], fit["S"], fit["M"], fit["D"]
    before = t / d
    after_num = t + dt
    after_den = d + 0.2 * dt + 0.2 * ds - 0.2 * dm
    return float(after_num / after_den - before) if after_den > 0 else 0.0


def prediction_bracket(net_support_credit: float,
                       claimed_dti: float = 0.2778,
                       mass: int = 37_654) -> dict:
    """Point and range over unobservable truth size, mean mass credit and precision."""
    truth_grid = (20_000, 65_000, 100_000)
    mean_credit_grid = (0.20, 0.44, 0.60)
    precision_grid = (0.10, 0.20, 0.35)
    values: list[float] = []
    for g in truth_grid:
        for mc in mean_credit_grid:
            fit = parent_fit(claimed_dti, mass, g, mc)
            for p in precision_grid:
                values.append(fixed_count_delta(net_support_credit, p, fit, claimed_dti))
    point_fit = parent_fit(claimed_dti, mass, 65_000, 0.44)
    return {
        "point": round(fixed_count_delta(net_support_credit, 0.20, point_fit, claimed_dti), 6),
        "low": round(min(values), 6),
        "high": round(max(values), 6),
        "grid": {
            "truth_px": list(truth_grid),
            "mean_mass_credit": list(mean_credit_grid),
            "support_precision": list(precision_grid),
            "point": {"truth_px": 65_000, "mean_mass_credit": 0.44, "support_precision": 0.20},
        },
        "assumption": "S and M fixed; net H19-5 support credit transfers to truth at the stated precision",
    }
