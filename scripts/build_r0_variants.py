#!/usr/bin/env python3
"""Rebuild R0 byte-for-byte, then build controlled PRUNE collar/refill variants.

The only changed axis is PRUNE cutoff radius. Each fixed-count candidate removes all R0 dots
with Euclidean catalogue distance <= the named threshold, then refills from H19-5 in its
reconstructed FIFO-BFS priority order, with every final dot strictly farther than the threshold.
No public-test labels or score endpoints are used. Local TIFFs are written under ignored
`releases/`; do not add them to public Git or any GitHub release.

Run: `.venv/bin/python scripts/build_r0_variants.py --build`
Verify written files: `.venv/bin/python scripts/build_r0_variants.py --verify`
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "PRUNE"
DATE = "20261023"
R0_ZEROS_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
R0_NAN_SHA = "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd"
R0_DOTS = 37_654
THRESHOLDS = (3.5, 4.5, 5.5)
PIN_PATHS = {
    "sample_submission": "sample_submission.tif",
    "catalogue": "existing_faults.tif",
    "parent_h27": "scored/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
    "parent_r0_zeros": "parent/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "parent_r0_nan": "parent/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif",
    "h19_5": "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "d28": "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_sha() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def manifest_entries() -> dict[str, dict]:
    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    return {entry["id"]: entry for entry in manifest["files"]}


def verify_manifest_inputs() -> dict:
    """Recheck every one of the 26 pinned files, not just the build subset."""
    entries = manifest_entries()
    receipt_path = ROOT / "evidence" / "manifest_verification.json"
    if not receipt_path.is_file():
        raise RuntimeError("manifest verification receipt missing; run scripts/restore_data.py first")
    receipt = json.loads(receipt_path.read_text())
    receipt_by_id = {row["id"]: row for row in receipt["files"]}
    if len(receipt_by_id) != len(entries) or not receipt["all_sha256_matched"]:
        raise RuntimeError("manifest receipt is incomplete or not fully verified")
    checked = {}
    for ident, entry in entries.items():
        path = DATA / entry["dest"]
        if not path.is_file():
            raise FileNotFoundError(f"manifest input missing: {ident}: {path}")
        got = sha256_file(path)
        if got != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise ValueError(f"manifest input mismatch: {ident}: {got} != {entry['sha256']}")
        r = receipt_by_id.get(ident)
        if not r or r.get("sha256") != got or r.get("bytes") != path.stat().st_size:
            raise ValueError(f"restore receipt mismatch: {ident}")
        checked[ident] = {"path": entry["dest"], "sha256": got, "bytes": path.stat().st_size}
    return checked


def read_binary(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return footprint & np.isfinite(a) & (a > 0.5)


def fifo_bfs_visit_rank(mask: np.ndarray) -> np.ndarray:
    """Recover exact deterministic FIFO-BFS visit order of the original thinning recipe.

    Mirrors `dot_thin` at GEMSDOE28@d618b648: connected components are 8-neighbour; seeds are
    the first raster index in each component; neighbors enter a FIFO queue in row-major offset
    order. The ranking is traversal priority only, not a geological probability.
    """
    mask = np.asarray(mask, dtype=bool)
    height, width = mask.shape
    pad = 4
    wp, hp = width + 2 * pad, height + 2 * pad
    padded = np.zeros((hp, wp), dtype=bool)
    padded[pad:pad + height, pad:pad + width] = mask
    flat = bytearray(padded.tobytes())
    visited = bytearray(hp * wp)
    offsets = (-wp - 1, -wp, -wp + 1, -1, 1, wp - 1, wp, wp + 1)
    components, _ = ndi.label(padded, structure=np.ones((3, 3), dtype=np.uint8))
    component_flat = components.ravel()
    order = np.flatnonzero(component_flat)
    _, first = np.unique(component_flat[order], return_index=True)
    ranks = np.full(hp * wp, -1, dtype=np.int32)
    visit = 0
    for seed in order[np.sort(first)].tolist():
        if visited[seed]:
            continue
        visited[seed] = 1
        queue = deque((seed,))
        while queue:
            current = queue.popleft()
            ranks[current] = visit
            visit += 1
            for off in offsets:
                neighbour = current + off
                if flat[neighbour] and not visited[neighbour]:
                    visited[neighbour] = 1
                    queue.append(neighbour)
    return ranks.reshape(hp, wp)[pad:pad + height, pad:pad + width]


def original_dot_thin(mask: np.ndarray, rank: np.ndarray, min_dist: float = 2.8) -> np.ndarray:
    """Greedy thinning with the same radius and deterministic rank used in d2.8."""
    height, width = mask.shape
    pad = int(np.ceil(min_dist)) + 1
    wp, hp = width + 2 * pad, height + 2 * pad
    padded = np.zeros((hp, wp), dtype=bool)
    padded[pad:pad + height, pad:pad + width] = mask
    blocked = bytearray(hp * wp)
    kept = bytearray(hp * wp)
    offsets = [dy * wp + dx
               for dy in range(-int(np.ceil(min_dist)), int(np.ceil(min_dist)) + 1)
               for dx in range(-int(np.ceil(min_dist)), int(np.ceil(min_dist)) + 1)
               if dy * dy + dx * dx < min_dist * min_dist]
    ys, xs = np.nonzero(mask)
    visit_order = np.argsort(rank[ys, xs], kind="stable")
    for pos in visit_order:
        py, px = int(ys[pos] + pad), int(xs[pos] + pad)
        cur = py * wp + px
        if not blocked[cur]:
            kept[cur] = 1
            for off in offsets:
                blocked[cur + off] = 1
    out = np.frombuffer(bytes(kept), dtype=np.uint8).reshape(hp, wp).astype(bool)
    return out[pad:pad + height, pad:pad + width]


def exact_parent_rebuild() -> tuple[dict, np.ndarray, np.ndarray, np.ndarray, dict]:
    paths = {key: DATA / rel for key, rel in PIN_PATHS.items()}
    for key, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"required R0 input absent: {key}: {path}")
        if key in manifest_entries():
            continue
        # Reusable parent artifacts are explicit manifest entries with unique IDs; check by dest.
        matched = next((e for e in manifest_entries().values() if e["dest"] == PIN_PATHS[key]), None)
        if matched is None or sha256_file(path) != matched["sha256"]:
            raise ValueError(f"unmanifested or hash-mismatched parent input: {key}")
    with rasterio.open(paths["sample_submission"]) as src:
        template = src.profile.copy()
        sample = src.read(1)
    footprint = np.isfinite(sample)
    with rasterio.open(paths["catalogue"]) as src:
        catalogue = (src.read(1) > 0) & footprint
    distance = ndi.distance_transform_edt(~catalogue)
    h27 = read_binary(paths["parent_h27"], footprint)
    r0 = h27 & (distance > 2.0)
    parent_zeros = read_binary(paths["parent_r0_zeros"], footprint)
    parent_nan = read_binary(paths["parent_r0_nan"], footprint)
    if not np.array_equal(r0, parent_zeros) or not np.array_equal(r0, parent_nan):
        raise ValueError("R0 mask reconstructed from h27-4 is not pixel-identical to pinned R0")
    if int(r0.sum()) != R0_DOTS or np.any(r0 & catalogue):
        raise ValueError("R0 count/catalogue integrity check failed")

    # Re-emit the reconstructed parent under the sample template and require both pinned byte hashes.
    rebuild_dir = ROOT / ".cache" / "r0_rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    r0_zeros_path = rebuild_dir / "r0-rebuilt-zeros.tif"
    r0_nan_path = rebuild_dir / "r0-rebuilt-nan.tif"
    emit(r0, footprint, template, "r0-rebuilt", "zeros", r0_zeros_path)
    emit(r0, footprint, template, "r0-rebuilt", "nan", r0_nan_path)
    rebuilt_zeros_sha = sha256_file(r0_zeros_path)
    rebuilt_nan_sha = sha256_file(r0_nan_path)
    if rebuilt_zeros_sha != R0_ZEROS_SHA or rebuilt_nan_sha != R0_NAN_SHA:
        raise ValueError(
            "R0 byte rebuild failed: "
            f"zeros={rebuilt_zeros_sha} (expected {R0_ZEROS_SHA}); "
            f"nan={rebuilt_nan_sha} (expected {R0_NAN_SHA})"
        )

    # Independently recover the original d2.8 ranking from the pinned H19-5 binary source and
    # ensure the recorded thinning recipe reproduces the pinned 44,090-dot mask exactly.
    h19 = read_binary(paths["h19_5"], footprint)
    d28 = read_binary(paths["d28"], footprint)
    rank = fifo_bfs_visit_rank(h19)
    d28_rebuilt = original_dot_thin(h19, rank, 2.8)
    if not np.array_equal(d28_rebuilt, d28):
        raise ValueError(f"H19-5 FIFO-BFS 2.8 thinning does not reproduce pinned d2.8 ({int((d28_rebuilt ^ d28).sum())} cells differ)")
    # H27-4 is an upstream documented solo-dejitter parent. We pin it exactly, while R0 itself is
    # reconstructed from that parent using the archived `distance_transform_edt(~cat) > 2 px` rule.
    return template, footprint, catalogue, r0, {
        "r0_rebuilt_from": "pinned h27-4 solo-d2.8 mask & (Euclidean d_cat > 2 px)",
        "r0_dots": int(r0.sum()),
        "r0_min_d_cat_px": float(distance[r0].min()),
        "r0_below_3px": int((r0 & (distance < 3.0)).sum()),
        "r0_zeros_parent_sha256": sha256_file(paths["parent_r0_zeros"]),
        "r0_nan_parent_sha256": sha256_file(paths["parent_r0_nan"]),
        "r0_rebuilt_zeros_sha256": rebuilt_zeros_sha,
        "r0_rebuilt_nan_sha256": rebuilt_nan_sha,
        "r0_byte_identity_passed": True,
        "d28_rebuilt_from_h19_5": True,
        "d28_dots": int(d28_rebuilt.sum()),
        "d28_symmetric_difference_px": int((d28_rebuilt ^ d28).sum()),
        "ranking": "H19-5 8-connected FIFO-BFS visitation order (GEMSDOE28/src/gems27/thinning.py)",
        "ranking_git_source": "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/d618b648f3ff3b30d04f376dcd6610c3cf28cf28/src/gems27/thinning.py",
    }


def emit(mask: np.ndarray, foot: np.ndarray, template: dict, slug: str, mode: str, temp_path: Path) -> Path:
    profile = template.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3,
                   zlevel=9, tiled=True, blockxsize=256, blockysize=256,
                   nodata=np.nan if mode == "nan" else None)
    a = np.where(foot, mask.astype(np.float32), np.nan if mode == "nan" else 0.0).astype(np.float32)
    with rasterio.open(temp_path, "w", **profile) as dst:
        dst.write(a, 1)
    return temp_path


def validate_file(path: Path, expected: np.ndarray, foot: np.ndarray, cat: np.ndarray,
                  sample_profile: dict, mode: str) -> dict:
    with rasterio.open(path) as src:
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
        "min_catalogue_distance_ge_3px": float(ndi.distance_transform_edt(~cat)[(a > 0.5) & foot].min()) >= 3.0,
        "file_re_read_from_disk": True,
    }
    if not all(checks.values()):
        raise ValueError(f"validator failed for {path.name}: {[k for k,v in checks.items() if not v]}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(((a > 0.5) & foot).sum()),
        "min_catalogue_distance_px": float(ndi.distance_transform_edt(~cat)[(a > 0.5) & foot].min()),
        "checks": checks,
    }


def check_pair_reservations() -> None:
    reservations = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text())
    occupied = []
    for source in reservations["sources"]:
        occupied.extend(float(x) for x in source["values_px"])
    ledger_path = ROOT / "ledger" / "submissions.csv"
    if ledger_path.exists():
        with ledger_path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                match = re.search(r"d_cat<=([0-9]+(?:\.[0-9]+)?)px", row.get("value", ""))
                if match:
                    occupied.append(float(match.group(1)))
    for cutoff in THRESHOLDS:
        if any(abs(cutoff - value) < 1e-6 for value in occupied):
            raise ValueError(f"duplicate experiment reservation: (PRUNE, {cutoff:g}px) already exists")


def build() -> dict:
    t0 = time.time()
    check_pair_reservations()
    input_receipt = verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~cat)
    h19 = read_binary(DATA / PIN_PATHS["h19_5"], foot)
    rank = fifo_bfs_visit_rank(h19)
    if np.any(rank[h19] < 0) or np.any(rank[~h19] != -1):
        raise RuntimeError("FIFO-BFS ranking failed to cover exactly the H19-5 support")

    OUT.mkdir(parents=True, exist_ok=True)
    variants = []
    for cutoff in THRESHOLDS:
        kept = r0 & (distance > cutoff)
        removed = r0 & ~kept
        n_refill = int(removed.sum())
        eligible = h19 & foot & ~cat & (distance > cutoff) & ~kept
        ey, ex = np.nonzero(eligible)
        if len(ey) < n_refill:
            raise ValueError(f"PRUNE {cutoff:g}px has only {len(ey)} eligible H19-5 refill pixels for {n_refill} removed dots")
        order = np.argsort(rank[ey, ex], kind="stable")[:n_refill]
        candidate = kept.copy()
        candidate[ey[order], ex[order]] = True
        if candidate.sum() != R0_DOTS:
            raise AssertionError("fixed-count refill did not hold 37,654 dots")
        if np.any(candidate & (distance <= cutoff)) or np.any(candidate & cat) or np.any(candidate & ~foot):
            raise AssertionError("PRUNE candidate violates its own collar/catalogue/footprint rule")
        changed = int(np.count_nonzero(candidate ^ r0))
        pct_changed = 100.0 * changed / R0_DOTS
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"PRUNE {cutoff:g}px changes {pct_changed:.6f}% of R0 (required 1–50%)")
        value = f"d_cat<={cutoff:g}px; fixed-count FIFO-BFS H19-5 refill; min d_cat>{cutoff:g}px"
        slug = f"{PARENT}-PRUNE{cutoff:g}px-{DATE}"
        temp_nan = OUT / f".{slug}-nan.tmp.tif"
        temp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        emit(candidate, foot, template, slug, "nan", temp_nan)
        emit(candidate, foot, template, slug, "zeros", temp_zeros)
        nan_sha = sha256_file(temp_nan)
        zeros_sha = sha256_file(temp_zeros)
        sha8 = nan_sha[:8]
        base = OUT / f"{PARENT}-PRUNE{str(cutoff).replace('.', 'p')}px-{DATE}-{sha8}"
        nan_path = base.with_suffix(".tif")
        zeros_path = OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = validate_file(nan_path, candidate, foot, cat, template, "nan")
        zeros_audit = validate_file(zeros_path, candidate, foot, cat, template, "zeros")
        delta = {"removed_from_parent": int(removed.sum()), "added_refill": int((candidate & ~r0).sum()),
                 "retained_parent": int((candidate & r0).sum()), "symmetric_difference_px": changed,
                 "pct_changed_of_R0": pct_changed}
        # No local hide-and-recover proxy is used as a gate or score. The parent recipe does not
        # contain an untouched test split that can validly rank the variants.
        prediction = {
            3.5: ("+0.002 DTI (MODEL; plausible interval -0.010 to +0.010; not a score)", "+0.002"),
            4.5: ("+0.000 DTI (MODEL; plausible interval -0.010 to +0.010; not a score)", "+0.000"),
            5.5: ("-0.003 DTI (MODEL; plausible interval -0.010 to +0.010; not a score)", "-0.003"),
        }[cutoff]
        cards = {
            "hypothesis": (
                f"At d_cat<={cutoff:g} px, R0's near-catalogue flank dots contain more false-positive mass than "
                "new-fault credit; replacing that collar with the same lineage's next-ranked ridge pixels "
                "should improve DTI without changing the emitted mass."
            ),
            "mechanism": (
                "Known catalogue pixels are masked pixel-exactly, while a nearby new fault remains scoreable; "
                "the PRUNE edit tests whether the empirical 2.0 px collar is too narrow. It drops every parent "
                "dot inside the specified radius and replaces the exact count from the H19-5 support, using its "
                "recovered FIFO-BFS thinning order, only where d_cat is strictly outside the new collar."
            ),
            "non_fault_confounder": (
                "H19-5's next-priority pixels may be ridges from lithologic contacts, drainage margins, or "
                "topographic lineaments rather than faults; new-fault truth may also cluster beside known traces."
            ),
            "predicted_live_change": prediction[0],
            "falsifier": (
                "A paired, same-week live receipt against R0 with Δ<=-0.010 falsifies the proposed positive "
                "collar effect for this cutoff/refill policy. Any |Δ|<0.010 is no evidence under the session rule."
            ),
            "structural_geologist_note": (
                "Interpret this as a positional-uncertainty/collar experiment, not as a claim that faults do not "
                "continue near mapped traces. Review both removed flanks and FIFO-ranked refill ridges on geology."
            ),
        }
        note = f"{PARENT}; PRUNE dcat<={cutoff:g}px, fixed-count refill; predicted {prediction[1]} DTI MODEL"
        if len(note) > 140:
            raise AssertionError(f"submission note is {len(note)} characters")
        variants.append({
            "id": base.name,
            "parent": PARENT,
            "axis": AXIS,
            "value": value,
            "n_dots": R0_DOTS,
            "pct_changed": pct_changed,
            "removed_dots": int(removed.sum()),
            "added_dots": int((candidate & ~r0).sum()),
            "retained_dots": int((candidate & r0).sum()),
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "predicted_change": cards["predicted_live_change"],
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": delta,
            "mechanism_card": cards,
            "threshold_px": cutoff,
        })

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha(),
        "axis": AXIS,
        "parent": {"id": PARENT, "claimed_live_score": 0.2778, "evidence_class": "CLAIM",
                   "zeros_sha256": R0_ZEROS_SHA, "nan_sha256": R0_NAN_SHA, **parent_stats},
        "manifest": {"manifest_path": "registry/data_manifest.json", "verified_count": len(input_receipt),
                     "all_pins_rechecked": True, "files": input_receipt},
        "ranking": {"recipe": "8-connected FIFO-BFS visit order over binary H19-5 support; exact d2.8 output reproduced",
                    "is_geological_probability": False,
                    "d28_reproduction_symmetric_difference_px": 0},
        "proxy_reports": {
            "catalogue_hide_recover": {"status": "NOT RUN", "reason": "No fold-clean, untouched truth instrument validated for this controlled refill; proxy is never a gate or score."},
            "leakage_canary": {"status": "REPORT ONLY", "sample": "all 60,988 known catalogue positives plus 250,000 seeded off-catalogue footprint pixels; median-fill finite values after sentinel masking", "seed": 20261023, "max_symmetric_auc": 0.5700, "max_feature": "geod_2ndinv", "auc_gt_0_90": False},
            "sgmc_control": {"status": "NOT RUN", "reason": "No fold-clean SGMC control is validated as calibrated for this collar/refill; not a gate."},
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
    }
    return result


def write_ledgers(result: dict) -> None:
    # The raw paste is the historical owner report; repeated site/name/score rows are collapsed.
    raw_rows = list(csv.DictReader((ROOT / "ledger" / "raw_paste.txt").open(newline="", encoding="utf-8")))
    deduped = {}
    for row in raw_rows:
        key = (row["site_repo"].strip(), row["submission_name"].strip(), row["public_score"].strip())
        deduped.setdefault(key, row)
    fields = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
              "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
              "receipt_score", "predicted_change", "date", "form_note", "notes"]
    rows = []
    for (site, name, score), _row in deduped.items():
        rows.append({"id": name, "site": site, "name": name, "score": score,
                     "evidence_class": "CLAIM", "status": "HISTORICAL_CLAIM", "receipt": "N",
                     "notes": "owner-reported from ledger/raw_paste.txt; not a receipt; duplicates collapsed by site/name/score"})
    for v in result["variants"]:
        rows.append({"id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
                     "evidence_class": "MODEL (predicted change only)", "encoding": "nan primary; zeros fallback",
                     "n_dots": v["n_dots"], "pct_changed": f"{v['pct_changed']:.6f}",
                     "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"], "parent": v["parent"],
                     "axis": v["axis"], "value": v["value"], "status": "BUILT", "receipt": "N",
                     "receipt_score": "", "predicted_change": v["predicted_change"], "date": "",
                     "form_note": v["form_note"], "notes": "receipt_score/date to be filled by human; agent never submits"})
    with (ROOT / "ledger" / "submissions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    cards = {
        "schema_version": 1,
        "parent": PARENT,
        "axis": AXIS,
        "variants": [{"id": v["id"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
                     for v in result["variants"]],
    }
    (ROOT / "ledger" / "mechanism_cards.json").write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.build:
        result = build()
        evidence = ROOT / "evidence" / "build_receipt.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        write_ledgers(result)
        print(f"Built {len(result['variants'])} variants from exact R0; evidence -> {evidence.relative_to(ROOT)}")
        for v in result["variants"]:
            print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.3f}% changed, sha256={v['sha256']}")
        return 0
    input_receipt = verify_manifest_inputs()
    receipt = json.loads((ROOT / "evidence" / "build_receipt.json").read_text())
    template, foot, cat, r0, parent_stats = exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~cat)
    h19 = read_binary(DATA / PIN_PATHS["h19_5"], foot)
    rank = fifo_bfs_visit_rank(h19)
    for v in receipt["variants"]:
        cutoff = float(v["threshold_px"])
        expected = r0 & (distance > cutoff)
        removed = r0 & ~expected
        eligible = h19 & foot & ~cat & (distance > cutoff) & ~expected
        ey, ex = np.nonzero(eligible)
        n_refill = int(removed.sum())
        order = np.argsort(rank[ey, ex], kind="stable")[:n_refill]
        expected[ey[order], ex[order]] = True
        if int(expected.sum()) != R0_DOTS:
            raise ValueError(f"recomputed {v['id']} count mismatch")
        for mode_name in ("nan", "zeros"):
            audit = validate_file(ROOT / v["files"][mode_name]["path"], expected, foot, cat, template, mode_name)
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"re-read SHA mismatch for {v['id']} {mode_name}")
            temp_dir = ROOT / ".cache" / "verify_candidate_bytes"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / f"{v['id']}-{mode_name}.tif"
            try:
                emit(expected, foot, template, v["id"], mode_name, temp_path)
                if sha256_file(temp_path) != audit["sha256"]:
                    raise ValueError(f"byte-for-byte deterministic re-emit failed for {v['id']} {mode_name}")
            finally:
                temp_path.unlink(missing_ok=True)
    verified_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["parent"].update(parent_stats)
    receipt["manifest"] = {"manifest_path": "registry/data_manifest.json", "verified_count": len(input_receipt),
                           "all_pins_rechecked": True, "files": input_receipt}
    receipt["verified_utc"] = verified_utc
    receipt["git_sha"] = git_sha()
    receipt["verification_git_sha"] = git_sha()
    receipt["generator_script_sha256"] = sha256_file(ROOT / "scripts" / "build_r0_variants.py")
    receipt["self_check"] = {"variant_files_re_read_and_validated": True,
                             "variant_bytes_reproduced_exactly": True,
                             "r0_rebuilt_byte_identically": True,
                             "d28_ranking_reproduced_pixel_exactly": True}
    (ROOT / "evidence" / "build_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    r0_receipt = {
        "generated_utc": verified_utc,
        "git_sha": git_sha(),
        "generator_script_sha256": sha256_file(ROOT / "scripts" / "build_r0_variants.py"),
        "parent": PARENT,
        "method": "reconstruct h33-h33-2-b2 as pinned h27-4 solo-d2.8 & (Euclidean distance to catalogue > 2 px), then re-emit with sample_submission.tif profile",
        "rebuilt": {"zeros_sha256": parent_stats["r0_rebuilt_zeros_sha256"],
                    "nan_sha256": parent_stats["r0_rebuilt_nan_sha256"],
                    "dots": parent_stats["r0_dots"],
                    "below_3px": parent_stats["r0_below_3px"]},
        "expected": {"zeros_sha256": R0_ZEROS_SHA, "nan_sha256": R0_NAN_SHA, "dots": R0_DOTS},
        "all_checks_passed": bool(parent_stats["r0_byte_identity_passed"] and parent_stats["d28_symmetric_difference_px"] == 0),
        "manifest_verified_count": len(input_receipt),
        "no_competition_inputs_added_to_git": True,
    }
    r0_path = ROOT / "evidence" / "r0_rebuild_receipt.json"
    r0_path.write_text(json.dumps(r0_receipt, indent=2) + "\n")
    print(f"Verified {len(receipt['variants'])} variant pairs from disk; R0 rebuilt byte-identically to {R0_ZEROS_SHA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
