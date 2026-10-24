#!/usr/bin/env python3
"""Build the AXIS=MASS add-direction ladder from R0 by coverage infill.

Parent: h33-h33-2-b2 (37,654 unit-mass dots, rebuilt byte-identically).
Change: add 5 / 10 / 20 % new unit-mass dots (1,883 / 3,765 / 7,531) in the
kernel mid-strand gaps of the H19-5 corroborated-ridge support. Nothing is
deleted, nothing is moved, no dot value changes.

Why the add direction (see src/reach.py and docs/MECHANISM_CARDS.md):
R0's thinning recipe enforces a 2.8 px minimum dot spacing while the kernel is
3 px wide, so the pixel midway between two consecutive dots on a strand can only
ever reach ~0.53 of the kernel credit the metric pays for. Infill at that
midpoint raises it to 1.0. The deletion ceiling (0.2/D per dot) and the
addition ceiling (1/D per dot) differ by 5x, and the whole recorded climb of this
lineage is deletion-side.

Evenness (Hard Constraint #5): additions are apportioned over 5 km blocks in
proportion to the block's R0 dot count (largest-remainder, water-filled), so no
region is enriched or emptied. The parent's FIFO-BFS traversal order is NOT used
(IR90-20 measured it to be geographic). The catalogue is used only as a
>= 3 px exclusion, never as a ranking signal.

Run build:  .venv/bin/python scripts/build_mass_infill.py --build
Run verify: .venv/bin/python scripts/build_mass_infill.py --verify
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import build_r0_variants as b  # noqa: E402  (audited exact-rebuild + emit path)
from src import reach  # noqa: E402

PARENT = "h33-h33-2-b2"
AXIS = "MASS"
DATE = "20261023"
R0_DOTS = 37_654
BLOCK_PX = 50  # 5 km at 100 m
DOSE_PCT = (5, 10, 20)
CLAIMED_DTI = 0.2778  # CLAIM, never a receipt
RECEIPT = ROOT / "evidence" / "mass_infill_receipt.json"
OUT = ROOT / "releases"

# Adopted MODEL predictions. The first-order model in src/reach.py is run for
# every dose, but its raw output assumes the truth set is an unbiased sample of
# the H19-5 support. It is not: R0's own thinning and collar concentrated the
# best-covered support exactly where the lineage was most confident, so the
# residual credit deficit sits in the least-confident part of the support. The
# adopted numbers apply a documented transfer discount (see docs/MECHANISM_CARDS.md)
# and are quoted with a sign-relevant bracket, never as a score.
PREDICTION = {
    5: ("+0.008 DTI (MODEL; plausible -0.004 to +0.030; not a score)", "+0.008"),
    10: ("+0.014 DTI (MODEL; plausible -0.008 to +0.045; not a score)", "+0.014"),
    20: ("+0.022 DTI (MODEL; plausible -0.015 to +0.070; not a score)", "+0.022"),
}
TRANSFER_DISCOUNT = 0.10  # adopted/raw ratio at the 5 % dose; see card


def pool_and_credit(foot: np.ndarray, cat: np.ndarray, h19: np.ndarray, r0: np.ndarray, dcat: np.ndarray):
    pool = h19 & foot & ~cat & (dcat >= 3.0) & ~r0
    credit = reach.credit_map(r0)
    return pool, credit


def validate_candidate(path: Path, expected: np.ndarray, foot: np.ndarray, cat: np.ndarray,
                       sample_profile: dict, mode: str, r0: np.ndarray, dcat: np.ndarray,
                       pool: np.ndarray) -> dict:
    """Format MUST-pass gate plus this axis's two design invariants."""
    with rasterio.open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs, transform = src.crs, src.transform
    dots = (a > 0.5) & foot
    added = dots & ~r0
    checks = {
        "crs_matches_sample": crs == sample_profile["crs"],
        "transform_matches_sample": transform == sample_profile["transform"],
        "shape_matches_sample": a.shape == (sample_profile["height"], sample_profile["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(a[foot]).all()),
        "inside_foot_range_0_1": bool(np.all((a[foot] >= 0) & (a[foot] <= 1))),
        "outside_is_nan": bool(np.isnan(a[~foot]).all()) if mode == "nan" else bool(np.all(a[~foot] == 0)),
        "exact_expected_mask_after_disk_read": bool(np.array_equal(dots, expected)),
        "zero_catalogue_mass": not bool(np.any(dots & cat)),
        "parent_subset_retained": bool(np.all(dots[r0])),
        "no_new_mass_within_3px": not bool(np.any(added & (dcat < 3.0))),
        "additions_only_in_eligible_pool": not bool(np.any(added & ~pool)),
        "file_re_read_from_disk": True,
    }
    if not all(checks.values()):
        raise ValueError(f"gate failed for {path.name}: {[k for k, v in checks.items() if not v]}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": b.sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(dots.sum()),
        "n_added": int(added.sum()),
        "min_catalogue_distance_px": float(dcat[dots].min()),
        "checks": checks,
    }


def structural_diagnostics(r0: np.ndarray, sel: np.ndarray, res: dict, dcat: np.ndarray) -> dict:
    """Region evenness, spacing and continuity numbers quoted in the receipt."""
    bid, block_ids, grid = reach.block_index(r0.shape, BLOCK_PX)
    before = np.bincount(bid[r0], minlength=len(block_ids))
    after = np.bincount(bid[r0 | sel], minlength=len(block_ids))
    add_counts = res["block_counts_add"].reshape(grid)
    occupied = before > 0
    add_share_by_block = np.divide(add_counts.ravel(), np.maximum(before, 1),
                                   where=occupied, out=np.zeros_like(add_counts, dtype=float).ravel())
    add_share_by_block = np.asarray(add_share_by_block, dtype=float)[occupied]
    d_parent = ndi.distance_transform_edt(~r0)
    return {
        "block_px": BLOCK_PX,
        "block_density_cv_before": round(reach.density_cv(before), 4),
        "block_density_cv_after": round(reach.density_cv(after), 4),
        "occupied_blocks_before": int(occupied.sum()),
        "occupied_blocks_after": int((after > 0).sum()),
        "blocks_with_additions": int((add_counts > 0).sum()),
        "max_additions_in_one_block": int(add_counts.max()),
        "p05_add_share_of_block_mass": round(float(np.percentile(add_share_by_block, 5)), 5),
        "p50_add_share_of_block_mass": round(float(np.percentile(add_share_by_block, 50)), 5),
        "largest_contiguous_block_run_with_additions": reach.largest_contiguous(add_counts > 0),
        "additions_within_2px_of_parent_dot": int((sel & (d_parent <= 2.0)).sum()),
        "additions_fraction_in_zero_credit_gap": round(
            float((sel & (reach.credit_map(r0) == 0)).sum()) / max(1, int(sel.sum())), 4),
        "mean_parent_distance_px": round(float(d_parent[sel].mean()), 3),
        "parent_dots_deleted": 0,
        "note_continuity": ("every parent dot is retained, so no parent strand can be lost; "
                            "infill can only merge strands"),
    }


def build() -> dict:
    t0 = time.time()
    input_receipt = b.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = b.exact_parent_rebuild()
    dcat = ndi.distance_transform_edt(~cat)
    h19 = b.read_binary(b.DATA / b.PIN_PATHS["h19_5"], foot)
    pool, _ = pool_and_credit(foot, cat, h19, r0, dcat)
    footprint_px = int(foot.sum())
    support_px = int((h19 & foot).sum())

    OUT.mkdir(parents=True, exist_ok=True)
    variants = []
    for pct in DOSE_PCT:
        n_add = int(round(pct / 100.0 * R0_DOTS))
        res = reach.infill_select(pool, r0, n_total=n_add, block_px=BLOCK_PX)
        sel = res["selected"]
        candidate = r0 | sel
        changed = int(np.count_nonzero(candidate ^ r0))
        pct_changed = 100.0 * changed / R0_DOTS
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"dose {pct}% changes {pct_changed:.4f}% of R0 (required 1-50%)")
        if np.any(candidate & cat) or np.any(candidate & ~foot) or not np.all(candidate[r0]):
            raise AssertionError(f"dose {pct}% breaks catalogue/footprint/parent-retention invariants")
        if np.any(sel & ~pool):
            raise AssertionError(f"dose {pct}% added outside the eligible pool")

        gain_sum = float(res["gains"].sum())
        model = {}
        for truth_px in (20_000, 55_000, 100_000):
            model[str(truth_px)] = round(reach.truth_free_add_delta(
                gain_sum=gain_sum, n_add=n_add, n_parent=R0_DOTS, dti=CLAIMED_DTI,
                support_px=support_px, truth_px=truth_px), 4)

        slug = f"{PARENT}-MASSadd{pct}pctq{BLOCK_PX}-{DATE}"
        temp_nan = OUT / f".{slug}-nan.tmp.tif"
        temp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        b.emit(candidate, foot, template, slug, "nan", temp_nan)
        b.emit(candidate, foot, template, slug, "zeros", temp_zeros)
        sha8 = b.sha256_file(temp_nan)[:8]
        base = OUT / f"{slug}-{sha8}"
        nan_path, zeros_path = base.with_suffix(".tif"), OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = validate_candidate(nan_path, candidate, foot, cat, template, "nan", r0, dcat, pool)
        zeros_audit = validate_candidate(zeros_path, candidate, foot, cat, template, "zeros", r0, dcat, pool)

        diag = structural_diagnostics(r0, sel, res, dcat)
        variants.append({
            "id": base.name,
            "value": f"add{pct}pctq{BLOCK_PX}",
            "axis": AXIS,
            "parent": PARENT,
            "n_added": n_add,
            "n_dots": int(candidate.sum()),
            "pct_changed": round(pct_changed, 6),
            "gain_sum_proxy": round(gain_sum, 3),
            "model_delta_by_truth_px": model,
            "predicted_change": PREDICTION[pct][0],
            "pred_short": PREDICTION[pct][1],
            "diagnostics": diag,
            "files": {"nan": {k: nan_audit[k] for k in ("path", "sha256", "bytes", "encoding", "n_dots", "n_added", "checks")},
                      "zeros": {k: zeros_audit[k] for k in ("path", "sha256", "bytes", "encoding", "n_dots", "n_added", "checks")}},
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "form_note": (f"{PARENT}; MASS add {n_add}d ({pct}%) kernel-mid-strand infill, "
                          f"{BLOCK_PX}px-block even quotas, d_cat>=3px; pred {PREDICTION[pct][1]} DTI MODEL")[:140],
        })
        print(f"  {base.name}: {candidate.sum()} dots (+{n_add}), {pct_changed:.2f}% changed, "
              f"sha256={nan_audit['sha256']}")

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": b.git_sha(),
        "generator_script_sha256": b.sha256_file(Path(__file__)),
        "session_branch": "arena/c3061751-gemsdoe90",
        "parent": PARENT,
        "axis": AXIS,
        "direction": "add (coverage infill); the entity's first add-direction receipt probe",
        "ranking": ("metric marginal kernel credit on the H19-5 corroborated-ridge support "
                    "(truth proxy), exact after every selection; per-5 km-block quota proportional "
                    "to the block's R0 dot count (largest remainder + water fill)"),
        "ranking_is_not": "the parent FIFO-BFS traversal order (IR90-20) and not the catalogue",
        "block_px": BLOCK_PX,
        "claimed_parent_dti_used_only_for_prediction": CLAIMED_DTI,
        "claimed_parent_dti_evidence_class": "CLAIM (owner-reported, no receipt on file)",
        "pool_cells": int(pool.sum()),
        "support_px": support_px,
        "footprint_px": footprint_px,
        "prediction_discount": {
            "factor": TRANSFER_DISCOUNT,
            "why": ("raw first-order model assumes the truth set is an unbiased sample of the H19-5 support; "
                    "the lineage's own thinning concentrated coverage where it was most confident, so the "
                    "residual credit deficit sits in its least-confident part"),
        },
        "parent_stats": parent_stats,
        "manifest": {"manifest_path": "registry/data_manifest.json", "verified_count": len(input_receipt),
                     "all_pins_rechecked": True},
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 1),
    }
    return result


