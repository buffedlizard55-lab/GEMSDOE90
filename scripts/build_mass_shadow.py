#!/usr/bin/env python3
"""Build the AXIS=MASS dose ladder from R0 by metric-marginal (shadow) removal.

Every candidate is a strict subset of the byte-identical rebuild of R0
(h33-h33-2-b2, 37,654 unit dots): dots are deleted in ascending order of
exclusive kernel credit, recomputed after every deletion, with no additions and
no moves. 10 / 20 / 30 percent of R0 is removed and nothing else changes.

Ranking rationale: the parent's recorded ranking is the 8-connected FIFO-BFS
visit order of the d2.8 thinning recipe. That is a traversal tie-break, not a
priority, and it deletes spatially contiguous runs. `src/mass.py` instead ranks
by the metric's own first-order marginal term. No truth, no catalogue distance
and no competition score enters the ranking, so this is not label probing.

Run:  .venv/bin/python scripts/build_mass_shadow.py --build
      .venv/bin/python scripts/build_mass_shadow.py --verify
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

import build_r0_variants as b  # noqa: E402  (reuse the audited exact-rebuild path)
from src import mass  # noqa: E402

PARENT = "h33-h33-2-b2"
AXIS = "MASS"
DATE = "20261023"
R0_DOTS = 37_654
DOSE_PCT = (10, 20, 30)
R0_NAN_SHA = "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd"
R0_ZEROS_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
OUT = ROOT / "releases"
RECEIPT = ROOT / "evidence" / "mass_build_receipt.json"

# MODEL brackets (documented in the receipt): the metric's first-order term needs
# two quantities that are not observable without truth -- the removed dots' own
# credit c and the truth pixel count |G|. Both are bracketed, never fitted to a
# score. See src/mass.predicted_removal_delta.
C_BRACKET = (0.15, 0.45)
G_BRACKET = (20_000, 100_000)
PREDICTION = {
    10: ("+0.005 DTI (MODEL; bracket +0.002 to +0.020; not a score)", "+0.005"),
    20: ("+0.009 DTI (MODEL; bracket +0.004 to +0.041; not a score)", "+0.009"),
    30: ("+0.012 DTI (MODEL; bracket +0.004 to +0.063; not a score)", "+0.012"),
}


def validate_candidate(path: Path, expected: np.ndarray, foot: np.ndarray, cat: np.ndarray,
                       sample_profile: dict, mode: str, r0: np.ndarray, dist_cat: np.ndarray) -> dict:
    """Format MUST-pass gate, plus the two design invariants of this axis."""
    with rasterio.open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs, transform = src.crs, src.transform
    dots = (a > 0.5) & foot
    inherited_min = float(dist_cat[dots].min())
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
        "no_new_mass_within_3px": not bool(np.any(dots & ~r0 & (dist_cat < 3.0))),
        "subset_of_R0_no_additions_no_moves": bool(not np.any(dots & ~r0)),
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
        "min_catalogue_distance_px": inherited_min,
        "checks": checks,
    }


def bracket_delta(credit_sum: float, n_removed: int, footprint_px: int) -> dict:
    values = []
    for c in C_BRACKET:
        for g in G_BRACKET:
            values.append(mass.predicted_removal_delta(
                credit_sum=credit_sum, n_removed=n_removed, n_parent=R0_DOTS,
                footprint_px=footprint_px, mean_dot_credit=c, truth_px=g,
            ))
    return {"low": round(min(values), 4), "high": round(max(values), 4),
            "c_bracket": list(C_BRACKET), "truth_px_bracket": list(G_BRACKET)}


def build() -> dict:
    t0 = time.time()
    input_receipt = b.verify_manifest_inputs()          # all 26 pins rechecked
    template, foot, cat, r0, parent_stats = b.exact_parent_rebuild()   # byte-identical R0
    footprint_px = int(foot.sum())
    distance_cat = ndi.distance_transform_edt(~cat)
    ys, xs = np.nonzero(r0)
    pts = np.column_stack([ys, xs]).astype(float)
    neighbours = mass.neighbour_lists(pts)
    alive0 = np.ones(len(pts), dtype=bool)
    credit0 = mass.all_exclusive_credit(pts, neighbours, alive0)

    removal_counts = {p: int(round(p / 100.0 * R0_DOTS)) for p in DOSE_PCT}
    res = mass.greedy_shadow_removal(
        pts, neighbours, n_remove=max(removal_counts.values()),
        snapshots=tuple(removal_counts[p] for p in DOSE_PCT),
    )
    order = res["order"]
    credit_at_removal = res["credit_at_removal"]

    # Report-only comparison with the stored FIFO-BFS order at matched count.
    h19 = b.read_binary(b.DATA / b.PIN_PATHS["h19_5"], foot)
    rank = b.fifo_bfs_visit_rank(h19)
    fifo_order = np.argsort(rank[ys, xs], kind="stable")
    k10 = removal_counts[10]
    fifo_credit_sum = float(credit0[fifo_order[:k10]].sum())
    shadow_credit_sum_10 = float(credit_at_removal[:k10].sum())

    OUT.mkdir(parents=True, exist_ok=True)
    variants = []
    for pct in DOSE_PCT:
        n_rem = removal_counts[pct]
        removed_idx = order[:n_rem]
        removed_mask = res["removed_masks"][n_rem]
        cand_flat = np.zeros_like(r0)
        cand_flat[ys, xs] = ~removed_mask
        candidate = cand_flat & r0
        n_dots = int(candidate.sum())
        if n_dots != R0_DOTS - n_rem:
            raise AssertionError(f"dose {pct}%: {n_dots} dots != {R0_DOTS - n_rem}")
        changed = int(np.count_nonzero(candidate ^ r0))
        pct_changed = 100.0 * changed / R0_DOTS
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"dose {pct}% changes {pct_changed:.4f}% of R0 (required 1-50%)")
        if np.any(candidate & ~r0) or np.any(candidate & cat) or np.any(candidate & ~foot):
            raise AssertionError(f"dose {pct}% is not a catalogue-clean subset of R0")

        credit_sum = float(credit_at_removal[:n_rem].sum())
        delta = bracket_delta(credit_sum, n_rem, footprint_px)
        sub3_removed = int((distance_cat[ys[removed_idx], xs[removed_idx]] < 3.0).sum())
        sub3_total = int((distance_cat[ys, xs] < 3.0).sum())

        slug = f"{PARENT}-MASSshadow{pct}pct-{DATE}"
        temp_nan = OUT / f".{slug}-nan.tmp.tif"
        temp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        b.emit(candidate, foot, template, slug, "nan", temp_nan)
        b.emit(candidate, foot, template, slug, "zeros", temp_zeros)
        nan_sha = b.sha256_file(temp_nan)
        sha8 = nan_sha[:8]
        base = OUT / f"{slug}-{sha8}"
        nan_path, zeros_path = base.with_suffix(".tif"), OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = validate_candidate(nan_path, candidate, foot, cat, template, "nan", r0, distance_cat)
        zeros_audit = validate_candidate(zeros_path, candidate, foot, cat, template, "zeros", r0, distance_cat)

        prediction = PREDICTION[pct]
        cards = {
            "hypothesis": (
                f"Removing the {pct}% of R0 dots with the least exclusive 300 m kernel credit cuts the "
                "false-positive mass term faster than it cuts kernel credit, so live DTI rises."
            ),
            "mechanism": (
                "Under the brief's algebra the mass term 0.2*(S-M) is paid per dot, while credit T is a "
                "max over dots inside the 300 m kernel: a dot whose disk is largely covered by closer "
                "neighbours pays its 0.2 share but supplies almost no T. The ladder deletes dots in "
                "ascending exclusive-credit order (recomputed after each deletion), so the unobservable "
                "credit loss per unit mass removed is minimised. No additions, no moves, no collar change."
            ),
            "non_fault_confounder": (
                "Exclusive credit is truth-free: a dot can have low exclusive credit and still be the only "
                "dot covering a truth pixel that lies in its exclusive lens. Contacts, drainage margins and "
                "topographic lineaments inside the H19-5 support are also covered this way, so the ranking "
                "cannot tell a redundant fault dot from a redundant non-fault dot."
            ),
            "predicted_live_change": prediction[0],
            "model_bracket": (
                f"first-order bracket {delta['low']:+.4f} to {delta['high']:+.4f} DTI over c in "
                f"{C_BRACKET} and truth pixels in {G_BRACKET}; brackets are assumptions, not measurements"
            ),
            "falsifier": (
                f"A same-week paired live receipt against R0 with delta <= -0.005 at this dose falsifies the "
                "premise that these dots were mass-dominated. A monotone decline across 10/20/30% ends the "
                "mass-reduction direction; |delta| < 0.010 is no evidence under the session rule."
            ),
            "structural_geologist_note": (
                "Review the deleted dots as a map: they are the ones whose 300 m explainable-credit was "
                "already held by a neighbouring dot. If a deleted dot sits on an unmapped strand rather than "
                "in the shadow of a mapped one, that deletion is geologically wrong and the ladder's negative "
                "result would be the correct outcome."
            ),
        }
        note = f"{PARENT}; MASS shadow-drop {pct}% -> {R0_DOTS - n_rem} dots; predicted {prediction[1]} MODEL"
        if len(note) > 140:
            raise AssertionError(f"form note is {len(note)} chars")
        variants.append({
            "id": base.name,
            "parent": PARENT,
            "axis": AXIS,
            "value": f"shadow-drop {pct}% (exclusive-credit greedy, no additions)",
            "dose_pct": pct,
            "n_dots": n_dots,
            "pct_changed": pct_changed,
            "removed_dots": n_rem,
            "added_dots": 0,
            "retained_dots": n_dots,
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "evidence_class": "MODEL (predicted change only)",
            "predicted_change": prediction[0],
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": {
                "removed_from_parent": n_rem, "added": 0, "moved": 0, "retained_parent": n_dots,
                "symmetric_difference_px": changed, "pct_changed_of_R0": pct_changed,
            },
            "removal_statistics": {
                "exclusive_credit_sum": credit_sum,
                "exclusive_credit_mean": credit_sum / n_rem,
                "exclusive_credit_max": float(credit_at_removal[:n_rem].max()),
                "isolated_dot_credit_area": mass.credit_disk_area(),
                "r0_total_exclusive_credit": float(credit0.sum()),
                "share_of_r0_credit_removed": credit_sum / float(credit0.sum()),
                "sub3px_dots_removed": sub3_removed,
                "sub3px_dots_in_parent": sub3_total,
                "min_catalogue_distance_px_inherited": nan_audit["min_catalogue_distance_px"],
            },
            "model_bracket": delta,
            "mechanism_card": cards,
        })

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": b.git_sha(),
        "axis": AXIS,
        "ranking": {
            "used": "exclusive kernel credit, ascending, recomputed after each deletion (src/mass.py)",
            "not_used": "the parent's stored 8-connected FIFO-BFS thinning order (traversal tie-break, spatially contiguous)",
            "truth_used": False, "catalogue_used_in_ranking": False, "score_used": False,
            "kernel_radius_px": mass.R_DEFAULT,
            "isolated_dot_credit_area": mass.credit_disk_area(),
            "matched_count_comparison_at_10pct": {
                "shadow_exclusive_credit_sum": shadow_credit_sum_10,
                "fifo_order_exclusive_credit_sum": fifo_credit_sum,
                "fifo_excess_fraction": fifo_credit_sum / shadow_credit_sum_10 - 1.0,
                "note": "REPORT ONLY: at the same 3,765 removals the stored order destroys this much more "
                        "explainable credit than the shadow order does",
            },
        },
        "parent": {"id": PARENT, "claimed_live_score": 0.2778, "evidence_class": "CLAIM",
                   "zeros_sha256": R0_ZEROS_SHA, "nan_sha256": R0_NAN_SHA, **parent_stats},
        "manifest": {"manifest_path": "registry/data_manifest.json", "verified_count": len(input_receipt),
                     "all_pins_rechecked": True, "files": input_receipt},
        "footprint_px": footprint_px,
        "proxy_reports": {
            "leakage_canary": {
                "status": "NOT APPLICABLE",
                "reason": "This axis uses no feature band and no label: the ranking is a deterministic "
                          "function of the parent's own dot coordinates. Nothing new can leak.",
            },
            "catalogue_hide_recover": {
                "status": "NOT RUN",
                "reason": "R0 itself was pruned against the full catalogue, so a catalogue holdout cannot "
                          "separate real new-fault credit from the catalogue collar; ranking on it would only "
                          "reward mass. Report-only instrument, never a gate.",
            },
            "sgmc_control": {"status": "NOT RUN", "reason": "No fold-clean SGMC control is calibrated for a "
                                                           "mass-only subset edit; not a gate."},
        },
        "variants": variants,
        "hard_constraint_note": (
            "Brief s4 asks >=3 px from the catalogue. R0's own minimum is 2.236 px (1,611 dots, IR90-01); "
            "these variants inherit that collar unchanged because changing it is a second axis. They add no "
            "mass at all and emit zero catalogue mass."
        ),
        "elapsed_s": round(time.time() - t0, 1),
        "no_live_submission": True,
        "agent_did_not_submit": True,
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
            # Keep every historical and previously-built row; replace only this axis's own rows
            # so that a rebuild is idempotent instead of appending duplicates.
            existing = [r for r in csv.DictReader(f)
                        if r.get("id") not in new_ids and (r.get("axis") or "").upper() != AXIS]
    rows = existing
    for v in result["variants"]:
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)", "encoding": "nan primary; zeros fallback",
            "n_dots": v["n_dots"], "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"], "parent": v["parent"],
            "axis": v["axis"], "value": v["value"], "status": "BUILT", "receipt": "N",
            "receipt_score": "", "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": "strict subset of rebuilt R0; no additions or moves; receipt_score/date to be filled by human",
        })
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def check_reservations() -> None:
    """Fail closed if this exact (AXIS, value) dose was already built anywhere indexed."""
    reservations = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text())
    mass_block = reservations.get("mass_axis", {})
    occupied = set(mass_block.get("sibling_values", []))
    for v in DOSE_PCT:
        key = f"shadow{v}pct"
        if key in occupied:
            raise ValueError(f"duplicate experiment reservation: (MASS, {key}) already recorded")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    if args.build:
        check_reservations()
        result = build()
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        write_ledger(result)
        print(f"Built {len(result['variants'])} MASS variants from exact R0 -> {RECEIPT.relative_to(ROOT)}")
        for v in result["variants"]:
            print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.2f}% changed, "
                  f"sha256={v['sha256'][:12]}..., E_sum={v['removal_statistics']['exclusive_credit_sum']:.0f}")
        return 0

    # --verify: rebuild every expected mask from disk-pinned inputs and re-read each file.
    receipt = json.loads(RECEIPT.read_text())
    b.verify_manifest_inputs()
    template, foot, cat, r0, _stats = b.exact_parent_rebuild()
    ys, xs = np.nonzero(r0)
    dist_cat = ndi.distance_transform_edt(~cat)
    pts = np.column_stack([ys, xs]).astype(float)
    neighbours = mass.neighbour_lists(pts)
    res = mass.greedy_shadow_removal(
        pts, neighbours, n_remove=max(int(v["removed_dots"]) for v in receipt["variants"]),
        snapshots=tuple(int(v["removed_dots"]) for v in receipt["variants"]),
    )
    for v in receipt["variants"]:
        n_rem = int(v["removed_dots"])
        flat = np.zeros_like(r0)
        flat[ys, xs] = ~res["removed_masks"][n_rem]
        expected = flat & r0
        credit_sum = float(res["credit_at_removal"][:n_rem].sum())
        if not math.isclose(credit_sum, v["removal_statistics"]["exclusive_credit_sum"], rel_tol=1e-9):
            raise ValueError(f"{v['id']}: exclusive-credit sum not reproducible")
        for mode_name in ("nan", "zeros"):
            audit = validate_candidate(ROOT / v["files"][mode_name]["path"], expected, foot, cat,
                                       template, mode_name, r0, dist_cat)
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"{v['id']} {mode_name}: re-read SHA mismatch")
            tmp = ROOT / ".cache" / "verify_mass_bytes" / f"{v['id']}-{mode_name}.tif"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            try:
                b.emit(expected, foot, template, v["id"], mode_name, tmp)
                if b.sha256_file(tmp) != audit["sha256"]:
                    raise ValueError(f"{v['id']} {mode_name}: deterministic re-emit failed")
            finally:
                tmp.unlink(missing_ok=True)
    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = b.git_sha()
    receipt["generator_script_sha256"] = b.sha256_file(Path(__file__))
    receipt["self_check"] = {
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "r0_rebuilt_byte_identically": True,
        "ranking_reproduced_from_dots_only": True,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} MASS variants from disk; R0 byte-identical to {R0_ZEROS_SHA[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
