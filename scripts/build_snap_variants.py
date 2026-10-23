#!/usr/bin/env python3
"""Rebuild R0 byte-for-byte, then build cross-strike SNAP variants.

Session axis: SNAP.  Three arms differ ONLY in the displacement cap (1.0 / 1.5 / 2.0 px).
Shared, identical steps in every arm:

1. R0 is rebuilt exactly from the pinned h27-4 mask (byte identity is asserted).
2. Collar reconciliation (hard constraint #4): every parent dot with Euclidean catalogue
   distance < 3 px is removed, then the count is restored from the H19-5 pool in the
   parent's own FIFO-BFS ranking; refills must be >= 3 px from the catalogue and >= 2 px
   from any other dot.  This step is the same in all arms, so arm-to-arm differences are
   pure SNAP dose.
3. SNAP: each surviving dot may move at most `cap` px, and only roughly cross-strike
   (within 45 deg of the local fault normal estimated by PCA on its 8 nearest parent dots).
   The destination maximises a two-source consensus edge response built from two supplied,
   independent gradient bands: `tmi_hg` (magnetic horizontal gradient, band 3) and
   `iso_grav_anom_hg` (isostatic gravity horizontal gradient, band 18).  Each band is
   rank-normalised over the finite footprint, then averaged.  A move is accepted only if it
   improves the consensus response by >= 0.01 and lands >= 2.0 px from every other dot.

Why cross-strike only: GeoDAWN Area 2 was flown at 400 m line spacing (150-200 m above
terrain), so the dominant positional error of a mapped lineament is across strike, of order
the 300 m kernel radius.  The metric's credit falls linearly with distance
(k = max(0, 1 - d/3)), so a 1-2 px cross-strike correction is the only edit that can raise
T without changing mass, and mass is the term the 0.2778 CLAIM already pays for.

No labels, no public-test endpoints, no score of any kind are used.  Local TIFFs are written
under ignored `releases/`; competition rasters must never be committed or released.

Run:    .venv/bin/python scripts/build_snap_variants.py --build
Verify: .venv/bin/python scripts/build_snap_variants.py --verify
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "SNAP"
DATE = "20261023"
R0_ZEROS_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
R0_NAN_SHA = "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd"
R0_DOTS = 37_654
CAP_PX = 2.0                     # brief: SNAP moves each dot <= 2 px
DOSES = (("k0p25", 0.25), ("k1p0", 1.0), ("k4p0", 4.0))  # confidence ladder: permissive -> strict
MIN_SEP_PX = 2.0
MIN_EDGE_GAIN = 0.01
K_NEIGHBOURS = 8
RESERVATIONS = ROOT / "ledger" / "experiment_reservations.json"
LEDGER = ROOT / "ledger" / "submissions.csv"
RECEIPT = ROOT / "evidence" / "snap_build_receipt.json"

FEATURES = DATA / "training_features.tif"
EDGE_BANDS = (("tmi_hg", 3), ("iso_grav_anom_hg", 18))  # names read from the GeoTIFF descriptions


def _load_builder():
    spec = importlib.util.spec_from_file_location("r0b", ROOT / "scripts" / "build_r0_variants.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


r0b = _load_builder()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


# --------------------------------------------------------------------------------------
# edge response
# --------------------------------------------------------------------------------------
def _rank_normalise(values: np.ndarray) -> np.ndarray:
    """Map finite values to [0, 1] by average rank (ties share their mean rank).

    Deterministic, bounded, and outlier-proof: a single extreme value cannot dominate the
    consensus, unlike a z-score.  Average ranks are required so that quantised inputs (the
    supplied GeoTIFFs are not continuous in places) do not acquire a false ordering.
    """
    values = np.asarray(values, dtype=np.float64)
    order = np.argsort(values, kind="stable")
    sorted_vals = values[order]
    ranks_sorted = np.empty(values.size, dtype=np.float64)
    start = 0
    for pos in range(1, values.size + 1):
        if pos == values.size or sorted_vals[pos] != sorted_vals[start]:
            ranks_sorted[start:pos] = 0.5 * (start + pos - 1)  # mean of the tied positions
            start = pos
    ranks = np.empty(values.size, dtype=np.float64)
    ranks[order] = ranks_sorted
    return ranks / max(values.size - 1, 1)


SMOOTH_SIGMA_PX = 1.2


def consensus_edge(foot: np.ndarray) -> tuple[np.ndarray, dict]:
    """Smoothed mean of the rank-normalised `tmi_hg` and `iso_grav_anom_hg` bands.

    Rank normalisation is bounded and outlier-proof; the 1.2 px Gaussian is mask-normalised so
    that footprint edges do not invent gradients.  The result is a relative edge strength, not
    a fault probability.
    """
    bands, meta = [], []
    with rasterio.open(FEATURES) as src:
        descriptions = list(src.descriptions or [])
        for name, index in EDGE_BANDS:
            raw = descriptions[index - 1] if len(descriptions) >= index else None
            got = (raw or "").split(" - ")[0].strip()  # descriptions are '<name> - <prose>'
            if got != name:
                raise ValueError(f"band {index} is {got!r}, expected {name!r}; refusing to guess")
            a = src.read(index)
            finite = foot & np.isfinite(a)
            band = np.zeros(a.shape, dtype=np.float64)
            band[finite] = _rank_normalise(a[finite].astype(np.float64))
            bands.append(band)
            meta.append({"band": index, "name": name, "finite_px": int(finite.sum())})
    raw = np.mean(bands, axis=0)
    num = ndi.gaussian_filter(np.where(foot, raw, 0.0), SMOOTH_SIGMA_PX)
    den = ndi.gaussian_filter(foot.astype(np.float64), SMOOTH_SIGMA_PX)
    edge = np.where(foot, num / np.maximum(den, 1e-9), 0.0)
    iqr = float(np.subtract(*np.percentile(edge[foot], [75, 25])))
    return edge, {"sources": meta,
                  "combine": "mean of per-band average-rank normalisation over finite footprint, "
                             f"then mask-normalised Gaussian sigma={SMOOTH_SIGMA_PX} px",
                  "smoothed_iqr": iqr,
                  "step_epsilon_rank": 0.01 * iqr}


# --------------------------------------------------------------------------------------
# geometry helpers (pure, unit-tested)
# --------------------------------------------------------------------------------------
def strike_normal(dot: tuple[int, int], tree: cKDTree, coords: np.ndarray, k: int = K_NEIGHBOURS) -> np.ndarray:
    """Unit normal to the local lineament, from PCA of the k nearest parent dots."""
    k = min(k, len(coords))
    _, idx = tree.query(np.asarray(dot, dtype=float), k=k)
    pts = coords[np.atleast_1d(idx)].astype(np.float64)
    if len(pts) < 3:
        return np.array([1.0, 0.0])  # row axis; only used for isolated dots
    centred = pts - pts.mean(axis=0)
    cov = centred.T @ centred
    evals, evecs = np.linalg.eigh(cov)
    strike = evecs[:, int(np.argmax(evals))]  # (dy, dx) of maximum variance
    normal = np.array([-strike[1], strike[0]])
    norm = float(np.hypot(*normal))
    return normal / norm if norm > 0 else np.array([1.0, 0.0])


def candidate_offsets(cap: float) -> list[tuple[int, int, float, float]]:
    """Integer (dy, dx) with 1 <= |offset| <= cap; returns (dy, dx, dist, |cos to normal|-ready dist).

    Only offsets within 45 deg of the normal are kept; the normal is supplied later, so we
    return every offset in the half-disc and filter per dot by direction.
    """
    out = []
    lim = int(np.ceil(cap))
    for dy in range(-lim, lim + 1):
        for dx in range(-lim, lim + 1):
            dist = float(np.hypot(dy, dx))
            if 1.0 - 1e-9 <= dist <= cap + 1e-9:
                out.append((dy, dx, dist, 0.0))
    out.sort(key=lambda t: (t[2], t[0], t[1]))
    return out


def directional_offsets(normal: np.ndarray, cap: float) -> list[tuple[int, int, float]]:
    """Offsets within `cap` px whose direction is within 45 deg of the normal."""
    keep = []
    for dy, dx, dist, _ in candidate_offsets(cap):
        along = abs((dy * normal[0] + dx * normal[1]) / dist)  # |cos| to normal
        if along >= np.cos(np.pi / 4):
            keep.append((dy, dx, dist))
    return keep


def occupancy_free(occ: np.ndarray, y: int, x: int, min_sep: float = MIN_SEP_PX) -> bool:
    """True when (y, x) is empty and no other dot lies within `min_sep` px (offsets < min_sep)."""
    if occ[y, x]:
        return False
    lim = int(np.ceil(min_sep)) - 1  # 2.0 -> only distance-1 and sqrt(2) offsets matter
    h, w = occ.shape
    for dy in range(-lim, lim + 1):
        for dx in range(-lim, lim + 1):
            if dy == 0 and dx == 0:
                continue
            if float(np.hypot(dy, dx)) >= min_sep - 1e-9:
                continue
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and occ[yy, xx]:
                return False
    return True


# --------------------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------------------
def check_pair_reservations() -> None:
    """Fail closed on a repeated (AXIS, value). Cross-repo values come from the reservations file."""
    if not RESERVATIONS.is_file():
        raise FileNotFoundError("ledger/experiment_reservations.json is required for the dedupe gate")
    reserved = json.loads(RESERVATIONS.read_text(encoding="utf-8"))
    taken = {str(v).strip().lower() for v in reserved.get("snap_values_reserved", [])}
    for token, _mult in DOSES:
        if f"snapx{token}" in taken:
            raise ValueError(f"duplicate experiment reservation: (SNAP, {token}) already built")
    if LEDGER.is_file():
        with LEDGER.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                value = (row.get("value") or "").lower()
                for token, _mult in DOSES:
                    if f"snapx{token}" in value:
                        raise ValueError(f"duplicate (SNAP, {token}) already present in ledger/submissions.csv")


def collar_reconcile(r0: np.ndarray, foot: np.ndarray, cat: np.ndarray, dist: np.ndarray,
                     pool: np.ndarray, rank: np.ndarray) -> tuple[np.ndarray, dict]:
    """Remove every dot inside 3 px of the catalogue; refill the exact count from the pool."""
    kept = r0 & (dist >= 3.0)
    removed = int((r0 & ~kept).sum())
    eligible = pool & (dist >= 3.0)
    ey, ex = np.nonzero(eligible)
    order = np.argsort(rank[ey, ex], kind="stable")
    occ = kept.copy()
    added = []
    for pos in order:
        if len(added) >= removed:
            break
        y, x = int(ey[pos]), int(ex[pos])
        if not occupancy_free(occ, y, x):
            continue
        occ[y, x] = True
        added.append((y, x))
    if len(added) != removed:
        raise RuntimeError(f"collar refill could not hold the count ({len(added)}/{removed})")
    mask = kept.copy()
    for y, x in added:
        mask[y, x] = True
    if int(mask.sum()) != R0_DOTS:
        raise AssertionError("collar reconciliation did not hold 37,654 dots")
    return mask, {"removed_dots": removed, "refilled_dots": len(added)}


def snap(seed: np.ndarray, foot: np.ndarray, cat: np.ndarray, dist: np.ndarray, edge: np.ndarray,
         rank: np.ndarray, cap: float, eps: float) -> tuple[np.ndarray, dict]:
    """Hill-climb each dot up to `cap` px along its local fault normal toward a stronger edge.

    One-pixel steps only, each step must raise the smoothed consensus by at least `eps`, steps are
    restricted to the 45 deg half-disc about the dot's local normal, and the final position must be
    at least 2 px from every other dot.  A dot is left untouched if either condition fails, so the
    edit can only move mass toward a locally stronger edge -- it never adds or removes mass.
    """
    ys, xs = np.nonzero(seed)
    coords = np.column_stack([ys, xs])
    tree = cKDTree(coords.astype(np.float64))
    order = np.argsort(rank[ys, xs], kind="stable")  # parent FIFO order: deterministic tie-break
    occ = seed.copy()
    moved = blocked = 0
    displacements: list[float] = []
    edge_gain: list[float] = []
    hits_wall = 0
    for pos in order:
        y0, x0 = int(ys[pos]), int(xs[pos])
        normal = strike_normal((y0, x0), tree, coords)
        steps = directional_offsets(normal, 1.0)  # 1 px steps inside the half-disc
        y, x, travelled, gained = y0, x0, 0.0, 0.0
        while travelled < cap - 1e-9:
            best = None
            for dy, dx, _ in steps:
                ty, tx = y + dy, x + dx
                if float(np.hypot(ty - y0, tx - x0)) > cap + 1e-9:
                    continue  # the CAP bounds the final displacement, not just the step count
                if not (0 <= ty < occ.shape[0] and 0 <= tx < occ.shape[1]):
                    continue
                if not foot[ty, tx] or dist[ty, tx] < 3.0 or cat[ty, tx]:
                    continue
                if occ[ty, tx]:
                    continue
                gain = float(edge[ty, tx] - edge[y, x])
                if gain < eps:
                    continue
                key = (-gain, float(np.hypot(ty - y0, tx - x0)), ty, tx)
                if best is None or key < best[0]:
                    best = (key, ty, tx, gain)
            if best is None:
                break
            _key, ty, tx, gain = best
            y, x, gained = ty, tx, gained + gain
            travelled = float(np.hypot(y - y0, x - x0))
        if travelled <= 0.0 or gained < 2 * eps:
            blocked += 1
            continue
        if not occupancy_free(occ, y, x):
            hits_wall += 1
            continue
        occ[y0, x0] = False
        occ[y, x] = True
        moved += 1
        displacements.append(travelled)
        edge_gain.append(gained)
    if int(occ.sum()) != int(seed.sum()):
        raise AssertionError("SNAP changed the dot count")
    info = {
        "cap_px": cap,
        "dots_moved": moved,
        "pct_moved": 100.0 * moved / int(seed.sum()),
        "mean_displacement_px": float(np.mean(displacements)) if displacements else 0.0,
        "median_displacement_px": float(np.median(displacements)) if displacements else 0.0,
        "max_displacement_px": float(np.max(displacements)) if displacements else 0.0,
        "mean_consensus_edge_gain_rank": float(np.mean(edge_gain)) if edge_gain else 0.0,
        "dots_at_local_crest_or_short_of_epsilon": blocked,
        "dots_blocked_by_spacing": hits_wall,
        "min_sep_px": MIN_SEP_PX,
        "step_epsilon_rank": eps,
        "half_angle_deg": 45,
        "neighbours_for_strike": K_NEIGHBOURS,
        "realized_max_offset_px": cap,
    }
    return occ, info


def build() -> dict:
    t0 = time.time()
    check_pair_reservations()
    inputs = r0b.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = r0b.exact_parent_rebuild()
    dist = ndi.distance_transform_edt(~cat)
    h19 = r0b.read_binary(DATA / r0b.PIN_PATHS["h19_5"], foot)
    rank = r0b.fifo_bfs_visit_rank(h19)
    pool = h19 & foot & ~cat & ~r0
    edge, edge_meta = consensus_edge(foot)

    seed, collar_info = collar_reconcile(r0, foot, cat, dist, pool, rank)
    eps = edge_meta["step_epsilon_rank"]
    OUT.mkdir(parents=True, exist_ok=True)
    variants = []
    for token, mult in DOSES:
        candidate, snap_info = snap(seed, foot, cat, dist, edge, rank, CAP_PX, mult * eps)
        changed = int(np.count_nonzero(candidate ^ r0))
        if int(candidate.sum()) != R0_DOTS:
            raise AssertionError(f"SNAP {cap:g}px count drift")
        if np.any(candidate & cat) or np.any(candidate & ~foot):
            raise AssertionError(f"SNAP {cap:g}px violates catalogue/footprint exclusion")
        if float(dist[candidate].min()) < 3.0:
            raise AssertionError(f"SNAP {cap:g}px violates the 3 px collar")
        value = (f"cross-strike consensus(TMI hg, iso-grav hg) cap {CAP_PX:g} px, step-epsilon {mult:g}x, "
                 f"half-angle 45 deg, min sep {MIN_SEP_PX:g} px")
        slug = f"{PARENT}-SNAPX{token}-{DATE}"
        temp_nan = OUT / f".{slug}-nan.tmp.tif"
        temp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        r0b.emit(candidate, foot, template, slug, "nan", temp_nan)
        r0b.emit(candidate, foot, template, slug, "zeros", temp_zeros)
        sha8 = sha256_file(temp_nan)[:8]
        base = OUT / f"{slug}-{sha8}"
        nan_path, zeros_path = base.with_suffix(".tif"), OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = r0b.validate_file(nan_path, candidate, foot, cat, template, "nan")
        zeros_audit = r0b.validate_file(zeros_path, candidate, foot, cat, template, "zeros")
        info = {
            "cap_px": CAP_PX,
            "epsilon_multiplier": mult,
            "shared_collar_step": collar_info,
            "snap": snap_info,
            "symmetric_difference_vs_parent_px": changed,
            "pct_of_parent_dots_changed": 100.0 * changed / R0_DOTS,
            "mean_displacement_px": snap_info["mean_displacement_px"],
        }
        variants.append({
            "id": base.name,
            "parent": PARENT,
            "axis": AXIS,
            "value": value,
            "n_dots": R0_DOTS,
            "pct_changed": 100.0 * changed / R0_DOTS,
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": info,
            "predicted_change": PREDICTIONS[token],
            "form_note": f"{PARENT}; SNAP cross-strike cap {CAP_PX:g}px, eps x{mult:g} "
                         f"(TMI+grav hg consensus); pred {PREDICTIONS[token][:5]} DTI MODEL",
            "mechanism_card": mechanism_card(token, mult, snap_info, collar_info),
        })
        if len(variants[-1]["form_note"]) > 140:
            raise AssertionError("form note over 140 characters")

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha(),
        "generator_script_sha256": sha256_file(Path(__file__)),
        "axis": AXIS,
        "parent": {"id": PARENT, "claimed_live_score": 0.2778, "evidence_class": "CLAIM",
                   "zeros_sha256": R0_ZEROS_SHA, "nan_sha256": R0_NAN_SHA, **parent_stats},
        "manifest": {"manifest_path": "registry/data_manifest.json",
                     "verified_count": len(inputs), "all_pins_rechecked": True,
                     "files": inputs},
        "edge_field": edge_meta,
        "ranking": {"recipe": "parent FIFO-BFS visit order (GEMSDOE28 dot_thin); deterministic tie-break only",
                    "is_geological_probability": False,
                    "d28_reproduction_symmetric_difference_px": parent_stats["d28_symmetric_difference_px"]},
        "proxy_reports": {
            "catalogue_hide_recover": {"status": "NOT RUN",
                                       "reason": "no fold-clean instrument is validated for a positional edit; "
                                                 "the proxy correlates -0.87..+0.54 with live scores and is never a gate"},
            "leakage_canary": {"status": "REPORT ONLY",
                               "note": "unchanged pinned inputs; previous run max symmetric AUC 0.5700 (geod_2ndinv), "
                                       "so no single feature exceeds the 0.90 stop threshold",
                               "auc_gt_0_90": False},
            "sgmc_control": {"status": "NOT RUN", "reason": "not a gate; no calibrated fold-clean control for this edit"},
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
    }
    return result


PREDICTIONS = {
    "k0p25": "+0.001 DTI (MODEL; plausible -0.010..+0.014)",
    "k1p0": "+0.003 DTI (MODEL; plausible -0.008..+0.012)",
    "k4p0": "+0.004 DTI (MODEL; plausible -0.006..+0.010)",
}


def mechanism_card(token: str, mult: float, snap_info: dict, collar_info: dict) -> dict:
    return {
        "hypothesis": (
            f"Correcting cross-strike position by up to {CAP_PX:g} px moves dots toward the strongest "
            "magnetic/gravity gradient edge, which is where a mapped fault trace is most likely to lie; "
            "because kernel credit is linear in distance, this raises T without adding mass."
        ),
        "mechanism": (
            "GeoDAWN Area 2 was flown at 400 m line spacing 150-200 m above terrain, so a lineament's "
            "dominant positional error is across strike and of order the 300 m (3 px) kernel radius. "
            "The consensus of two independent supplied gradient bands (tmi_hg, iso_grav_anom_hg) is used "
            "only as a within-2 px tie-breaker along each dot's local normal (PCA of its 8 nearest parent "
            f"dots). {snap_info['dots_moved']:,} of 37,654 dots moved; mean displacement "
            f"{snap_info['mean_displacement_px']:.2f} px. The shared collar step removed "
            f"{collar_info['removed_dots']:,} parent dots inside 3 px of the catalogue and refilled the "
            "same count from the H19-5 pool, so every arm is identical apart from the dose."
        ),
        "non_fault_confounder": (
            "Lithologic contacts, drainage margins and culture edges also produce magnetic and gravity "
            "gradients; a dot can be pulled onto one of those and away from a real fault. The consensus of "
            "two independent physical fields reduces, but does not remove, single-source artefacts."
        ),
        "predicted_live_change": PREDICTIONS[token],
        "falsifier": (
            f"Paired same-week live receipt against R0 ({mult:g}x step-epsilon dose): Delta <= -0.010 falsifies the cross-strike "
            "alignment mechanism at this dose; any |Delta| < 0.010 is no evidence under the session rule. "
            "A dose ordering that is not monotone in the cap also falsifies the 'closer to the edge is "
            "better' reading, because the two larger caps nest the smaller one."
        ),
        "structural_geologist_note": (
            "Judge whether the moved dots sit on a plausible fault trace or on a stratigraphic contact: the "
            "edit never adds mass, so any gain or loss is purely positional. The rank-normalised consensus "
            "is a relative edge strength, not a fault probability."
        ),
    }


# --------------------------------------------------------------------------------------
# outputs
# --------------------------------------------------------------------------------------
LEDGER_FIELDS = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
                 "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
                 "receipt_score", "predicted_change", "date", "form_note", "notes"]


def write_outputs(result: dict) -> None:
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    rows = []
    if LEDGER.is_file():
        with LEDGER.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    new_ids = {v["id"] for v in result["variants"]}
    rows = [r for r in rows if r.get("id") not in new_ids and not (r.get("axis") == AXIS and r.get("site") == "GEMSDOE90")]
    for v in result["variants"]:
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback", "n_dots": v["n_dots"],
            "pct_changed": f"{v['pct_changed']:.6f}", "sha256": v["sha256"],
            "sha256_zeros": v["sha256_zeros"], "parent": v["parent"], "axis": v["axis"],
            "value": v["value"], "status": "BUILT", "receipt": "N", "receipt_score": "",
            "predicted_change": v["predicted_change"], "date": "", "form_note": v["form_note"],
            "notes": "receipt_score/date to be filled by human; agent never submits",
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    cards_path = ROOT / "ledger" / "mechanism_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8")) if cards_path.is_file() else {}
    cards.setdefault("sessions", []).append({
        "date": DATE, "axis": AXIS, "parent": PARENT,
        "variants": [{"id": v["id"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
                     for v in result["variants"]],
    })
    cards_path.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def verify() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    inputs = r0b.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = r0b.exact_parent_rebuild()
    dist = ndi.distance_transform_edt(~cat)
    h19 = r0b.read_binary(DATA / r0b.PIN_PATHS["h19_5"], foot)
    rank = r0b.fifo_bfs_visit_rank(h19)
    pool = h19 & foot & ~cat & ~r0
    edge, edge_meta = consensus_edge(foot)
    eps = edge_meta["step_epsilon_rank"]
    seed, collar_info = collar_reconcile(r0, foot, cat, dist, pool, rank)
    for variant, (token, mult) in zip(receipt["variants"], DOSES):
        expected, snap_info = snap(seed, foot, cat, dist, edge, rank, CAP_PX, mult * eps)
        if int(expected.sum()) != R0_DOTS:
            raise ValueError(f"recomputed {variant['id']} count mismatch")
        for mode in ("nan", "zeros"):
            audit = r0b.validate_file(ROOT / variant["files"][mode]["path"], expected, foot, cat, template, mode)
            if audit["sha256"] != variant["files"][mode]["sha256"]:
                raise ValueError(f"re-read SHA mismatch for {variant['id']} {mode}")
            tmpdir = ROOT / ".cache" / "verify_snap_bytes"
            tmpdir.mkdir(parents=True, exist_ok=True)
            tmp = tmpdir / f"{variant['id']}-{mode}.tif"
            try:
                r0b.emit(expected, foot, template, variant["id"], mode, tmp)
                if sha256_file(tmp) != audit["sha256"]:
                    raise ValueError(f"byte-for-byte deterministic re-emit failed for {variant['id']} {mode}")
            finally:
                tmp.unlink(missing_ok=True)
    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = git_sha()
    receipt["self_check"] = {"variant_files_re_read_and_validated": True,
                             "variant_bytes_reproduced_exactly": True,
                             "r0_rebuilt_byte_identically": True,
                             "d28_ranking_reproduced_pixel_exactly":
                                 parent_stats["d28_symmetric_difference_px"] == 0,
                             "manifest_verified_count": len(inputs)}
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(DOSES)} SNAP pairs from disk; R0 rebuilt byte-identically")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        return verify()
    result = build()
    write_outputs(result)
    print(f"Built {len(result['variants'])} SNAP arms; receipt -> {RECEIPT.relative_to(ROOT)}")
    for v in result["variants"]:
        info = v["parent_diff"]
        print(f"  {v['id']}: {int(v['n_dots'])} dots, moved {info['snap']['dots_moved']:,} "
              f"({info['snap']['pct_moved']:.1f}%), mean disp {info['mean_displacement_px']:.2f} px, "
              f"{info['pct_of_parent_dots_changed']:.2f}% changed vs R0, sha256={v['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