def write_ledger(result: dict) -> None:
    path = ROOT / "ledger" / "submissions.csv"
    fields = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
              "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
              "receipt_score", "predicted_change", "date", "form_note", "notes"]
    new_ids = {v["id"] for v in result["variants"]}
    existing = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            existing = [r for r in csv.DictReader(f) if r.get("id") not in new_ids]
    for v in result["variants"]:
        existing.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": v["n_dots"], "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"],
            "parent": v["parent"], "axis": v["axis"], "value": v["value"],
            "status": "BUILT", "receipt": "N", "receipt_score": "",
            "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": ("superset of rebuilt R0: no deletions, no moves, unit mass only; "
                      "additions on H19-5 support, d_cat>=3px, 5km-block quotas proportional to R0 dots; "
                      "receipt_score/date to be filled by human"),
        })
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(existing)


def write_cards(result: dict) -> None:
    cards = {"schema_version": 1, "session": result["session_branch"], "parent": PARENT,
             "axis": AXIS, "variants": []}
    for v in result["variants"]:
        n = v["n_added"]
        pct = round(100 * n / R0_DOTS)
        cards["variants"].append({
            "id": v["id"], "value": v["value"],
            "mechanism_card": {
                "hypothesis": (
                    f"R0 leaves a 300 m-kernel coverage deficit along its own strands, so adding {n} unit dots "
                    f"({pct}% of the parent count) at the mid-strand gaps of the H19-5 support raises kernel "
                    "credit T under the metric's max-over-dots rule more than it raises the mass penalty, and "
                    "live DTI rises."
                ),
                "mechanism": (
                    "DTI = T/(0.2T + 0.2(S-M) + 0.8|G|) with T = sum over truth pixels of the best dot's "
                    "credit. R0's thinning recipe enforces a 2.8 px minimum spacing while the kernel is 3 px, "
                    "so any strand pixel midway between two consecutive dots can only reach ~0.53 credit; a "
                    "dot placed there lifts it to 1.0. The price of an addition is only 0.2/D (its mass share) "
                    "whenever it supplies no credit, i.e. five times smaller than the 1/D a landed dot earns, "
                    "so the add direction is the higher-ceiling half of MASS. Dots are chosen by exact "
                    "marginal credit against the H19-5 support proxy and apportioned over 5 km blocks in "
                    "proportion to the parent's own dot counts."
                ),
                "non_fault_confounder": (
                    "The H19-5 support is not truth: it also carries drainage lines, lithologic contacts and "
                    "pluvial shoreline segments. More insidiously, the residual credit deficit is concentrated "
                    "where the lineage's own thinning and catalogue collar removed dots, i.e. where it was "
                    "least confident - so the additions preferentially densify the support's weakest parts. "
                    "Dense mid-strand infill can also manufacture false along-strike continuity."
                ),
                "predicted_live_change": v["predicted_change"],
                "model_bracket": (
                    "raw first-order model: "
                    + ", ".join(f"|G|={g} px -> {d:+.4f}" for g, d in v["model_delta_by_truth_px"].items())
                    + " DTI; adopted prediction applies a 0.10 transfer discount (see receipt)"
                ),
                "falsifier": (
                    "Paired same-week receipt vs R0. Delta <= -0.010 falsifies the coverage-deficit mechanism "
                    "and closes the add direction (mass then behaves as pure penalty, matching the deployed "
                    "drop ladder's positive model predictions). Delta >= +0.010 opens deeper infill and, "
                    "crucially, licenses adding mass in the same week as a thinned file. |Delta| < 0.010 is "
                    "no evidence."
                ),
                "structural_geologist_note": (
                    f"Read this as a resampling-density test on your own traces, not as new fault evidence: "
                    f"the {n} added dots are all within ~3 px (300 m) of a dot R0 already had, and "
                    f"{v['diagnostics']['additions_within_2px_of_parent_dot']} of them are within 2 px. If the "
                    "score rises, the truth is line-like and under-sampled rather than diffuse; if it does not, "
                    "the parent's spacing is already adequate and the remaining error is positional, not "
                    "densification."
                ),
            },
            "diagnostics": v["diagnostics"],
        })
    (ROOT / "ledger" / "mechanism_cards_mass_infill.json").write_text(json.dumps(cards, indent=2) + "\n",
                                                                     encoding="utf-8")


