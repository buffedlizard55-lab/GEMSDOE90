#!/usr/bin/env python3
"""Rebuild R0 byte-for-byte, then build controlled MASS dose-ladder variants.

Session axis: MASS. The only changed quantity is emitted mass (count), edited along the
parent's own ranking: the deterministic 8-connected FIFO-BFS traversal order recorded in
the d2.8 thinning recipe (GEMSDOE28@src/gems27/thinning.py), recovered pixel-exact in
scripts/build_r0_variants.py. Values (free across the checked sibling ledgers GEMSDOE84-101):

  drop5pct-tail  -- remove the 1,883 lowest-ranked (traversal-tail) R0 dots      (n=35,771)
  add5pct-next   -- add the 1,883 next-ranked suppressed H19-5 support cells     (n=39,537)
  add20pct-next  -- add the 7,531 next-ranked suppressed H19-5 support cells     (n=45,185)

"Next-ranked" = highest-priority cells the parent's greedy 2.8 px thinning did not keep
(suppressed by its own spacing rule), in the same traversal order. Added cells obey the
non-PRUNE floor of Hard Constraint 4 (Euclidean catalogue distance >= 3 px); inherited
parent dots keep their recorded positions (removing them would add a PRUNE change and
confound the dose test - see IRREGULARITIES.md IR90-01/IR90-06). Zero catalogue mass is
absolute. No public-test labels or score endpoints are used. Local GeoTIFFs are written
under ignored `releases/`; do not add them to public Git or any GitHub release.

Run: `.venv/bin/python scripts/build_mass_variants.py --build`
Verify written files: `.venv/bin/python scripts/build_mass_variants.py --verify`
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "MASS"
DATE = "20261023"
R0_DOTS = 37_654

# (value, delta_mass_fraction) - fraction of R0's count, rounded half away from zero.
VARIANTS = (
    ("drop5pct-tail", -0.05),
    ("add5pct-next", 0.05),
    ("add20pct-next", 0.20),
)

# Cross-session (AXIS, value) pairs already built by sibling sessions checked on 2026-10-23
# (ledgers of GEMSDOE84-92 fetched via api.github.com; GEMSDOE93-101 have no ledger file).
SIBLING_OCCUPIED_MASS_VALUES = {
    "+10pct", "-10pct", "-20pct", "m10e", "m10u", "p10",
    "m10minus", "m10plus", "m20minus", "minus10pct", "plus10pct",
    "MASS_D10", "MASS_A10", "MASS_SWAP10",
}


def _load_build_r0() -> object:
    spec = importlib.util.spec_from_file_location("build_r0_variants", ROOT / "scripts" / "build_r0_variants.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


B = _load_build_r0()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def dose_count(fraction: float) -> int:
    return int(round(abs(fraction) * R0_DOTS + 1e-9))


def check_pair_reservations() -> None:
    """Fail closed on any (MASS, value) already present in the local or audited sibling ledgers."""
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("axis") or "").strip().upper() == AXIS:
                local_value = (row.get("value") or "").strip()
                for value, _ in VARIANTS:
                    if local_value == value:
                        raise ValueError(f"duplicate experiment reservation: (MASS, {value}) already exists")
    for value, _ in VARIANTS:
        if value in SIBLING_OCCUPIED_MASS_VALUES:
            raise ValueError(f"duplicate experiment reservation: (MASS, {value}) occupied by a sibling session")


def validate_variant_file(path: Path, expected: np.ndarray, new_dots: np.ndarray, foot: np.ndarray,
                          cat: np.ndarray, distance: np.ndarray, sample_profile: dict, mode: str) -> dict:
    """Format MUST-gates from brief s6, re-read from disk.

    Gate: zero catalogue mass. Newly placed dots must keep >=3 px from the catalogue
    (Hard Constraint 4 floor for non-PRUNE axes). Inherited parent dots retain the
    parent's recorded >=2 px collar (IR90-01/IR90-06); their minimum distance is
    reported, not gated.
    """
    with rasterio_open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs = src.crs
        transform = src.transform
    checks = {
        "crs_matches_sample": crs == sample_profile["crs"],
        "transform_matches_sample": transform == sample_profile["transform"],
        "shape_matches_sample": a.shape == (sample_profile["height"], sample_profile["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(a[foot]).all()),
        "inside_foot_range_0_1": bool(np.all((a[foot] >= 0) & (a[foot] <= 1))),
        "outside_is_nan": bool(np.isnan(a[~foot]).all()) if mode == "nan" else bool(np.all(a[~foot] == 0)),
        "exact_expected_mask_after_disk_read": bool(np.array_equal((a > 0.5) & foot, expected)),
        "zero_catalogue_mass": not bool(np.any((a > 0.5) & cat)),
        "new_dots_min_catalogue_distance_ge_3px": (
            True if not new_dots.any() else float(distance[new_dots].min()) >= 3.0
        ),
        "file_re_read_from_disk": True,
    }
    if not all(checks.values()):
        raise ValueError(f"validator failed for {path.name}: {[k for k, v in checks.items() if not v]}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(((a > 0.5) & foot).sum()),
        "min_catalogue_distance_px": float(distance[(a > 0.5) & foot].min()),
        "new_dots_min_catalogue_distance_px": (
            None if not new_dots.any() else float(distance[new_dots].min())
        ),
        "checks": checks,
    }


def rasterio_open(path: Path):
    import rasterio

    return rasterio.open(path)


def emit(mask: np.ndarray, foot: np.ndarray, template: dict, slug: str, mode: str, temp_path: Path) -> Path:
    return B.emit(mask, foot, template, slug, mode, temp_path)


def credit_components(p: np.ndarray, g: np.ndarray) -> tuple[float, float, float, np.ndarray]:
    """(T, S, M, credit) under src/dti.py assumptions A1/A2, credit returned at every pixel."""
    from src import dti as dti_mod

    p = np.asarray(p, dtype=float)
    truth = np.asarray(g) > 0
    S = float(p.sum())
    credit = np.zeros_like(p)
    if not truth.any():
        return 0.0, S, 0.0, credit
    k_at_dot = dti_mod.kernel(ndi.distance_transform_edt(~truth))
    M = float((p * k_at_dot).sum())
    rows, cols = np.nonzero(p > 0)
    r = dti_mod.R_PX
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    kpatch = dti_mod.kernel(np.hypot(yy, xx))
    H, W = p.shape
    for i, j in zip(rows, cols):
        r0, r1 = max(0, i - r), min(H, i + r + 1)
        c0, c1 = max(0, j - r), min(W, j + r + 1)
        sub = kpatch[r0 - (i - r) : r0 - (i - r) + (r1 - r0), c0 - (j - r) : c0 - (j - r) + (c1 - c0)]
        credit[r0:r1, c0:c1] = np.maximum(credit[r0:r1, c0:c1], p[i, j] * sub)
    T = float(credit[truth].sum())
    return T, S, M, credit


def hide_recover_proxy(p: np.ndarray, g: np.ndarray, tile: int = 64, n_boot: int = 400,
                       seed: int = 20261023) -> dict:
    """REPORT-ONLY hide-and-recover PROXY (brief s6): score the file against withheld
    positives g with the metric-code algebra. 95% CI from a paired spatial tile bootstrap
    on the truth-sum term (S, M held fixed). Never a gate, never a score."""
    from src import dti as dti_mod

    T, S, M, credit = credit_components(p, g)
    truth = np.asarray(g) > 0
    G = int(truth.sum())
    point = dti_mod.dti_from_components(T, S, M, G)
    # per-tile truth credit sums
    H, W = truth.shape
    ty, tx = np.nonzero(truth)
    tile_id = (ty // tile) * ((W + tile - 1) // tile) + (tx // tile)
    tile_t = np.bincount(tile_id, weights=credit[ty, tx])
    n_tiles = int(tile_id.max()) + 1 if tile_id.size else 0
    rng = np.random.default_rng(seed)
    if n_tiles < 2 or G == 0:
        return {"dti": point, "ci95": None, "n_truth_px": G, "n_tiles": n_tiles}
    draws = np.empty(n_boot)
    for b in range(n_boot):
        sample = rng.integers(0, n_tiles, size=n_tiles)
        T_star = float(tile_t[sample].sum())
        draws[b] = dti_mod.dti_from_components(T_star, S, M, G)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {
        "dti": point,
        "ci95": [float(lo), float(hi)],
        "n_truth_px": G,
        "n_tiles": n_tiles,
        "tile_px": tile,
        "n_boot": n_boot,
        "seed": seed,
        "method": "paired spatial-tile bootstrap on the truth-sum credit term; S and M held fixed",
    }


def paired_delta_proxy(p_var: np.ndarray, p_r0: np.ndarray, g: np.ndarray, tile: int = 64,
                       n_boot: int = 400, seed: int = 20261023) -> dict:
    """REPORT-ONLY paired delta of the same PROXY: variant minus R0, same tiles resampled."""
    from src import dti as dti_mod

    T0, S0, M0, c0 = credit_components(p_r0, g)
    T1, S1, M1, c1 = credit_components(p_var, g)
    truth = np.asarray(g) > 0
    G = int(truth.sum())
    point = dti_mod.dti_from_components(T1, S1, M1, G) - dti_mod.dti_from_components(T0, S0, M0, G)
    H, W = truth.shape
    ty, tx = np.nonzero(truth)
    tile_id = (ty // tile) * ((W + tile - 1) // tile) + (tx // tile)
    t0 = np.bincount(tile_id, weights=c0[ty, tx])
    t1 = np.bincount(tile_id, weights=c1[ty, tx])
    n_tiles = int(tile_id.max()) + 1 if tile_id.size else 0
    rng = np.random.default_rng(seed)
    if n_tiles < 2 or G == 0:
        return {"delta": point, "ci95": None, "n_truth_px": G}
    draws = np.empty(n_boot)
    for b in range(n_boot):
        sample = rng.integers(0, n_tiles, size=n_tiles)
        Ts0 = float(t0[sample].sum())
        Ts1 = float(t1[sample].sum())
        draws[b] = dti_mod.dti_from_components(Ts1, S1, M1, G) - dti_mod.dti_from_components(Ts0, S0, M0, G)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {
        "delta": point,
        "ci95": [float(lo), float(hi)],
        "n_truth_px": G,
        "n_tiles": n_tiles,
        "tile_px": tile,
        "n_boot": n_boot,
        "seed": seed,
        "method": "paired spatial-tile bootstrap on the truth-sum credit term; S and M held fixed",
    }


PREDICTIONS = {
    "drop5pct-tail": (
        "-0.002 DTI (MODEL; plausible interval -0.010 to +0.003; not a score)",
        "-0.002",
    ),
    "add5pct-next": (
        "-0.002 DTI (MODEL; plausible interval -0.009 to +0.005; not a score)",
        "-0.002",
    ),
    "add20pct-next": (
        "-0.008 DTI (MODEL; plausible interval -0.020 to +0.004; not a score)",
        "-0.008",
    ),
}


def mechanism_card(value: str, variant_stats: dict) -> dict:
    if value == "drop5pct-tail":
        return {
            "hypothesis": (
                "R0's traversal-tail dots (the last 5% of the parent's own FIFO-BFS selection order) "
                "still carry unique kernel credit on short late-visited strands, so removing them lowers "
                "DTI slightly rather than releasing false-positive mass."
            ),
            "mechanism": (
                "DTI = T / (0.2T + 0.2(S-M) + 0.8|G|). Dropping a dot removes 1 from S (helping the "
                "0.2(S-M) term) but deletes its max-kernel credit wherever it was the best coverer of a "
                "truth pixel (hurting T). The parent's recorded recipe ranks its dots by 8-connected "
                "FIFO-BFS traversal of the H19-5 support; the dropped tranche is the lowest-priority tail "
                f"(visit ranks {variant_stats.get('visit_rank_range')}, n=1,883 of 37,654)."
            ),
            "non_fault_confounder": (
                "FIFO-BFS order is a raster convention (seeds at the first raster pixel of each 8-connected "
                "support component), not geological confidence: tail dots are the far ends of long lineaments "
                "and late chips, where drainage divides and lithologic contacts mimic fault strands. The local "
                "report-only PROXYs lean the same sign (catalogue hide-and-recover delta -0.0003; SGMC control "
                "delta -0.008), but SGMC-mapped faults are not the new-fault truth and neither PROXY is a score."
            ),
            "predicted_live_change": PREDICTIONS[value][0],
            "falsifier": (
                "Paired same-week receipt vs R0: delta >= +0.010 confirms the false-positive regime and "
                "re-opens the sibling -10/-20% rungs; delta <= -0.010 shows the tail carries unique fault "
                "credit and closes the drop direction. |delta| < 0.010 is no evidence under the session rule."
            ),
            "structural_geologist_note": (
                "Read this as a dose rung on the lineage's own selection order, not as a claim that fault "
                "traces end where the traversal ends. Inspect the dropped SE ends and small chips on geology "
                "before any slot is spent."
            ),
        }
    return {
        "hypothesis": (
            "The parent's 2.8 px thinning already suppressed the cells this variant adds; being kernel-redundant "
            "with surviving dots, their marginal max-operator credit is near zero while each still pays full "
            f"false-positive mass, so +{variant_stats['pct_changed']:.0f}% of them lowers DTI slightly."
        ),
        "mechanism": (
            "Added cells are the next-ranked suppressed H19-5 support cells in the parent's own FIFO-BFS order. "
            f"Measured: {variant_stats.get('frac_within_2p8px_of_parent'):.1%} of them lie within 2.8 px of an "
            "existing R0 dot (median 1.0 px), i.e. exactly the pixels the parent's greedy 2.8 px rule did not "
            "keep. Under the metric algebra a dot pays only if its marginal kernel credit exceeds ~0.2*DTI "
            "(about 0.056 at 0.28; lower for line-like truth). Redundant neighbours add S but little T and M."
        ),
        "non_fault_confounder": (
            "Dense multiscale ridge corridors (drainage divides, lithologic contacts, foliation lineaments) "
            "populate H19-5's suppressed cells. The opposite confounder: real fault zones are damage-zone wide "
            "and can carry several parallel strands inside the 300 m kernel, so genuinely useful adds look "
            "redundant and new-fault truth can sit within 300 m of known traces (organizer forum, 2026-10-22)."
        ),
        "predicted_live_change": PREDICTIONS[value][0],
        "falsifier": (
            "Paired same-week receipt vs R0: delta >= +0.010 falsifies the redundancy picture (line-like truth "
            "extends credit along strike) and promotes larger spaced adds; delta <= -0.010 confirms redundancy "
            "and closes the add direction. |delta| < 0.010 is no evidence under the session rule."
        ),
        "structural_geologist_note": (
            "This is a kernel-budget experiment along the parent's own ranking. Review where the added cells "
            "double existing strands (damage-zone width vs raster duplication) before spending a slot."
        ),
    }


def build() -> dict:
    t0 = time.time()
    check_pair_reservations()
    input_receipt = B.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = B.exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~cat)
    h19 = B.read_binary(DATA / B.PIN_PATHS["h19_5"], foot)
    rank = B.fifo_bfs_visit_rank(h19)
    if np.any(rank[h19] < 0) or np.any(rank[~h19] != -1):
        raise RuntimeError("FIFO-BFS ranking failed to cover exactly the H19-5 support")

    pool = h19 & foot & (distance >= 3.0) & ~r0
    py, px_ = np.nonzero(pool)
    pool_ranks = rank[py, px_]
    pool_order = np.argsort(pool_ranks, kind="stable")
    ry, rx = np.nonzero(r0)
    r_ranks = rank[ry, rx]
    tail_order = np.argsort(-r_ranks, kind="stable")  # lowest-ranked first (largest visit rank)

    d_to_r0 = ndi.distance_transform_edt(~r0)
    OUT.mkdir(parents=True, exist_ok=True)
    variants = []
    for value, fraction in VARIANTS:
        k = dose_count(fraction)
        candidate = r0.copy()
        if fraction < 0:
            sel = tail_order[:k]
            removed = np.zeros_like(r0)
            removed[ry[sel], rx[sel]] = True
            candidate &= ~removed
            added = np.zeros_like(r0)
            visit_range = f"{int(r_ranks[sel].min())}-{int(r_ranks[sel].max())} of 0-{int(r_ranks.max())}"
        else:
            if len(pool_order) < k:
                raise ValueError(f"{value}: only {len(pool_order)} eligible cells for {k} added dots")
            sel = pool_order[:k]
            added = np.zeros_like(r0)
            added[py[sel], px_[sel]] = True
            candidate |= added
            removed = np.zeros_like(r0)
            visit_range = f"{int(pool_ranks[sel].min())}-{int(pool_ranks[sel].max())}"
        n_dots = int(candidate.sum())
        expected_n = R0_DOTS + int(round(fraction * R0_DOTS + 1e-9)) if fraction > 0 else R0_DOTS - k
        if n_dots != expected_n:
            raise AssertionError(f"{value}: count {n_dots} != expected {expected_n}")
        if np.any(candidate & cat) or np.any(candidate & ~foot):
            raise AssertionError(f"{value}: catalogue/footprint violation")
        if added.any() and float(distance[added].min()) < 3.0:
            raise AssertionError(f"{value}: placed dot violates the >=3px constraint-4 floor")
        changed = int(np.count_nonzero(candidate ^ r0))
        pct_changed = 100.0 * changed / R0_DOTS
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"{value} changes {pct_changed:.6f}% of R0 (required 1-50%)")

        slug = f"{PARENT}-MASS{value}-{DATE}"
        temp_nan = OUT / f".{slug}-nan.tmp.tif"
        temp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        emit(candidate, foot, template, slug, "nan", temp_nan)
        emit(candidate, foot, template, slug, "zeros", temp_zeros)
        nan_sha = sha256_file(temp_nan)
        sha8 = nan_sha[:8]
        base = OUT / f"{PARENT}-MASS{value}-{DATE}-{sha8}"
        nan_path = base.with_suffix(".tif")
        zeros_path = OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = validate_variant_file(nan_path, candidate, added, foot, cat, distance, template, "nan")
        zeros_audit = validate_variant_file(zeros_path, candidate, added, foot, cat, distance, template, "zeros")

        frac_near = float(np.mean(d_to_r0[added] < 2.8)) if added.any() else float("nan")
        delta = {
            "removed_from_parent": int(removed.sum()),
            "added_dots": int(added.sum()),
            "retained_parent": int((candidate & r0).sum()),
            "symmetric_difference_px": changed,
            "pct_changed_of_R0": pct_changed,
            "n_dots": n_dots,
        }
        stats_extra = {
            "visit_rank_range": visit_range,
            "frac_within_2p8px_of_parent": (float("nan") if frac_near != frac_near else frac_near),
            "pct_changed": pct_changed,
        }
        cards = mechanism_card(value, stats_extra)
        note = f"{PARENT}; MASS {value} (n={n_dots}); predicted {PREDICTIONS[value][1]} DTI MODEL"
        if len(note) > 140:
            raise AssertionError(f"submission note is {len(note)} characters: {note}")
        variants.append({
            "id": base.name,
            "parent": PARENT,
            "axis": AXIS,
            "value": value,
            "n_dots": n_dots,
            "pct_changed": pct_changed,
            "removed_dots": int(removed.sum()),
            "added_dots": int(added.sum()),
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "predicted_change": cards["predicted_live_change"],
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": delta,
            "mechanism_card": cards,
            "ranking_stats": {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in stats_extra.items()},
            "mass_fraction": fraction,
        })

    # REPORT-ONLY proxies (brief s6). Never gates, never scores.
    p_r0 = r0.astype(float)
    cat_truth = cat.astype(float)
    with rasterio_open(DATA / "external/derived_sgmc_faults_100m_u8.tif") as src:
        sgmc_raw = src.read(1)
    sgmc_truth = ((sgmc_raw > 0) & foot & ~cat).astype(float)

    proxy_reports = {
        "catalogue_hide_recover": {
            "status": "REPORT ONLY (PROXY)",
            "description": (
                "Known catalogue pixels are the withheld positives (the builder's hide): every candidate has "
                "zero catalogue mass, so this measures kernel credit to known-trace geometry only. Not new-fault "
                "truth; historical correlation with live scores -0.87..+0.54 (n=12-14). Never a gate."
            ),
            "r0": hide_recover_proxy(p_r0, cat_truth),
            "variants": {},
        },
        "sgmc_control": {
            "status": "REPORT ONLY (PROXY)",
            "description": (
                "SGMC-derived geologic-map fault pixels off the known catalogue used as an alternative "
                "pseudo-truth; checks whether variant deltas are specific to catalogue-like geometry. Never a gate."
            ),
            "r0": hide_recover_proxy(p_r0, sgmc_truth),
        },
        "leakage_canary": {
            "status": "REPORT ONLY",
            "note": (
                "Not re-run this session: identical hash-pinned inputs were canaried on 2026-10-23 "
                "(evidence/build_receipt.json, seed 20261023): 19 supplied bands, all 60,988 catalogue "
                "positives + 250,000 seeded off-catalogue footprint pixels, median-fill after sentinel "
                "masking; max symmetric AUC 0.5700 (geod_2ndinv) < 0.90 trigger."
            ),
        },
    }
    for v in variants:
        v_mask = _rebuild_variant_mask(r0, v, pool, pool_order, tail_order, ry, rx, py, px_)
        p_var = v_mask.astype(float)
        proxy_reports["catalogue_hide_recover"]["variants"][v["value"]] = {
            "proxy": hide_recover_proxy(p_var, cat_truth),
            "delta_vs_r0": paired_delta_proxy(p_var, p_r0, cat_truth),
        }
        proxy_reports["sgmc_control"]["variants"] = proxy_reports["sgmc_control"].get("variants", {})
        proxy_reports["sgmc_control"]["variants"][v["value"]] = {
            "proxy": hide_recover_proxy(p_var, sgmc_truth),
            "delta_vs_r0": paired_delta_proxy(p_var, p_r0, sgmc_truth),
        }

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha(),
        "axis": AXIS,
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": B.R0_ZEROS_SHA,
            "nan_sha256": B.R0_NAN_SHA,
            **parent_stats,
        },
        "manifest": {
            "manifest_path": "registry/data_manifest.json",
            "verified_count": len(input_receipt),
            "all_pins_rechecked": True,
            "files": input_receipt,
        },
        "ranking": {
            "recipe": (
                "8-connected FIFO-BFS visit order over binary H19-5 support (the parent's recorded "
                "d2.8 thinning ranking; pixel-exact reproduction recorded in evidence/r0_rebuild_receipt.json)"
            ),
            "is_geological_probability": False,
            "drop_rule": "largest visit ranks among R0's dots (lowest-ranked = traversal tail)",
            "add_rule": (
                "smallest visit ranks among H19-5 support cells not in R0 with d_cat >= 3.0 px "
                "(next-ranked cells suppressed by the parent's 2.8 px thinning)"
            ),
            "pool_size_d_cat_ge_3": int(pool.sum()),
            "add_pool_frac_within_2p8px_of_r0": float(np.mean(d_to_r0[pool] < 2.8)),
        },
        "proxy_reports": proxy_reports,
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
    }
    return result


def _rebuild_variant_mask(r0, v, pool, pool_order, tail_order, ry, rx, py, px_) -> np.ndarray:
    candidate = r0.copy()
    fraction = v["mass_fraction"]
    kk = dose_count(fraction)
    if fraction < 0:
        sel = tail_order[:kk]
        candidate[ry[sel], rx[sel]] = False
    else:
        sel = pool_order[:kk]
        candidate[py[sel], px_[sel]] = True
    return candidate


def write_ledger_rows(result: dict) -> None:
    path = ROOT / "ledger" / "submissions.csv"
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    existing_shas = set()
    existing_pairs = set()
    for row in csv.DictReader(text.splitlines()):
        if row.get("sha256"):
            existing_shas.add(row["sha256"].strip())
        if row.get("sha256_zeros"):
            existing_shas.add(row["sha256_zeros"].strip())
        existing_pairs.add(((row.get("parent") or "").strip(), (row.get("axis") or "").strip(),
                            (row.get("value") or "").strip()))
    fields = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
              "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
              "receipt_score", "predicted_change", "date", "form_note", "notes"]
    rows = []
    for v in result["variants"]:
        if v["sha256"] in existing_shas or v["sha256_zeros"] in existing_shas:
            raise ValueError(f"sha256 already in ledger: {v['id']}")
        if (v["parent"], v["axis"], v["value"]) in existing_pairs:
            raise ValueError(f"(parent, axis, value) already in ledger: {v['value']}")
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)", "encoding": "nan primary; zeros fallback",
            "n_dots": v["n_dots"], "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"], "parent": v["parent"],
            "axis": v["axis"], "value": v["value"], "status": "BUILT", "receipt": "N",
            "receipt_score": "", "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": "receipt_score/date to be filled by human; agent never submits",
        })
    import io

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    # The appended block must not repeat the header.
    body = out.getvalue().split("\n", 1)[1]
    path.write_text(text + body, encoding="utf-8")


def write_machine_cards(result: dict) -> None:
    cards = {
        "schema_version": 1,
        "session": "arena/307b04fc-gemsdoe90",
        "parent": PARENT,
        "axis": AXIS,
        "variants": [
            {"id": v["id"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
            for v in result["variants"]
        ],
    }
    (ROOT / "ledger" / "mechanism_cards_mass.json").write_text(json.dumps(cards, indent=2) + "\n")


def update_reservations(result: dict) -> None:
    path = ROOT / "ledger" / "experiment_reservations.json"
    data = json.loads(path.read_text())
    data["mass_axis_20261023"] = {
        "checked_utc": "2026-10-23",
        "scope": (
            "Cross-session MASS dose values checked against sibling ledgers GEMSDOE84-92 "
            "(fetched via api.github.com 2026-10-23; GEMSDOE93-101 have no ledger/submissions.csv). "
            "Exact (AXIS, value) reuse prohibited; selection policy is part of a value's identity."
        ),
        "occupied_values": sorted(SIBLING_OCCUPIED_MASS_VALUES),
        "selected_values": [v["value"] for v in result["variants"]],
        "interpretation": (
            "-10%/+10%/-20% doses (and a 10% swap) are built by GEMSDOE84/85/86/87/88/89/91/92 under "
            "several selection policies. The selected rungs fill the missing parts of one dose ladder "
            "on the parent's own recorded-recipe ranking (FIFO-BFS traversal): -5% tail drop and +5%/+20% "
            "next-ranked adds. Best-effort owner-repo audit, not proof of every submission ever made."
        ),
    }
    path.write_text(json.dumps(data, indent=2) + "\n")


def verify() -> int:
    check_pair_reservations_ok = True
    try:
        check_pair_reservations()
    except ValueError:
        # On re-verify the local ledger now contains our rows; compare against the receipt instead.
        check_pair_reservations_ok = False
    receipt = json.loads((ROOT / "evidence" / "mass_build_receipt.json").read_text())
    template, foot, cat, r0, parent_stats = B.exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~cat)
    h19 = B.read_binary(DATA / B.PIN_PATHS["h19_5"], foot)
    rank = B.fifo_bfs_visit_rank(h19)
    pool = h19 & foot & (distance >= 3.0) & ~r0
    py, px_ = np.nonzero(pool)
    pool_order = np.argsort(rank[py, px_], kind="stable")
    ry, rx = np.nonzero(r0)
    tail_order = np.argsort(-rank[ry, rx], kind="stable")
    for v in receipt["variants"]:
        candidate = _rebuild_variant_mask(r0, v, pool, pool_order, tail_order, ry, rx, py, px_)
        added = candidate & ~r0
        for mode in ("nan", "zeros"):
            audit = validate_variant_file(ROOT / v["files"][mode]["path"], candidate, added,
                                          foot, cat, distance, template, mode)
            if audit["sha256"] != v["files"][mode]["sha256"]:
                raise ValueError(f"re-read SHA mismatch for {v['id']} {mode}")
            temp_dir = ROOT / ".cache" / "verify_mass_bytes"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / f"{v['id']}-{mode}.tif"
            try:
                emit(candidate, foot, template, v["id"], mode, temp_path)
                if sha256_file(temp_path) != audit["sha256"]:
                    raise ValueError(f"byte-for-byte deterministic re-emit failed for {v['id']} {mode}")
            finally:
                temp_path.unlink(missing_ok=True)
    verified = {
        "verified_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha(),
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "r0_rebuilt_byte_identically": True,
        "pair_reservation_check_at_verify": "skipped (rows already recorded)" if not check_pair_reservations_ok else "clean",
    }
    receipt["self_check"] = verified
    (ROOT / "evidence" / "mass_build_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Verified {len(receipt['variants'])} MASS variant pairs from disk; R0 rebuilt byte-identically")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.build:
        result = build()
        evidence = ROOT / "evidence" / "mass_build_receipt.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(result, indent=2) + "\n")
        write_ledger_rows(result)
        write_machine_cards(result)
        update_reservations(result)
        print(f"Built {len(result['variants'])} MASS variants from exact R0; evidence -> {evidence.relative_to(ROOT)}")
        for v in result["variants"]:
            print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.3f}% changed, sha256={v['sha256']}")
        return 0
    return verify()


if __name__ == "__main__":
    raise SystemExit(main())
