"""AXIS=MASS, ADD direction: region-even, block-budgeted additions to R0.

Why this exists
---------------
Every *valid* MASS rung in `ledger/submissions.csv` is a DROP (shadow 10/20/30/40/48 %
and a credit-blind random 40 %). The add half of the dose curve has never been built
validly: the FIFO-ranked add rungs were withdrawn because the parent's stored visit
order places every added cell in a northern grid strip (IR90-20). The brief's own
MASS recipe ("add the next-ranked 10 %") therefore has no valid implementation yet.

The brief's algebra gives the decision rule for one added unit-mass dot:

    DTI = T / (0.2T + 0.2(S - M) + 0.8|G|)

    dDTI = [ E * (D - 0.2T) - 0.2T * (1 - c) ] / D**2,      D = denominator

so an addition pays if and only if its exclusive truth credit `E` exceeds
`0.2T/(D - 0.2T) * (1 - c)` -- about 0.056 at the parent's claimed 0.2778. Unlike a
deletion, an addition can never reduce `T` (T is a max over dots), so the downside of
an add rung is bounded by the mass penalty alone. That asymmetry is why this axis is
worth a slot: it is the only untested arm whose failure mode is cheap.

Region evenness
---------------
Quotas are proportional to each 5 km block's own R0 count and capped at +50 % of that
count, with zero quota where R0 has zero dots. Additions therefore follow the parent's
own regional distribution instead of re-ranking the grid: this is the repair proposed
in `SLOT_PLAN.md` after IR90-20, not a new geography.

All functions are pure numpy and operate on pixel indices; no truth, no label, and no
leaderboard value enters the placement.
"""
from __future__ import annotations

import numpy as np

BLOCK_PX = 50  # 5 km at the 100 m grid; same block size as the removal evenness gate
CAP_FRAC = 0.5  # no block may gain more than half of its own parent count


def n_blocks(shape: tuple[int, int], block_px: int = BLOCK_PX) -> tuple[int, int]:
    h, w = shape
    return (h - 1) // block_px + 1, (w - 1) // block_px + 1


def block_counts(mask: np.ndarray, block_px: int = BLOCK_PX) -> np.ndarray:
    """Count `mask` pixels per block -> (n_block_rows, n_block_cols) int64 array."""
    m = np.asarray(mask, dtype=bool)
    nr, nc = n_blocks(m.shape, block_px)
    h, w = m.shape
    pad_h, pad_w = nr * block_px - h, nc * block_px - w
    padded = np.pad(m, ((0, pad_h), (0, pad_w)), constant_values=False)
    return padded.reshape(nr, block_px, nc, block_px).sum(axis=(1, 3)).astype(np.int64)


def allocate_quotas(
    counts: np.ndarray,
    capacity: np.ndarray,
    n_add: int,
    cap_frac: float = CAP_FRAC,
    max_rounds: int = 200,
) -> np.ndarray:
    """Per-block integer addition quotas, proportional to `counts`, capped and exact.

    Deterministic: floor shares first, then single units to the largest fractional
    remainders (ties broken by flat block index). Blocks whose parent count is zero
    receive nothing; no block is asked for more than `capacity` or
    `floor(cap_frac * counts)` additions.
    """
    counts = np.asarray(counts, dtype=np.int64).ravel()
    capacity = np.asarray(capacity, dtype=np.int64).ravel()
    if counts.shape != capacity.shape:
        raise ValueError("counts and capacity must share a shape")
    if n_add <= 0:
        raise ValueError("n_add must be positive")
    cap = np.minimum(capacity, np.floor(cap_frac * counts).astype(np.int64))
    cap = np.maximum(cap, 0)
    if int(cap.sum()) < n_add:
        raise ValueError(
            f"capacity {int(cap.sum())} < requested additions {n_add}: the block budget "
            "cannot deliver this dose without exceeding the caps"
        )
    q = np.zeros(counts.shape[0], dtype=np.int64)
    for _ in range(max_rounds):
        short = int(n_add - q.sum())
        if short == 0:
            break
        room = cap - q
        weight = np.where(room > 0, counts.astype(np.float64), 0.0)
        total = float(weight.sum())
        if total <= 0.0:
            raise ValueError("no block has remaining capacity for the requested dose")
        ideal = short * weight / total
        add = np.minimum(np.floor(ideal).astype(np.int64), room)
        q += add
        short = int(n_add - q.sum())
        if short > 0:
            frac = np.where((cap - q) > 0, ideal - np.floor(ideal), -1.0)
            order = np.lexsort((np.arange(frac.size), -frac))
            for idx in order[:short]:
                if (cap[idx] - q[idx]) > 0:
                    q[idx] += 1
    if int(q.sum()) != n_add:
        raise ValueError(f"quota allocation produced {int(q.sum())} != {n_add} additions")
    return q


