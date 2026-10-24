"""AXIS=SPACING: local kernel-scale respacing of crowded dots at fixed count.

Why this module exists
----------------------
The brief's SPACING axis asks how dots are *arranged* at matched count
(lattice vs Poisson-disk vs along-strike; lowest priority). Those three
global arrangements are already built by sibling sessions (GEMSDOE86
`lattice`/`poisson-disk`/`along-strike`/`pdiskc16`/`latticec16`/`strikec16`,
GEMSDOE88 `poisson28`/`lattice4px`/`strike`, GEMSDOE91 ring-2
`spread40`/`clump40`/`jitter40` at 2.0-2.24 px), so this module tests the
one arrangement question none of them asks: at R0's own count, own support
and own geography, does moving a dot out of a crowded kernel disk into the
nearest uncovered stretch of the *same* support pay?

Measured on the byte-identical R0 rebuild: every dot's nearest neighbour
is >= 2.828 px (the parent d2.8 thinning survives), yet 50.5% of dots have
another dot within the 3 px metric kernel and the mean dot has 2.82 other
dots within 6 px, i.e. inside the zone where two triangular kernels
contest the same truth pixels. Under the brief's algebra
``DTI = T / (0.2T + 0.2(S - M) + 0.8|G|)`` with ``T`` a max over dots, a
second dot deep inside a neighbour's disk supplies little new ``T`` while
paying the same mass. Respacing keeps ``S`` (and the count) exactly fixed,
so any live change is arrangement, not mass -- the control the MASS
shadow ladder (delete, no refill) and the MASS q50 ladder (add, no
delete) each lack on their own.

The operator
------------
* Removal ranking is pure spacing: each R0 dot's crowding is the sum of
  triangular-kernel overlaps ``max(0, 1 - d/6)`` from every other dot
  within 6 px (two kernel radii: the full contest zone). Most crowded
  first; ties break on nearest-neighbour distance, then raster position.
  No label, catalogue distance, block prior or landform enters the rank.
* Each removed dot is respaced *locally*: the replacement is the eligible
  support pixel within ``window_px`` (15 px = 1.5 km) of the removed dot
  with the largest exact marginal triangular-kernel credit against the
  current dot set, subject to >= ``min_sep_px`` (2.8 px, the parent's own
  thinning distance) from every current dot and >= 3 px from the
  catalogue. Windows expand 15 -> 30 -> 60 px only when a window holds no
  legal pixel; a dot that cannot be placed even at 60 px stays put and
  the next crowded dot is tried, so the dose is exact or the build fails.
* Doses are snapshots of one nested sequential process (relocate 5%,
  10%, 15% of R0), so the three files differ only in dose.

What this module does NOT do
----------------------------
* It never looks at a score, leaderboard or test label; the catalogue is
  only a hard exclusion for replacements (>= 3 px, Hard Constraint #4's
  no-new-mass convention; untouched R0 dots keep R0's 2.236 px floor).
* It does not re-rank geography: replacements stay within 1.5 km of the
  dot they replace in the primary window, so block-scale density, relief
  mix and strand geography are inherited, not redesigned.
* Support credit (H19-5) is a truth *proxy* used to place replacements;
  a positive support-credit balance is arithmetic, not evidence about
  live DTI, and predictions are discounted for exactly that reason.

All functions are pure numpy/scipy and operate on pixel-centre coords.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

R_KERNEL = 3.0       # triangular metric kernel radius, brief s2
CONTEST_PX = 6.0     # two kernel radii: disks contest credit inside this
MIN_SEP_PX = 2.8     # parent's own d2.8 thinning distance
WINDOW_PX = 15       # primary respacing window (1.5 km)
EXPANSIONS_PX = (15, 30, 60)


def crowding_scores(pts: np.ndarray, contest_px: float = CONTEST_PX,
                    radius: float = R_KERNEL) -> np.ndarray:
    """Sum of kernel-disk overlaps from all other dots within `contest_px`.

    crowding_j = sum_{i != j, d_ij < 2*radius} (1 - d_ij / (2*radius))

    A dot alone on its strand scores 0; a dot in a tight cluster scores
    near the number of overlapping neighbours. Pure geometry: no truth,
    no catalogue, no support enters.
    """
    pts = np.asarray(pts, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) == 0:
        raise ValueError("pts must be a non-empty (n, 2) array")
    tree = cKDTree(pts)
    pairs = tree.query_pairs(r=float(contest_px), output_type="ndarray")
    crowd = np.zeros(len(pts), dtype=np.float64)
    if pairs.size:
        d = np.hypot(*(pts[pairs[:, 0]] - pts[pairs[:, 1]]).T)
        w = np.maximum(0.0, 1.0 - d / (2.0 * radius))
        np.add.at(crowd, pairs[:, 0], w)
        np.add.at(crowd, pairs[:, 1], w)
    return crowd


def removal_order(pts: np.ndarray, crowd: np.ndarray | None = None) -> np.ndarray:
    """Indices of dots from most to least crowded (deterministic).

    Sort keys: crowding desc, nearest-neighbour distance asc, row, col.
    The order is a spacing rank only -- it is not a probability that a
    dot is wrong, and it is computed once on the parent (nested doses).
    """
    pts = np.asarray(pts, dtype=np.float64)
    if crowd is None:
        crowd = crowding_scores(pts)
    crowd = np.asarray(crowd, dtype=np.float64)
    if len(crowd) != len(pts):
        raise ValueError("crowd must match pts")
    if len(pts) > 1:
        nn, _ = cKDTree(pts).query(pts, k=2)
        nn_dist = nn[:, 1]
    else:
        nn_dist = np.full(len(pts), np.inf)
    order = np.lexsort((pts[:, 1], pts[:, 0], nn_dist, -crowd))
    return order


def _kernel_offsets(radius: float = R_KERNEL) -> tuple[np.ndarray, np.ndarray]:
    r = int(np.ceil(radius))
    offs, cred = [], []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dy, dx))
            if d < radius:
                offs.append((dy, dx))
                cred.append(1.0 - d / radius)
    return np.asarray(offs, dtype=np.int64), np.asarray(cred, dtype=np.float64)


def relocate(dots: np.ndarray, pool: np.ndarray, order_pts: np.ndarray,
             doses: tuple[int, ...], window_px: int = WINDOW_PX,
             expansions_px: tuple[int, ...] = EXPANSIONS_PX,
             min_sep_px: float = MIN_SEP_PX, radius: float = R_KERNEL) -> dict:
    """Sequentially respace the most crowded dots; snapshot at each dose.

    `pool` = pixels a replacement may occupy (support, in-footprint,
    catalogue-clear, not a parent dot). `order_pts` = parent dot coords in
    removal order. Returns {dose: mask} plus the paired move list
    [(removed_yx, added_yx, window_used), ...] in process order.
    Raises if a dose cannot be reached even after trying every ordered dot.
    """
    dots = np.asarray(dots, dtype=bool)
    pool = np.asarray(pool, dtype=bool) & ~dots
    if dots.shape != pool.shape:
        raise ValueError("dots and pool shapes differ")
    doses = tuple(sorted(int(d) for d in doses))
    if not doses or doses[0] <= 0:
        raise ValueError("doses must be positive")
    from src.reach import credit_map

    current = dots.copy()
    credit = credit_map(current, radius).astype(np.float64)
    pad = int(np.ceil(radius))
    padded = np.pad(credit, pad, mode="constant", constant_values=0.0)
    offs, cred = _kernel_offsets(radius)
    offs_l, cred_l = offs.tolist(), cred.tolist()
    h, w = dots.shape

    def patch_credit_from_scratch(cy: int, cx: int) -> None:
        """Recompute credit in the kernel patch after a removal."""
        y0, y1 = max(0, cy - pad), min(h, cy + pad + 1)
        x0, x1 = max(0, cx - pad), min(w, cx + pad + 1)
        sub_dots = current[y0:y1, x0:x1]
        ys, xs = np.nonzero(sub_dots)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        best = np.zeros((y1 - y0, x1 - x0), dtype=np.float64)
        for dy_, dx_ in zip(ys.tolist(), xs.tolist()):
            d = np.hypot(yy - (y0 + dy_), xx - (x0 + dx_))
            best = np.maximum(best, np.maximum(0.0, 1.0 - d / radius))
        padded[y0 + pad:y1 + pad, x0 + pad:x1 + pad] = best

    def stamp_add(cy: int, cx: int) -> None:
        for (dy, dx), k in zip(offs_l, cred_l):
            yy, xx = cy + dy, cx + dx
            if 0 <= yy < h and 0 <= xx < w and padded[yy + pad, xx + pad] < k:
                padded[yy + pad, xx + pad] = k

    def try_place(ry: int, rx: int) -> tuple[int, int, int] | None:
        """Best legal replacement near (ry, rx); None if no window works."""
        for win in expansions_px:
            if win == window_px or win in expansions_px:
                pass
            y0, y1 = max(0, ry - win), min(h, ry + win + 1)
            x0, x1 = max(0, rx - win), min(w, rx + win + 1)
            cand = np.argwhere(pool[y0:y1, x0:x1] & ~current[y0:y1, x0:x1])
            if cand.size == 0:
                continue
            cand[:, 0] += y0
            cand[:, 1] += x0
            dist_removed = np.hypot(cand[:, 0] - ry, cand[:, 1] - rx)
            cand = cand[dist_removed <= win]
            if cand.shape[0] == 0:
                continue
            # Minimum separation from every current dot: only dots within
            # min_sep + 1 px of a candidate can violate it, and all such
            # dots lie inside the expanded window slice.
            ey0, ey1 = max(0, ry - win - pad - 1), min(h, ry + win + pad + 2)
            ex0, ex1 = max(0, rx - win - pad - 1), min(w, rx + win + pad + 2)
            dys, dxs = np.nonzero(current[ey0:ey1, ex0:ex1])
            dot_y = dys + ey0
            dot_x = dxs + ex0
            if len(dot_y):
                d2 = (cand[:, 0:1] - dot_y[None, :]) ** 2 + (cand[:, 1:2] - dot_x[None, :]) ** 2
                nearest = np.sqrt(d2.min(axis=1))
            else:
                nearest = np.full(cand.shape[0], np.inf)
            ok = nearest >= min_sep_px
            if not ok.any():
                continue
            cand = cand[ok]
            dist_removed = np.hypot(cand[:, 0] - ry, cand[:, 1] - rx)
            gains = np.zeros(cand.shape[0], dtype=np.float64)
            for (dy, dx), k in zip(offs_l, cred_l):
                gains += np.maximum(0.0, k - padded[cand[:, 0] + pad + dy, cand[:, 1] + pad + dx])
            # Max gain; ties: nearer the removed dot, then raster order.
            pick = int(np.lexsort((cand[:, 0] * w + cand[:, 1], dist_removed, -gains))[0])
            return int(cand[pick, 0]), int(cand[pick, 1]), int(win)
        return None

    snapshots: dict[int, np.ndarray] = {}
    moves: list[tuple[tuple[int, int], tuple[int, int], int]] = []
    n_done = 0
    dose_set = set(doses)
    for idx in range(len(order_pts)):
        if n_done >= doses[-1]:
            break
        ry, rx = int(order_pts[idx, 0]), int(order_pts[idx, 1])
        if not current[ry, rx]:
            continue
        current[ry, rx] = False
        patch_credit_from_scratch(ry, rx)
        placed = try_place(ry, rx)
        if placed is None:
            current[ry, rx] = True  # cannot respace this dot; it stays
            patch_credit_from_scratch(ry, rx)
            continue
        ay, ax, win_used = placed
        current[ay, ax] = True
        stamp_add(ay, ax)
        moves.append(((ry, rx), (ay, ax), win_used))
        n_done += 1
        if n_done in dose_set:
            snapshots[n_done] = current.copy()
    missing = [d for d in doses if d not in snapshots]
    if missing:
        raise ValueError(f"respacing exhausted the removal order at {n_done} moves; doses {missing} unreachable")
    return {"snapshots": snapshots, "moves": moves}


def spacing_stats(mask: np.ndarray) -> dict:
    """Nearest-neighbour / kernel-contest summary of a dot mask."""
    pts = np.column_stack(np.nonzero(mask)).astype(np.float64)
    if len(pts) < 2:
        raise ValueError("need at least 2 dots")
    tree = cKDTree(pts)
    nn, _ = tree.query(pts, k=2)
    nn = nn[:, 1]
    within3 = tree.query_ball_point(pts, r=R_KERNEL, return_length=True) - 1
    within6 = tree.query_ball_point(pts, r=CONTEST_PX, return_length=True) - 1
    crowd = crowding_scores(pts)
    return {
        "n_dots": int(len(pts)),
        "nn_min_px": float(nn.min()),
        "nn_median_px": float(np.median(nn)),
        "nn_mean_px": float(nn.mean()),
        "frac_with_neighbour_within_3px": float((within3 > 0).mean()),
        "mean_other_dots_within_3px": float(within3.mean()),
        "mean_other_dots_within_6px": float(within6.mean()),
        "mean_crowding": float(crowd.mean()),
        "total_crowding": float(crowd.sum()),
    }