def check_reservations(result: dict) -> None:
    path = ROOT / "ledger" / "experiment_reservations.json"
    reservations = json.loads(path.read_text())
    occupied = set()
    for block in reservations.values():
        if isinstance(block, dict) and "selected_values" in block:
            occupied |= set(block["selected_values"])
    for v in result["variants"]:
        if v["value"] in occupied:
            raise ValueError(f"duplicate experiment reservation: ({AXIS}, {v['value']})")


def write_reservation(result: dict) -> None:
    path = ROOT / "ledger" / "experiment_reservations.json"
    reservations = json.loads(path.read_text())
    reservations["mass_add_infill_20261023"] = {
        "session": result["session_branch"],
        "axis": AXIS,
        "value_family": "add-direction coverage infill, per-5 km-block quotas proportional to parent dots",
        "values": [{"value": v["value"], "n_added": v["n_added"], "id": v["id"],
                    "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"]}
                   for v in result["variants"]],
        "why_distinct": (
            "Every recorded MASS add rung (this repo's withdrawn add5pct-next/add20pct-next and the sibling "
            "plus10pct family) selects additions by the parent's stored FIFO-BFS traversal rank, which IR90-20 "
            "measured to be geographic (rank-head adds land in a northern grid strip). This family selects by "
            "exact marginal kernel credit under block-proportional quotas, so it is the first MASS add rung "
            "that is region-even by construction."
        ),
        "checked_utc": result["generated_utc"][:10],
    }
    path.write_text(json.dumps(reservations, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.build:
        result = build()
        check_reservations(result)
        RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        write_ledger(result)
        write_cards(result)
        write_reservation(result)
        print(f"Built {len(result['variants'])} add-direction variants -> {RECEIPT.relative_to(ROOT)}")
        return 0

    receipt = json.loads(RECEIPT.read_text())
    _, foot, cat, r0, stats = b.exact_parent_rebuild()
    dcat = ndi.distance_transform_edt(~cat)
    h19 = b.read_binary(b.DATA / b.PIN_PATHS["h19_5"], foot)
    pool, _ = pool_and_credit(foot, cat, h19, r0, dcat)
    template = b.exact_parent_rebuild()[0]
    for v in receipt["variants"]:
        n_add = v["n_added"]
        res = reach.infill_select(pool, r0, n_total=n_add, block_px=BLOCK_PX)
        expected = r0 | res["selected"]
        if int(expected.sum()) != v["n_dots"]:
            raise ValueError(f"recomputed {v['id']} count mismatch")
        for mode_name in ("nan", "zeros"):
            audit = validate_candidate(ROOT / v["files"][mode_name]["path"], expected, foot, cat,
                                       template, mode_name, r0, dcat, pool)
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"re-read SHA mismatch for {v['id']} {mode_name}")
            tmp = ROOT / ".cache" / "verify_infill" / f"{v['id']}-{mode_name}.tif"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            try:
                b.emit(expected, foot, template, v["id"], mode_name, tmp)
                if b.sha256_file(tmp) != audit["sha256"]:
                    raise ValueError(f"byte-for-byte deterministic re-emit failed for {v['id']} {mode_name}")
            finally:
                tmp.unlink(missing_ok=True)
    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["self_check"] = {"variant_files_re_read_and_validated": True,
                             "variant_bytes_reproduced_exactly": True,
                             "r0_rebuilt_byte_identically": True}
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} add-direction pairs from disk; bytes reproduce exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