def fifo_pick_within_blocks(
    eligible_mask: np.ndarray,
    rank: np.ndarray,
    quotas: np.ndarray,
    block_px: int = BLOCK_PX,
) -> tuple[np.ndarray, np.ndarray]:
    """Take the lowest-FIFO-rank eligible cells per block, up to that block's quota.

    `rank` is the parent's recorded 8-connected FIFO-BFS visit order. The global order
    is geographic (IR90-20); restricting it to a per-block quota is what makes the
    selection region-even.
    """
    elig = np.asarray(eligible_mask, dtype=bool)
    q = np.asarray(quotas, dtype=np.int64).ravel()
    nr, nc = n_blocks(elig.shape, block_px)
    ny, nx = np.nonzero(elig)
    bid = (ny // block_px) * nc + (nx // block_px)
    rk = np.asarray(rank, dtype=np.float64)[ny, nx]
    order = np.lexsort((rk, bid))
    taken_y: list[np.ndarray] = []
    taken_x: list[np.ndarray] = []
    start, n = 0, order.size
    while start < n:
        cur = bid[order[start]]
        end = start
        while end < n and bid[order[end]] == cur:
            end += 1
        k = int(q[cur]) if 0 <= cur < q.size else 0
        sel = order[start : start + k]
        if sel.size:
            taken_y.append(ny[sel])
            taken_x.append(nx[sel])
        start = end
    if not taken_y:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    return np.concatenate(taken_y), np.concatenate(taken_x)


def kernel_offsets(radius: int = 3) -> list[tuple[int, int, float]]:
    out: list[tuple[int, int, float]] = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            d = float(np.hypot(dy, dx))
            k = max(0.0, 1.0 - d / float(radius))
            if k > 0.0:
                out.append((dy, dx, k))
    return out


def coverage(dots: np.ndarray, support: np.ndarray, radius: int = 3) -> np.ndarray:
    """Best kernel credit per pixel on `support` (max over dots), zero elsewhere."""
    cov = np.zeros(dots.shape, dtype=np.float32)
    dotf = np.asarray(dots, dtype=np.float32)
    buf = np.zeros_like(cov)
    h, w = cov.shape
    for dy, dx, k in kernel_offsets(radius):
        buf.fill(0.0)
        ys0, ys1 = max(0, dy), min(h, h + dy)
        xs0, xs1 = max(0, dx), min(w, w + dx)
        buf[ys0:ys1, xs0:xs1] = dotf[ys0 - dy : ys1 - dy, xs0 - dx : xs1 - dx] * k
        np.maximum(cov, buf, out=cov)
    cov[~np.asarray(support, dtype=bool)] = 0.0
    return cov


def _window_gains(
    cov: np.ndarray,
    sup: np.ndarray,
    ys: np.ndarray,
    xs: np.ndarray,
    radius: int = 3,
) -> np.ndarray:
    """Marginal support credit for each candidate pixel (vectorised over candidates)."""
    offs = kernel_offsets(radius)
    h, w = cov.shape
    gains = np.zeros(ys.size, dtype=np.float64)
    for dy, dx, k in offs:
        yy = ys + dy
        xx = xs + dx
        ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        if not ok.any():
            continue
        yyc = np.clip(yy, 0, h - 1)
        xxc = np.clip(xx, 0, w - 1)
        contrib = np.where(sup[yyc, xxc], np.maximum(0.0, k - cov[yyc, xxc]), 0.0)
        gains += np.where(ok, contrib, 0.0)
    return gains


def gapmax_pick_within_blocks(
    eligible_mask: np.ndarray,
    support: np.ndarray,
    dots: np.ndarray,
    quotas: np.ndarray,
    radius: int = 3,
    block_px: int = BLOCK_PX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Greedy maximum marginal kernel credit inside each block's quota.

    The coverage array is global and updated after every pick, so a cell's marginal
    credit reflects earlier picks in its own block and in neighbouring blocks (the
    kernel crosses block edges). Returns (ys, xs, marginal_credit_at_pick).
    """
    elig = np.asarray(eligible_mask, dtype=bool).copy()
    sup = np.asarray(support, dtype=bool)
    h, w = elig.shape
    q = np.asarray(quotas, dtype=np.int64).ravel()
    nr, nc = n_blocks(elig.shape, block_px)
    cov = coverage(dots, sup, radius)
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
        alive = np.ones(gy.size, dtype=bool)
        for _ in range(need):
            gains = _window_gains(cov, sup, gy[alive], gx[alive], radius)
            idx_alive = np.flatnonzero(alive)
            pick = int(np.argmax(gains))
            i = int(idx_alive[pick])
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


def full_support_credit(ys: np.ndarray, xs: np.ndarray, support: np.ndarray, radius: int = 3) -> np.ndarray:
    """Total support credit inside each dot's kernel (not exclusive): `s_i` of the model."""
    sup = np.asarray(support, dtype=bool)
    h, w = sup.shape
    out = np.zeros(ys.size, dtype=np.float64)
    for dy, dx, k in kernel_offsets(radius):
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        out += np.where(ok, np.where(sup[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)], k, 0.0), 0.0)
    return out


def addition_report(
    added: np.ndarray,
    parent: np.ndarray,
    block_px: int = BLOCK_PX,
    min_block_dots: int = 20,
) -> dict:
    """Per-5 km-block addition shares: the region-evenness statistic for an ADD rung."""
    add = np.asarray(added, dtype=bool)
    par = np.asarray(parent, dtype=bool)
    counts = block_counts(par, block_px)
    adds = block_counts(add, block_px)
    dose = float(add.sum()) / float(par.sum())
    big = counts >= min_block_dots
    share = np.divide(adds, counts, out=np.zeros(counts.shape, dtype=float), where=counts > 0)
    s = share[big]
    ys, xs = np.nonzero(add)
    py, px = np.nonzero(par)
    return {
        "block_px": int(block_px),
        "block_km": round(block_px * 0.1, 3),
        "nominal_dose": round(dose, 6),
        "blocks_with_parent_dots": int((counts > 0).sum()),
        "blocks_with_20plus_dots": int(big.sum()),
        "blocks_receiving_additions": int((adds > 0).sum()),
        "blocks_with_zero_additions_among_20plus": int(((adds == 0) & big).sum()),
        "add_share_p05": round(float(np.percentile(s, 5)), 4) if s.size else 0.0,
        "add_share_median": round(float(np.median(s)), 4) if s.size else 0.0,
        "add_share_p95": round(float(np.percentile(s, 95)), 4) if s.size else 0.0,
        "add_share_max": round(float(s.max()), 4) if s.size else 0.0,
        "adds_into_blocks_with_zero_parent_dots": int(adds[counts == 0].sum()),
        "added_bbox_y": [int(ys.min()), int(ys.max())] if ys.size else [],
        "added_bbox_x": [int(xs.min()), int(xs.max())] if xs.size else [],
        "added_centroid_yx": [round(float(ys.mean()), 2), round(float(xs.mean()), 2)] if ys.size else [],
        "parent_centroid_yx": [round(float(py.mean()), 2), round(float(px.mean()), 2)],
    }


def addition_evenness_gate(
    report: dict,
    p05_floor: float = 0.25,
    p95_ceiling: float = 4.0,
    max_zero_share: float = 0.10,
    max_block_share: float = CAP_FRAC + 1e-9,
) -> bool:
    """Fail closed if the additions stop looking like a scaled copy of the parent."""
    dose = report["nominal_dose"]
    if dose <= 0:
        return False
    zero_share = report["blocks_with_zero_additions_among_20plus"] / max(1, report["blocks_with_20plus_dots"])
    return (
        report["add_share_p05"] >= p05_floor * dose
        and report["add_share_p95"] <= p95_ceiling * dose
        and report["add_share_max"] <= max_block_share
        and report["adds_into_blocks_with_zero_parent_dots"] == 0
        and zero_share <= max_zero_share
    )


def parent_fit(claimed_dti: float = 0.2778, mass: int = 37654, truth_px: int = 65000,
               mean_mass_credit: float = 0.44, alpha: float = 0.2) -> dict:
    """Solve the brief's algebra for (T, D) at R0's claimed score, for one (G, M) guess.

    M = mean_mass_credit * mass is the assumed sum of each dot's best kernel credit to
    any truth pixel. Both G and M are unobservable without truth, so callers bracket
    them; this function is a bracket element, never a fitted parameter.
    """
    m_sum = mean_mass_credit * mass
    t = claimed_dti * (alpha * (mass - m_sum) + (1.0 - alpha) * truth_px) / (1.0 - alpha * claimed_dti)
    d = alpha * t + alpha * (mass - m_sum) + (1.0 - alpha) * truth_px
    return {"T": float(t), "D": float(d), "S": int(mass), "M": float(m_sum), "G": int(truth_px)}


def predicted_add_delta(
    exclusive_credit: np.ndarray,
    full_credit: np.ndarray,
    field_precision: float,
    fit: dict,
) -> float:
    """MODEL: sum of per-addition DTI contributions under the support-precision assumption.

    `exclusive_credit[i]` is the marginal kernel credit addition i gains on the H19-5
    support; `full_credit[i]` is the same dot's total support credit inside its kernel.
    Truth credit is taken as `field_precision * credit`, i.e. support precision =
    P(a support pixel is a new-fault truth pixel).
    """
    e = np.asarray(exclusive_credit, dtype=np.float64)
    s = np.asarray(full_credit, dtype=np.float64)
    t, d = fit["T"], fit["D"]
    if d <= 0:
        raise ValueError("degenerate parent fit")
    e_truth = field_precision * e
    c = np.clip(field_precision * s, 0.0, 1.0)
    per_dot = (e_truth * (d - 0.2 * t) - 0.2 * t * (1.0 - c)) / (d * d)
    return float(per_dot.sum())


def prediction_bracket(
    exclusive_credit: np.ndarray,
    full_credit: np.ndarray,
    claimed_dti: float = 0.2778,
    mass: int = 37654,
    truth_px_grid: tuple[int, ...] = (60988, 65000, 90000),
    mean_mass_credit_grid: tuple[float, ...] = (0.20, 0.44, 0.60),
    precision_grid: tuple[float, ...] = (0.10, 0.20, 0.35),
    point: tuple[int, float, float] = (65000, 0.44, 0.20),
) -> dict:
    """Point MODEL plus the min/max over the unobservable (G, M, support precision) grid."""
    values = []
    for g in truth_px_grid:
        for m in mean_mass_credit_grid:
            fit = parent_fit(claimed_dti, mass, g, m)
            for p in precision_grid:
                values.append(predicted_add_delta(exclusive_credit, full_credit, p, fit))
    fit_point = parent_fit(claimed_dti, mass, point[0], point[1])
    return {
        "point": round(predicted_add_delta(exclusive_credit, full_credit, point[2], fit_point), 6),
        "low": round(min(values), 6),
        "high": round(max(values), 6),
        "grid": {
            "truth_px": list(truth_px_grid),
            "mean_mass_credit": list(mean_mass_credit_grid),
            "support_precision": list(precision_grid),
            "point": {"truth_px": point[0], "mean_mass_credit": point[1], "support_precision": point[2]},
        },
        "fit_point": fit_point,
    }


def support_precision_estimate(total_credit: float, support_px: int, mean_kernel_on_truth: float = 0.7) -> float:
    """Implied P(support pixel is a truth pixel) from the parent's total credit.

    T = sum over truth of the best dot's credit, so truth pixels covered ~ T / mean_k.
    Dividing by the support size gives the precision the MODEL grid is centred on.
    """
    if support_px <= 0 or mean_kernel_on_truth <= 0:
        raise ValueError("support_px and mean_kernel_on_truth must be positive")
    return float(total_credit / (support_px * mean_kernel_on_truth))
