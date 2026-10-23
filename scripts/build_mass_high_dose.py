#!/usr/bin/env python3
"""High-dose MASS arms from the byte-identical R0, plus the credit-blind control the
existing 10/20/30% ladder has never had.

Session axis: MASS (agent-selected, not assigned). New (AXIS, value) pairs only:

  shadow-drop 40%   delete the 15,062 lowest-exclusive-credit dots of R0
  shadow-drop 48%   delete the 18,072 lowest-exclusive-credit dots of R0
  random-drop 40%   delete 15,062 dots drawn uniformly at random (seed 20261023)

The two shadow arms continue `scripts/build_mass_shadow.py` with the same parent,
the same ranking code and the same gate, nested by construction. The random arm is
the matched-count, matched-dose control: it has the same spatial distribution as R0
in expectation but is blind to kernel credit, so `shadow40` vs `rand40` separates
"the ranking removes redundancy" from "any 40% removal helps".

Two doses were built, probed and then rejected before any submission, and both
probes are kept in the receipt: (a) the parent's stored 8-connected FIFO-BFS order,
which the sibling MASS doses use -- at 10% it already deletes mass from one south-east
corner and at 40% it empties 41% of 5 km blocks, in one contiguous 632-block hole;
(b) a 50% shadow drop -- the deepest dose, where the greedy starts to empty whole
contiguous regions (largest emptied cluster 17 blocks, 425 km2). Both are
region-isolated files under Hard Constraint #5, so the deep arm stops at 48%, the
largest dose whose every candidate passes the region-evenness gate.

Nothing is added or moved; every candidate is a strict subset of R0. No truth, no
label, no catalogue distance and no score enters any ranking, so this is not label
probing. Rasters are written to ignored `releases/` and must not be committed.

Run:    .venv/bin/python scripts/build_mass_high_dose.py --build
Verify: .venv/bin/python scripts/build_mass_high_dose.py --verify
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
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_r0_variants as b            # noqa: E402  audited exact-R0 rebuild path
import build_mass_shadow as shadow       # noqa: E402  audited gate + existing ladder
from src import mass                     # noqa: E402  exclusive-credit ranking

PARENT = "h33-h33-2-b2"
AXIS = "MASS"
DATE = "20261023"
R0_DOTS = 37_654
SEED = 20261023
OUT = ROOT / "releases"
RECEIPT = ROOT / "evidence" / "mass_high_dose_receipt.json"
LADDER_RECEIPT = ROOT / "evidence" / "mass_build_receipt.json"
LEDGER = ROOT / "ledger" / "submissions.csv"
R0_NAN_SHA = "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd"
R0_ZEROS_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"

# (dose percent, selection rule). 40% is built twice so the pair differs only in which
# dots leave; 50% extends the ladder to the brief's 50% change cap.
ARMS = ((40, "shadow"), (48, "shadow"), (40, "random"))

# Decelerating continuation of the recorded ladder predictions (+0.005 / +0.009 /
# +0.012 at 10 / 20 / 30%) and of the nearest recorded mass-only step in the ledger
# (d1.5 0.2477 -> d2.8 0.2600 at ~27% less mass, +0.0123). MODEL only: no MASS dose
# has a receipt, and the first-order brackets are assumptions, not measurements.
POINT_PREDICTION = {40: 0.014, 48: 0.015}
BRACKET = {40: (0.004, 0.025), 48: (0.002, 0.030)}

# Region-isolation gate (Hard Constraint #5), measured per 5 km block:
#   * no more than 2% of blocks holding >=20 R0 dots may lose >=90% of their dots;
#   * the 5th percentile of the per-block removed share may not fall below a quarter
#     of the nominal dose (catches corner-only deletions);
#   * the largest cluster of 8-connected near-emptied blocks (>=90% removed, blocks
#     holding >=5 dots) may not exceed 4 blocks, i.e. no contiguous hole over 100 km2.
# R0 has ~7.3 dots/km2, so a full 25 km2 block holds ~180 dots and a 100 km2 hole is
# a genuine regional blank, not a rounding artefact.
BLOCK_PX = 50
MAX_FRACTION_BLOCKS_EMPTIED = 0.02
MAX_EMPTIED_CLUSTER_BLOCKS = 4
MIN_P05_SHARE_FRACTION = 0.25

FIELDS = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
          "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
          "receipt_score", "predicted_change", "date", "form_note", "notes"]


def removal_count(pct: int) -> int:
    return int(round(pct / 100.0 * R0_DOTS))


def arm_slug(pct: int, rule: str) -> str:
    return f"{PARENT}-MASS{rule}{pct}pct-{DATE}"


def random_removal(n: int, n_remove: int, seed: int = SEED) -> np.ndarray:
    """Seeded uniform subset. Spatially even by construction, blind to kernel credit."""
    picked = np.random.default_rng(seed).choice(n, size=n_remove, replace=False)
    return np.sort(picked)


def fifo_removal_order(xs_rank: np.ndarray) -> np.ndarray:
    """Indices in the order the parent's stored thinning recipe deprioritises them.

    Kept only for the report-only comparison: this order is spatially concentrated and
    is therefore unusable as a mass control (see module docstring).
    """
    return np.argsort(xs_rank, kind="stable")[::-1]


def spatial_removal_report(removed: np.ndarray, ys: np.ndarray, xs: np.ndarray, shape: tuple[int, int],
                           dose: float) -> dict:
    """Per-5 km-block removal share: the region-isolation statistic and its gate."""
    tot = np.zeros((shape[0] // BLOCK_PX + 2, shape[1] // BLOCK_PX + 2))
    rem = np.zeros_like(tot)
    np.add.at(tot, (ys // BLOCK_PX, xs // BLOCK_PX), 1)
    np.add.at(rem, (ys[removed] // BLOCK_PX, xs[removed] // BLOCK_PX), 1)
    share_all = np.divide(rem, tot, out=np.zeros_like(rem), where=tot > 0)
    blown = (tot >= 5) & (share_all >= 0.9)
    _lab, n_clusters = ndi.label(blown, structure=np.ones((3, 3), dtype=np.uint8))
    cluster_sizes = np.bincount(_lab.ravel())[1:] if n_clusters else np.zeros(0, dtype=int)
    keep20 = tot >= 20
    share = share_all[keep20]
    return {
        "block_px": BLOCK_PX,
        "blocks_with_20plus_dots": int(keep20.sum()),
        "removed_share_mean": round(float(share.mean()), 4),
        "removed_share_p05": round(float(np.percentile(share, 5)), 4),
        "removed_share_p95": round(float(np.percentile(share, 95)), 4),
        "removed_share_max": round(float(share.max()), 4),
        "fraction_blocks_90pct_emptied": round(float((share >= 0.9).mean()), 4),
        "fraction_blocks_10pct_or_less": round(float((share <= 0.1).mean()), 4),
        "emptied_block_clusters": int(n_clusters),
        "largest_emptied_cluster_blocks": int(cluster_sizes.max()) if cluster_sizes.size else 0,
        "bbox_y": [int(ys[removed].min()), int(ys[removed].max())],
        "bbox_x": [int(xs[removed].min()), int(xs[removed].max())],
        "nominal_dose": round(float(dose), 4),
    }


def region_evenness_gate(report: dict) -> bool:
    return (report["fraction_blocks_90pct_emptied"] <= MAX_FRACTION_BLOCKS_EMPTIED
            and report["removed_share_p05"] >= MIN_P05_SHARE_FRACTION * report["nominal_dose"]
            and report["largest_emptied_cluster_blocks"] <= MAX_EMPTIED_CLUSTER_BLOCKS)


def strand_report(dots: np.ndarray, link_px: float = 5.0) -> dict:
    """REPORT ONLY: what a geologist would see. Dots linked at <= link_px form strands.

    R0 is a pointillist field (median nearest-neighbour spacing 3 px, i.e. 300 m), so
    strands only appear once the linking distance exceeds the kernel radius; link_px=5
    (500 m) is reported as the trace-continuity view, never as a score proxy.
    """
    ys, xs = np.nonzero(dots)
    pts = np.column_stack([ys, xs]).astype(float)
    if len(pts) < 2:
        return {"dots": int(len(pts)), "link_px": link_px}
    tree = cKDTree(pts)
    dist, _ = tree.query(pts, k=2)
    nn = dist[:, 1]
    pairs = np.asarray(sorted(tree.query_pairs(link_px)), dtype=np.int64)
    n = len(pts)
    lab = np.arange(n)

    def find(a: int) -> int:
        while lab[a] != a:
            lab[a] = lab[lab[a]]
            a = lab[a]
        return a

    for i, j in pairs.tolist():
        ri, rj = find(i), find(j)
        if ri != rj:
            lab[ri] = rj
    sizes = np.unique([find(i) for i in range(n)], return_counts=True)[1]
    return {
        "dots": int(n),
        "link_px": link_px,
        "strands": int(len(sizes)),
        "strands_ge_10dots": int((sizes >= 10).sum()),
        "largest_strand_dots": int(sizes.max()),
        "mean_nearest_neighbour_px": round(float(nn.mean()), 4),
        "median_nearest_neighbour_px": round(float(np.median(nn)), 4),
        "fraction_nn_beyond_kernel": round(float((nn > mass.R_DEFAULT).mean()), 4),
    }


def build() -> dict:
    t0 = time.time()
    input_receipt = b.verify_manifest_inputs()                          # all 26 pins rechecked
    template, foot, cat, r0, parent_stats = b.exact_parent_rebuild()   # byte-identical R0
    if parent_stats["r0_rebuilt_zeros_sha256"] != R0_ZEROS_SHA:
        raise ValueError("R0 rebuild is not the recorded parent")
    footprint_px = int(foot.sum())
    distance_cat = ndi.distance_transform_edt(~cat)
    ys, xs = np.nonzero(r0)
    if len(ys) != R0_DOTS:
        raise ValueError(f"R0 dot count {len(ys)} != {R0_DOTS}")
    pts = np.column_stack([ys, xs]).astype(float)
    neighbours = mass.neighbour_lists(pts)
    credit0 = mass.all_exclusive_credit(pts, neighbours, np.ones(len(pts), dtype=bool))

    counts = sorted({removal_count(p) for p, rule in ARMS if rule == "shadow"} | {removal_count(50)})
    res = mass.greedy_shadow_removal(pts, neighbours, n_remove=max(counts), snapshots=tuple(counts))

    # Report-only: why the parent's stored order is not used as a control.
    h19 = b.read_binary(b.DATA / b.PIN_PATHS["h19_5"], foot)
    fifo_order = fifo_removal_order(b.fifo_bfs_visit_rank(h19)[ys, xs])
    rejected_probes = {}
    for pct in (10, 20, 40):
        mask = np.zeros(R0_DOTS, dtype=bool)
        mask[fifo_order[:removal_count(pct)]] = True
        rep = spatial_removal_report(mask, ys, xs, r0.shape, pct / 100.0)
        rep["candidate_built"] = False
        rep["passes_region_evenness_gate"] = region_evenness_gate(rep)
        rejected_probes[f"fifo{pct}pct"] = rep
    deep = spatial_removal_report(res["removed_masks"][removal_count(50)], ys, xs, r0.shape, 0.50)
    deep["candidate_built"] = False
    deep["passes_region_evenness_gate"] = region_evenness_gate(deep)
    rejected_probes["shadow50pct"] = deep

    matched = removal_count(40)
    shadow_credit_40 = float(res["credit_at_removal"][:matched].sum())
    rand_idx_40 = random_removal(R0_DOTS, matched)
    rand_mask_40 = np.zeros(R0_DOTS, dtype=bool)
    rand_mask_40[rand_idx_40] = True
    rand_credit_40 = float(credit0[rand_mask_40].sum())
    fifo_credit_40 = float(credit0[fifo_order[:matched]].sum())
    ratio = shadow_credit_40 / rand_credit_40

    existing_ladder = json.loads(LADDER_RECEIPT.read_text()) if LADDER_RECEIPT.is_file() else {}
    ladder_ids = {v["id"]: v["sha256"] for v in existing_ladder.get("variants", [])}

    OUT.mkdir(parents=True, exist_ok=True)
    variants = []
    for pct, rule in ARMS:
        n_rem = removal_count(pct)
        if rule == "shadow":
            removed = res["removed_masks"][n_rem]
            credit_sum = float(res["credit_at_removal"][:n_rem].sum())
            ranking_text = ("ascending exclusive 300 m kernel credit, recomputed after each deletion "
                            "(src/mass.py)")
        else:
            removed = np.zeros(R0_DOTS, dtype=bool)
            removed[random_removal(R0_DOTS, n_rem)] = True
            credit_sum = float(credit0[removed].sum())
            ranking_text = f"seeded uniform random subset, numpy default_rng({SEED}); credit-blind control"
        candidate = r0.copy()
        candidate[ys[removed], xs[removed]] = False
        n_dots = int(candidate.sum())
        if n_dots != R0_DOTS - n_rem:
            raise AssertionError(f"{rule} {pct}%: {n_dots} dots != {R0_DOTS - n_rem}")
        changed = int(np.count_nonzero(candidate ^ r0))
        pct_changed = 100.0 * changed / R0_DOTS
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"{rule} {pct}% changes {pct_changed:.4f}% of R0 (required 1-50%)")
        if np.any(candidate & ~r0) or np.any(candidate & cat) or np.any(candidate & ~foot):
            raise AssertionError(f"{rule} {pct}% is not a catalogue-clean subset of R0")
        spatial = spatial_removal_report(removed, ys, xs, r0.shape, pct / 100.0)
        spatial["passes_region_evenness_gate"] = region_evenness_gate(spatial)
        if not spatial["passes_region_evenness_gate"]:
            raise ValueError(f"{rule} {pct}% fails the region-evenness gate: {spatial}")

        slug = arm_slug(pct, rule)
        temp_nan, temp_zeros = OUT / f".{slug}-nan.tmp.tif", OUT / f".{slug}-zeros.tmp.tif"
        b.emit(candidate, foot, template, slug, "nan", temp_nan)
        b.emit(candidate, foot, template, slug, "zeros", temp_zeros)
        sha8 = b.sha256_file(temp_nan)[:8]
        base = OUT / f"{slug}-{sha8}"
        nan_path, zeros_path = base.with_suffix(".tif"), OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = shadow.validate_candidate(nan_path, candidate, foot, cat, template, "nan", r0, distance_cat)
        zeros_audit = shadow.validate_candidate(zeros_path, candidate, foot, cat, template, "zeros", r0, distance_cat)

        structure = {"parent": strand_report(r0), "candidate": strand_report(candidate)}
        point = POINT_PREDICTION[pct] * (shadow_credit_40 / credit_sum if rule == "random" else 1.0)
        low, high = BRACKET[pct]
        if rule == "random":
            low, high = low * ratio, high * ratio
        pred_text = f"{point:+.3f} DTI (MODEL; bracket {low:+.3f} to {high:+.3f}; not a score)"
        cards = {
            "hypothesis": (
                f"Deleting the {pct}% of R0 dots with the least exclusive 300 m kernel credit continues to "
                "raise live DTI, because the mass term is paid per dot while kernel credit is a max over "
                "dots inside 300 m; a credit-blind deletion of the same size should gain less."
            ),
            "mechanism": (
                "D = 0.2T + 0.2(S-M) + 0.8|G| charges 0.2 per unit of predicted mass but credits T only once "
                "per truth pixel. A dot whose disk is already covered by closer neighbours pays its full 0.2 "
                "share and supplies almost no T, so deleting it lowers D by 0.2(1-c) while T barely moves. "
                "Ranking by exclusive credit (the credit only that dot supplies, recomputed after each "
                "deletion) minimises the unobservable T loss per unit mass removed. The 40% and 50% doses "
                "test whether that gain keeps compounding or turns over once strands start to be eaten."
            ),
            "non_fault_confounder": (
                "Exclusive credit is truth-free. A dot can have near-zero exclusive credit and still be the "
                "only dot covering a genuine new strand that lies in the shadow of a mapped one; lithologic "
                "contacts, drainage margins and topographic lineaments are shadowed identically. Deep doses "
                "thin every trace, so a negative result at 40-50% is as consistent with 'the removed strands "
                "were real' as with 'the metric punishes sparse coverage'."
            ),
            "matched_count_control": (
                "random-drop 40% removes 15,062 dots drawn uniformly at random with a recorded seed: same "
                "dose, same spatial distribution in expectation, blind to kernel credit. At matched count the "
                f"random set destroys {credit_sum / shadow_credit_40 - 1:+.1%} more exclusive credit than the "
                f"shadow set (shadow E={shadow_credit_40:.0f}, this arm E={credit_sum:.0f}, of "
                f"{credit0.sum():.0f} total)."
            ),
            "competing_prediction": (
                "The structural report contradicts the credit argument in the opposite direction. R0 "
                f"carries {structure['parent']['strands_ge_10dots']} strands of >=10 dots (>=1 km) at 5 px "
                f"linking; this arm keeps {structure['candidate']['strands_ge_10dots']} of them and raises "
                f"mean dot spacing from {structure['parent']['mean_nearest_neighbour_px']:.1f} px to "
                f"{structure['candidate']['mean_nearest_neighbour_px']:.1f} px "
                f"({structure['candidate']['fraction_nn_beyond_kernel']:.0%} of dots farther than the 3 px "
                "kernel from their nearest neighbour). If new-fault truth is line-like, T depends on "
                "along-strike continuity and this arm could score BELOW the credit-blind control even though "
                "it destroys less exclusive credit. Both predictions are recorded; the paired live receipts "
                "decide, and |delta| < 0.010 is no evidence."
            ),
            "predicted_live_change": pred_text,
            "model_bracket": (
                f"first-order bracket {low:+.4f} to {high:+.4f} DTI; ladder-anchored point estimate. Brackets "
                "are assumptions, not measurements, and a live delta below 0.010 is no evidence."
            ),
            "falsifier": (
                "A same-week paired live receipt against R0 with delta <= -0.005 at 40% falsifies the dose "
                "direction. If rand40 lands within 0.005 of shadow40, the exclusive-credit ranking adds "
                "nothing and the ladder is really a pure mass effect; if rand40 beats shadow40 by >= 0.005 "
                "the ranking is wrong and must be abandoned. |delta| < 0.010 is no evidence either way."
            ),
            "structural_geologist_note": (
                "Review the deleted dots as a map. At 40-50% whole short strands and trace tips leave and the "
                "mean dot spacing grows from 3 px (300 m) to 6-7 px (600-700 m), i.e. beyond the metric's "
                "own kernel radius. If the survivors still chart as strike-consistent lineaments, the "
                "deletion is defensible; where a deleted dot closed a step-over or a mapped-trace "
                "termination, the deletion is geologically wrong and a negative live result should be "
                "believed."
            ),
        }
        note = f"{PARENT}; MASS {rule}-drop {pct}% -> {R0_DOTS - n_rem} dots; predicted {point:+.3f} MODEL"
        if len(note) > 140:
            raise AssertionError(f"form note is {len(note)} chars: {note}")
        variants.append({
            "id": base.name,
            "parent": PARENT,
            "axis": AXIS,
            "value": (f"shadow-drop {pct}% (exclusive-credit greedy, no additions)" if rule == "shadow"
                      else f"random-drop {pct}% (seeded {SEED}, credit-blind, no additions)"),
            "selection_rule": rule,
            "dose_pct": pct,
            "ranking": ranking_text,
            "seed": SEED if rule == "random" else None,
            "n_dots": n_dots,
            "pct_changed": pct_changed,
            "removed_dots": n_rem,
            "added_dots": 0,
            "moved_dots": 0,
            "retained_dots": n_dots,
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "evidence_class": "MODEL (predicted change only)",
            "predicted_change": pred_text,
            "point_prediction_dti": round(point, 4),
            "model_bracket": {"low": round(float(low), 4), "high": round(float(high), 4),
                              "basis": ("ladder-anchored continuation of the recorded 10/20/30% predictions; "
                                        "first-order credit term bracketed over unobservable c and |G|. "
                                        "Assumptions, not measurements.")},
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": {
                "removed_from_parent": n_rem, "added": 0, "moved": 0, "retained_parent": n_dots,
                "symmetric_difference_px": changed, "pct_changed_of_R0": pct_changed,
            },
            "removal_statistics": {
                "exclusive_credit_sum": credit_sum,
                "exclusive_credit_mean": credit_sum / n_rem,
                "exclusive_credit_max": float(
                    res["credit_at_removal"][:n_rem].max() if rule == "shadow" else credit0[removed].max()),
                "r0_total_exclusive_credit": float(credit0.sum()),
                "share_of_r0_credit_removed": credit_sum / float(credit0.sum()),
                "min_catalogue_distance_px_inherited": nan_audit["min_catalogue_distance_px"],
                "sub3px_dots_removed": int((distance_cat[ys[removed], xs[removed]] < 3.0).sum()),
                "sub3px_dots_in_parent": int((distance_cat[ys, xs] < 3.0).sum()),
            },
            "spatial_removal": spatial,
            "structure_report_only": structure,
            "mechanism_card": cards,
        })

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": b.git_sha(),
        "axis": AXIS,
        "session": "2026-10-23c high-dose MASS + credit-blind control",
        "parent": {"id": PARENT, "claimed_live_score": 0.2778, "evidence_class": "CLAIM",
                   "zeros_sha256": R0_ZEROS_SHA, "nan_sha256": R0_NAN_SHA, **parent_stats},
        "manifest": {"manifest_path": "registry/data_manifest.json",
                     "verified_count": len(input_receipt), "all_pins_rechecked": True,
                     "files": input_receipt},
        "footprint_px": footprint_px,
        "random_seed": SEED,
        "previous_ladder": {
            "receipt": "evidence/mass_build_receipt.json",
            "ids": ladder_ids,
            "note": ("10/20/30% shadow doses are owned by scripts/build_mass_shadow.py; this session adds "
                     "only new (MASS, value) pairs and re-derives them from the same parent with the same gate."),
        },
        "ranking": {
            "used_shadow": "exclusive kernel credit, ascending, recomputed after each deletion (src/mass.py)",
            "used_random": f"seeded uniform random subset (numpy default_rng({SEED}))",
            "rejected_fifo": ("the parent's stored 8-connected FIFO-BFS visit order, descending: spatially "
                              "concentrated, one contiguous 632-block hole at the 40% dose"),
            "rejected_shadow50": ("50% shadow drop: the greedy starts emptying whole contiguous regions "
                                  "(largest emptied cluster 17 blocks = 425 km2)"),
            "truth_used": False, "catalogue_used_in_ranking": False, "score_used": False,
            "kernel_radius_px": mass.R_DEFAULT,
            "isolated_dot_credit_area_px2": round(mass.credit_disk_area(), 4),
            "rejected_region_isolation_probes": rejected_probes,
            "matched_count_comparison_at_40pct": {
                "shadow_exclusive_credit_sum": round(shadow_credit_40, 4),
                "random_exclusive_credit_sum": round(rand_credit_40, 4),
                "fifo_exclusive_credit_sum": round(fifo_credit_40, 4),
                "random_excess_fraction_vs_shadow": round(rand_credit_40 / shadow_credit_40 - 1.0, 6),
                "fifo_excess_fraction_vs_shadow": round(fifo_credit_40 / shadow_credit_40 - 1.0, 6),
                "note": ("REPORT ONLY: at the same 15,062 removals this is how much more explainable credit "
                         "the credit-blind and stored-order sets destroy than the shadow set does"),
            },
        },
        "region_evenness_gate": {
            "block_px": BLOCK_PX,
            "max_fraction_of_blocks_90pct_emptied": MAX_FRACTION_BLOCKS_EMPTIED,
            "max_emptied_cluster_blocks": MAX_EMPTIED_CLUSTER_BLOCKS,
            "min_p05_share_fraction_of_dose": MIN_P05_SHARE_FRACTION,
            "why": ("Hard Constraint #5 forbids region-isolated files. Every candidate must remove mass "
                    "spatially evenly, which the parent's stored FIFO-BFS order does not."),
        },
        "proxy_reports": {
            "leakage_canary": {
                "status": "NOT APPLICABLE",
                "reason": ("No feature band and no label is read: every ranking is a deterministic function "
                           "of the parent's own dot coordinates. Nothing new can leak."),
            },
            "catalogue_hide_recover": {
                "status": "NOT RUN",
                "reason": ("R0 was already pruned against the full catalogue, so a catalogue holdout cannot "
                           "separate real new-fault credit from the collar; it would only reward mass. "
                           "Report-only instrument, never a gate."),
            },
            "sgmc_control": {"status": "NOT RUN",
                             "reason": "No fold-clean SGMC control is calibrated for a mass-only subset edit."},
        },
        "variants": variants,
        "hard_constraint_note": (
            "Brief s4 asks >=3 px from the catalogue. R0's own minimum is 2.236 px (1,611 dots, IR90-01); "
            "these variants inherit that collar unchanged because changing it would be a second axis. They "
            "add no mass at all, so no new near-catalogue mass is created, and catalogue mass is zero."
        ),
        "deadline_note": ("Deadline 2026-12-03 and the 3-scored-submissions-per-week rule are supplied by the "
                          "brief, not re-verified: automated access to DrivenData is prohibited. The human "
                          "confirms both on the competition page."),
        "elapsed_s": round(time.time() - t0, 1),
        "no_live_submission": True,
        "agent_did_not_submit": True,
    }
    return result


def check_reservations() -> None:
    """Fail closed if one of these (AXIS, value) pairs was already built anywhere indexed."""
    reservations = json.loads((ROOT / "ledger" / "experiment_reservations.json").read_text())
    block = reservations.get("mass_high_dose", {})
    taken = {v.lower() for v in block.get("sibling_values", [])}
    for pct, rule in ARMS:
        if f"{rule}{pct}pct" in taken:
            raise ValueError(f"duplicate experiment reservation: (MASS, {rule}{pct}pct) already recorded")
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("axis") or "").upper() != AXIS:
                    continue
                value = (row.get("value") or "").lower()
                for pct, rule in ARMS:
                    if f"{rule}-drop {pct}%" in value:
                        raise ValueError(
                            f"duplicate experiment reservation: (MASS, {rule}-drop {pct}%) already in ledger "
                            f"as {row.get('id')}")


def write_ledger(result: dict) -> None:
    """Append this session's rows; never rewrite or drop another session's rows."""
    own = {v["id"] for v in result["variants"]}
    rows = []
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("id") not in own]
    existing_hashes = {r.get("sha256") for r in rows} | {r.get("sha256_zeros") for r in rows}
    for v in result["variants"]:
        if v["sha256"] in existing_hashes or v["sha256_zeros"] in existing_hashes:
            raise ValueError(f"sha256 already present in ledger: {v['id']}")
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)", "encoding": "nan primary; zeros fallback",
            "n_dots": v["n_dots"], "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"], "parent": v["parent"],
            "axis": v["axis"], "value": v["value"], "status": "BUILT", "receipt": "N",
            "receipt_score": "", "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": ("strict subset of rebuilt R0; no additions, no moves, no collar change; "
                      "receipt_score/date to be filled by the human; agent never submits"),
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify() -> int:
    receipt = json.loads(RECEIPT.read_text())
    b.verify_manifest_inputs()
    template, foot, cat, r0, _stats = b.exact_parent_rebuild()
    ys, xs = np.nonzero(r0)
    distance_cat = ndi.distance_transform_edt(~cat)
    pts = np.column_stack([ys, xs]).astype(float)
    neighbours = mass.neighbour_lists(pts)
    shadow_counts = [int(v["removed_dots"]) for v in receipt["variants"] if v["selection_rule"] == "shadow"]
    res = mass.greedy_shadow_removal(pts, neighbours, n_remove=max(shadow_counts),
                                     snapshots=tuple(shadow_counts))
    for v in receipt["variants"]:
        n_rem = int(v["removed_dots"])
        expected = r0.copy()
        if v["selection_rule"] == "shadow":
            expected[ys, xs] = ~res["removed_masks"][n_rem]
        else:
            pick = random_removal(len(ys), n_rem, int(v.get("seed") or SEED))
            expected[ys[pick], xs[pick]] = False
        expected &= r0
        if int(expected.sum()) != v["n_dots"]:
            raise ValueError(f"{v['id']}: recomputed count mismatch")
        for mode_name in ("nan", "zeros"):
            audit = shadow.validate_candidate(ROOT / v["files"][mode_name]["path"], expected, foot, cat,
                                              template, mode_name, r0, distance_cat)
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"{v['id']} {mode_name}: re-read SHA mismatch")
            tmp = ROOT / ".cache" / "verify_mass_high_dose" / f"{v['id']}-{mode_name}.tif"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            try:
                b.emit(expected, foot, template, v["id"], mode_name, tmp)
                if b.sha256_file(tmp) != audit["sha256"]:
                    raise ValueError(f"{v['id']} {mode_name}: deterministic re-emit failed")
            finally:
                tmp.unlink(missing_ok=True)
        if not math.isclose(v["pct_changed"], 100.0 * n_rem / R0_DOTS, rel_tol=1e-9):
            raise ValueError(f"{v['id']}: pct_changed is not the exact parent diff")
        if not region_evenness_gate(v["spatial_removal"]):
            raise ValueError(f"{v['id']}: region-evenness gate fails on the recorded statistics")
    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = b.git_sha()
    receipt["generator_script_sha256"] = b.sha256_file(Path(__file__))
    receipt["self_check"] = {
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "r0_rebuilt_byte_identically": True,
        "no_additions_no_moves": True,
        "region_evenness_gate_rechecked": True,
        "sha256_absent_from_ledger_before_write": True,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} high-dose pairs from disk; "
          f"R0 rebuilt byte-identically to {R0_ZEROS_SHA[:12]}...")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        return verify()
    check_reservations()
    result = build()
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_ledger(result)
    print(f"Built {len(result['variants'])} high-dose MASS variants from exact R0 -> "
          f"{RECEIPT.relative_to(ROOT)}")
    for v in result["variants"]:
        print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.4f}% changed, "
              f"sha256={v['sha256'][:12]}..., E_sum={v['removal_statistics']['exclusive_credit_sum']:.0f}, "
              f"pred={v['point_prediction_dti']:+.4f}")
    cmp_ = result["ranking"]["matched_count_comparison_at_40pct"]
    print(f"  matched count at 40%: shadow E={cmp_['shadow_exclusive_credit_sum']:.0f}, "
          f"random E={cmp_['random_exclusive_credit_sum']:.0f} "
          f"({cmp_['random_excess_fraction_vs_shadow']:+.1%}), "
          f"FIFO E={cmp_['fifo_exclusive_credit_sum']:.0f} "
          f"({cmp_['fifo_excess_fraction_vs_shadow']:+.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
