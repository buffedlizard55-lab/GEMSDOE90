#!/usr/bin/env python3
"""Build three controlled AXIS=SPACING variants from byte-identical R0.

Session selection (agent-chosen, per brief: do not prompt over the axis):
SPACING -- local kernel-scale respacing at fixed count. The brief's global
arrangements (lattice / Poisson-disk / along-strike) are already built by
sibling sessions (GEMSDOE86/88/91, audited read-only via `gh api`), so this
session tests the unbuilt arrangement question: move the most kernel-crowded
5/10/15% of R0's dots to the best uncovered pixel of the same H19-5 support
within 15 px (expanding 30/60 px only when a window is empty), at the
parent's own 2.8 px minimum separation and >= 3 px from the catalogue.
Count (37,654), support, block geography and mass are held exactly; only
arrangement changes. Untouched R0 dots keep the parent's 2.236 px floor
(no-new-mass convention, IR90-07/18/31/33).

Measured before building (byte-identical R0): support-credit balance of the
respacing is -87 / -284 / -496 credit units at 5/10/15% -- replacements gain
slightly less on the H19-5 proxy than crowded dots lose, the same
credit-uniformity headwind as IR90-25. Predictions are therefore centred at
~-0.001..-0.003 (MODEL), frozen below before any PROXY is computed.

This script never contacts DrivenData or Dropbox, never reads a leaderboard,
never logs in and never submits. Competition rasters stay in ignored
`.cache/gems_data/`; generated rasters in ignored `releases/`.

Run build:  `.venv/bin/python scripts/build_spacing_variants.py --build`
Run verify: `.venv/bin/python scripts/build_spacing_variants.py --verify`
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_r0_variants as base_build  # noqa: E402
import build_relief_variants as relief_build  # noqa: E402  report-only proxy helpers
from src import spacing as spacing_core  # noqa: E402
from src.concentration import density_cv  # noqa: E402
from src.reach import credit_map  # noqa: E402
from src.validate import validate as format_validate  # noqa: E402

DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "SPACING"
DATE = "20261024"
SEED = 20261024
R0_DOTS = 37_654
CLAIMED_PARENT_DTI = 0.2778  # CLAIM (owner-reported, no receipt); prediction anchor only
DISCOUNT = 1.0  # no discount: measured support balance is already net-negative (see prediction_model)
SGMC_PATH = DATA / "external" / "derived_sgmc_faults_100m_u8.tif"
RECEIPT_PATH = ROOT / "evidence" / "spacing_build_receipt.json"
RESERVATIONS_PATH = ROOT / "ledger" / "experiment_reservations.json"
LEDGER_PATH = ROOT / "ledger" / "submissions.csv"
CARDS_PATH = ROOT / "ledger" / "mechanism_cards.json"

# Cross-session audit performed read-only via `gh api` on 2026-10-24 of
# ledger/submissions.csv on the default branches of the sibling repositories
# that carry one (GEMSDOE84-88, 91, 92 checked; SPACING rows found in 86/88/91).
CROSS_REPO_SPACING_VALUES = (
    "lattice", "poisson-disk", "along-strike",           # GEMSDOE86, parent R0
    "pdiskc16", "latticec16", "strikec16", "randomc16",  # GEMSDOE86, parent R0
    "poisson28", "lattice4px", "strike",                 # GEMSDOE88, parent PRUNEp3
    "spread40", "clump40", "jitter40",                   # GEMSDOE91 ring-2 (2.0-2.24 px), parent R0
)

VARIANT_SPECS = (
    {"tag": "resp5pct", "file_value": "resp5pctW15", "n_move": 1_883, "dose_pct": 5.0},
    {"tag": "resp10pct", "file_value": "resp10pctW15", "n_move": 3_765, "dose_pct": 10.0},
    {"tag": "resp15pct", "file_value": "resp15pctW15", "n_move": 5_648, "dose_pct": 15.0},
)


def existing_ledger_hashes(exclude_ids: set[str] | None = None) -> set[str]:
    hashes: set[str] = set()
    exclude_ids = exclude_ids or set()
    if LEDGER_PATH.is_file():
        with LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("id") in exclude_ids:
                    continue
                for col in ("sha256", "sha256_zeros"):
                    val = (row.get(col) or "").strip()
                    if val:
                        hashes.add(val)
    return hashes


def check_spacing_reservations() -> None:
    """Fail closed on any (AXIS, value) reuse, ours or a sibling's (brief s1/s6)."""
    ours = {s["file_value"] for s in VARIANT_SPECS}
    if ours & set(CROSS_REPO_SPACING_VALUES):
        raise ValueError(f"spacing value collides with sibling session: {ours & set(CROSS_REPO_SPACING_VALUES)}")
    if LEDGER_PATH.is_file():
        with LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                val = (row.get("value") or "")
                for spec in VARIANT_SPECS:
                    if spec["tag"] in val and not (row.get("id") or "").startswith(f"{PARENT}-SPACING{spec['file_value']}-"):
                        raise ValueError(f"duplicate experiment reservation: (SPACING, {spec['tag']}) in {row.get('id')}")


def load_inputs() -> dict:
    input_receipt = base_build.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    if parent_stats["r0_rebuilt_zeros_sha256"] != base_build.R0_ZEROS_SHA:
        raise ValueError("R0 rebuild is not the recorded parent")
    if parent_stats["r0_rebuilt_nan_sha256"] != base_build.R0_NAN_SHA:
        raise ValueError("R0 NaN rebuild is not the recorded parent")
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    pool = support & ~r0 & (dist_cat >= 3.0)
    return {
        "input_receipt": input_receipt, "template": template, "foot": foot,
        "cat": cat, "r0": r0, "parent_stats": parent_stats,
        "dist_cat": dist_cat, "support": support, "pool": pool,
    }


def build_masks(inp: dict) -> dict:
    r0, pool = inp["r0"], inp["pool"]
    pts = np.column_stack(np.nonzero(r0)).astype(float)
    crowd = spacing_core.crowding_scores(pts)
    order = spacing_core.removal_order(pts, crowd)
    out = spacing_core.relocate(r0, pool, pts[order], doses=tuple(s["n_move"] for s in VARIANT_SPECS))
    return {"pts": pts, "crowd": crowd, "order": order, **out}


def prediction_model(delta_credit: float, support_px: int, credit0: float) -> dict:
    """First-order DTI projection from the exact support-credit balance.

    Truth is modelled as a uniform random subset of the H19-5 support of
    |G| pixels, so E[Delta T] = delta_credit * |G| / support_px. S is fixed
    (count held) and M is held at its parent value (replacements sit on the
    same support, so their nearest-truth credit distribution is assumed
    unchanged); the (S-M) term is calibrated so the parent reproduces its
    CLAIM 0.2778. No optimism discount is applied (DISCOUNT=1.0): the q50
    infill discount exists to deflate *positive* proxy gains sitting in the
    support's least-confident stretches, but here the exact balance is
    already net-negative at every dose, so the raw centre is adopted and
    the interval carries the uncertainty. MODEL, never a score.
    """
    by_g = {}
    for g in (20_000, 55_000, 100_000):
        t0 = g * credit0 / support_px
        d0 = t0 / CLAIMED_PARENT_DTI
        sm_term = (d0 - 0.2 * t0 - 0.8 * g) / 0.2
        t1 = t0 + delta_credit * g / support_px
        dti1 = t1 / (0.2 * t1 + 0.2 * sm_term + 0.8 * g)
        by_g[str(g)] = round(float(dti1 - CLAIMED_PARENT_DTI), 6)
    adopted = round(DISCOUNT * by_g["55000"], 3)
    lo = round(min(by_g.values()) - 0.008, 3)
    hi = round(max(by_g.values()) + 0.008, 3)
    return {"model_delta_by_truth_px": by_g, "discount": DISCOUNT,
            "adopted": adopted, "plausible_lo": lo, "plausible_hi": hi}


def block_report(r0: np.ndarray, cand: np.ndarray, foot: np.ndarray, block_px: int = 50) -> dict:
    """5 km block geography guard (Hard Constraint #5): nothing emptied,
    no block's dot count more than halved or doubled by a local respacing."""
    from src.mass_add import block_counts
    before = block_counts(r0, block_px)
    after = block_counts(cand, block_px)
    changed = after - before
    emptied = int(((before > 0) & (after == 0)).sum())
    worst_loss = float((changed[before > 0] / np.maximum(before[before > 0], 1)).min())
    return {
        "block_px": block_px,
        "cv_before": round(float(density_cv(r0, foot, block_px=block_px)), 6),
        "cv_after": round(float(density_cv(cand, foot, block_px=block_px)), 6),
        "max_block_gain": int(changed.max()), "max_block_loss": int(changed.min()),
        "worst_block_loss_frac": round(worst_loss, 6),
        "emptied_blocks": emptied,
        "pass": bool(emptied == 0 and worst_loss >= -0.5),
    }


def validate_spacing_file(path, expected_mask, inp, moves_for_mask, sample_profile, mode) -> dict:
    audit = relief_build.validate_relief_file(
        path, expected_mask, inp["r0"], inp["foot"], inp["cat"], inp["dist_cat"],
        DATA / base_build.PIN_PATHS["sample_submission"],
        DATA / base_build.PIN_PATHS["catalogue"], sample_profile, mode)
    with rasterio.open(path) as src:
        a = src.read(1)
    disk_mask = (a > 0.5) & inp["foot"]
    added = disk_mask & ~inp["r0"]
    ay, ax = np.nonzero(added)
    ry, rx = np.nonzero(inp["r0"] & ~disk_mask)
    # Added dots must honour the 2.8 px spacing against retained dots and
    # each other (retained-retained pairs inherit R0's own 2.828 px floor).
    tree = cKDTree(np.column_stack(np.nonzero(disk_mask & ~added)).astype(float))
    d_ret, _ = tree.query(np.column_stack([ay, ax]).astype(float), k=1)
    if len(ay) > 1:
        d_add, _ = cKDTree(np.column_stack([ay, ax]).astype(float)).query(
            np.column_stack([ay, ax]).astype(float), k=2)
        min_add_add = float(d_add[:, 1].min())
    else:
        min_add_add = float("inf")
    extra = {
        "src_validate_gate_pass": bool(audit["checks"]["src_validate_gate_pass"]),
        "added_min_dist_to_retained_px": round(float(d_ret.min()), 6),
        "added_min_dist_to_added_px": round(min_add_add, 6),
        "spacing_floor_honoured": bool(float(d_ret.min()) >= spacing_core.MIN_SEP_PX - 1e-9
                                       and min_add_add >= spacing_core.MIN_SEP_PX - 1e-9),
        "all_added_on_h19_support": bool(np.all(inp["support"][added])),
        "n_removed_equals_n_added": bool(len(ry) == len(ay)),
        "format_gate_revalidated_from_disk": bool(format_validate(
            str(path), str(DATA / base_build.PIN_PATHS["sample_submission"]),
            str(DATA / base_build.PIN_PATHS["catalogue"]), zeros_outside=(mode == "zeros"))["pass"]),
    }
    if not (extra["spacing_floor_honoured"] and extra["all_added_on_h19_support"]
            and extra["n_removed_equals_n_added"] and extra["format_gate_revalidated_from_disk"]):
        raise ValueError(f"spacing validator failed for {path.name}: {extra}")
    audit["checks"].update(extra)
    audit["added_dots"] = int(added.sum())
    audit["removed_dots"] = int((inp["r0"] & ~disk_mask).sum())
    return audit


def emit_pair(mask, foot, template, slug):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp_nan = OUT / f".{slug}-nan.tmp.tif"
    tmp_zeros = OUT / f".{slug}-zeros.tmp.tif"
    base_build.emit(mask, foot, template, slug, "nan", tmp_nan)
    base_build.emit(mask, foot, template, slug, "zeros", tmp_zeros)
    nan_sha = base_build.sha256_file(tmp_nan)
    zeros_sha = base_build.sha256_file(tmp_zeros)
    base = OUT / f"{slug}-{nan_sha[:8]}"
    nan_path = base.with_suffix(".tif")
    zeros_path = OUT / f"{base.name}-zeros.tif"
    tmp_nan.replace(nan_path)
    tmp_zeros.replace(zeros_path)
    return nan_path, zeros_path, nan_sha, zeros_sha


def mechanism_card(spec: dict, stats: dict, pred: dict) -> dict:
    return {
        "id": stats["id"],
        "hypothesis": (
            f"Respacing the {spec['n_move']} most kernel-crowded R0 dots ({spec['dose_pct']:.0f}% of the "
            "field) onto uncovered stretches of the same corroborated ridge within 1.5 km extends "
            "along-strike coverage of line-like new faults, which the brief's algebra rewards (a dot "
            "pays more cheaply against line-like truth), without changing mass, count or geography."
        ),
        "mechanism": (
            "Under DTI = T/(0.2T + 0.2(S-M) + 0.8|G|) with T a max over dots inside the 300 m (3 px) "
            "triangular kernel, a dot whose disk is already covered by neighbours pays full mass for "
            "almost no credit. Crowding is measured exactly as summed kernel-disk overlap within 6 px; "
            "each crowded dot is moved to the eligible support pixel of maximum exact marginal kernel "
            "credit at >= 2.8 px (the parent's own thinning distance) from every remaining dot."
        ),
        "non_fault_mimic": (
            "Crowded dots may be real fault complexity -- intersecting or stepping-over splays (the "
            "Faulds-style zones where systems sit) genuinely pack dots into one kernel -- and uncovered "
            "support stretches may be cover/vegetation gaps, lithologic contacts or drainage lineaments "
            "in the H19-5 field rather than unmapped fault. Either mimic makes the move delete signal "
            "and add noise at the same time."
        ),
        "predicted_change": stats["predicted_change"],
        "predicted_sign_reason": (
            f"Exact H19-5 support-credit balance is {stats['support_credit']['delta']:+.1f} units "
            f"(removals lose {stats['support_credit']['removal_loss']:.1f}, replacements gain "
            f"{stats['support_credit']['replacement_gain']:.1f}): local replacements cannot reach the "
            "far uncovered support, so the proxy centre is flat-to-negative and the adopted MODEL is "
            f"{pred['adopted']:+.3f} with no optimism discount (the balance is already negative). "
            "Any |live delta| < 0.010 is "
            "no evidence by the session rule."
        ),
        "falsifier": (
            f"A paired same-week receipt at the 5% dose with delta <= -0.010 rejects local respacing; "
            "monotone worsening across 5/10/15% confirms crowded dots were carrying credit, not "
            "redundancy. A delta >= +0.010 at any dose falsifies the credit-uniformity headwind "
            "(IR90-25) for arrangement edits and reopens kernel-scale respacing."
        ),
    }


def build() -> dict:
    t0 = time.time()
    check_spacing_reservations()
    inp = load_inputs()
    foot, cat, r0 = inp["foot"], inp["cat"], inp["r0"]
    support = inp["support"]
    built = build_masks(inp)
    moves = built["moves"]
    credit0 = float(credit_map(r0)[support].sum())
    stats_r0 = spacing_core.spacing_stats(r0)

    # --- Predictions are computed and frozen here, before any PROXY. ---
    variants = []
    candidate_masks = {"R0": r0}
    for spec in VARIANT_SPECS:
        mask = built["snapshots"][spec["n_move"]]
        dose_moves = moves[: spec["n_move"]]
        removed_mask = np.zeros_like(r0)
        for (ry, rx), _, _ in dose_moves:
            removed_mask[ry, rx] = True
        credit_after = float(credit_map(mask)[support].sum())
        credit_removed_only = float(credit_map(r0 & ~removed_mask)[support].sum())
        delta_credit = credit_after - credit0
        pred = prediction_model(delta_credit, int(support.sum()), credit0)
        disp = np.array([float(np.hypot(ay - ry, ax - rx)) for (ry, rx), (ay, ax), _ in dose_moves])
        windows = {str(w): int(sum(1 for _, _, ww in dose_moves if ww == w))
                   for w in spacing_core.EXPANSIONS_PX}
        blocks = block_report(r0, mask, foot)
        if not blocks["pass"]:
            raise ValueError(f"region-evenness gate failed for {spec['tag']}: {blocks}")
        slug = f"{PARENT}-SPACING{spec['file_value']}-{DATE}"
        nan_path, zeros_path, nan_sha, zeros_sha = emit_pair(mask, foot, inp["template"], slug)
        vid = nan_path.stem
        pct_changed = 100.0 * float((mask ^ r0).sum()) / float(R0_DOTS)
        pred_str = (f"{pred['adopted']:+.3f} DTI (MODEL; plausible interval "
                    f"{pred['plausible_lo']:+.3f} to {pred['plausible_hi']:+.3f}; not a score)")
        v = {
            "id": vid, "tag": spec["tag"], "value": (
                f"tag={spec['tag']}; local kernel-scale respacing of {spec['n_move']} most crowded "
                f"R0 dots ({spec['dose_pct']:.1f}%); window 15px (expand 30/60); min-sep 2.8px; "
                "fixed count 37654; added d_cat>=3px"),
            "axis": AXIS, "parent": PARENT, "n_dots": int(mask.sum()),
            "n_relocated": spec["n_move"], "pct_changed": pct_changed,
            "sha256": nan_sha, "sha256_zeros": zeros_sha,
            "support_credit": {"parent": credit0, "after": credit_after,
                               "removal_loss": credit0 - credit_removed_only,
                               "replacement_gain": credit_after - credit_removed_only,
                               "delta": delta_credit},
            "prediction_model": pred, "predicted_change": pred_str,
            "pred_short": f"{pred['adopted']:+.3f}",
            "displacement_px": {"mean": round(float(disp.mean()), 3),
                                "median": round(float(np.median(disp)), 3),
                                "p95": round(float(np.percentile(disp, 95)), 3),
                                "max": round(float(disp.max()), 3)},
            "windows_used": windows,
            "spacing_before": stats_r0, "spacing_after": spacing_core.spacing_stats(mask),
            "block_geography_5km": blocks,
            "form_note": (f"h33-h33-2-b2; SPACING respace {spec['n_move']}d ({spec['dose_pct']:.0f}%) "
                          f"crowded->gap <1.5km, count fixed; pred {pred['adopted']:+.3f} DTI MODEL")[:140],
            "files": {},
        }
        for mode, path in (("nan", nan_path), ("zeros", zeros_path)):
            v["files"][mode] = validate_spacing_file(path, mask, inp, dose_moves, inp["template"], mode)
        v["mechanism_card"] = mechanism_card(spec, v, pred)
        variants.append(v)
        candidate_masks[spec["tag"]] = mask

    # --- Report-only diagnostics (never gates, never scores). Predictions
    # above were frozen before this block ran. ---
    crowd_map = np.zeros(r0.shape, dtype=np.float64)
    crowd_map[r0] = built["crowd"]
    canary = relief_build.compute_leakage_canary(foot, cat, crowd_map, seed=SEED)
    canary["features"]["crowding_score_at_dot_pixels"] = canary["features"].pop("composite_landform_relief_idx")
    if canary["max_feature"] == "composite_landform_relief_idx":
        canary["max_feature"] = "crowding_score_at_dot_pixels"
    canary["crowding_score_symmetric_auc"] = canary["features"]["crowding_score_at_dot_pixels"]["symmetric_auc"]
    with rasterio.open(SGMC_PATH) as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (inp["dist_cat"] > 3.0)
    hide = relief_build.compute_spatial_block_proxy(candidate_masks, foot, cat, holdout_quarter=True, seed=SEED)
    hide["caveat"] = ("Catalogue hide-and-recover on withheld 20 km blocks. The ledger shows this PROXY "
                      "correlates -0.87..+0.54 with live scores; REPORT ONLY, never a gate or score.")
    sgmc = relief_build.compute_spatial_block_proxy(candidate_masks, foot, sgmc_off, holdout_quarter=False, seed=SEED)
    sgmc["caveat"] = ("Off-catalogue USGS SGMC geologic-map faults; exposed-bedrock biased, not the hidden "
                      "new-fault labels. PROXY ONLY, never a gate or score.")

    other_hashes = existing_ledger_hashes(exclude_ids={v["id"] for v in variants})
    for v in variants:
        if v["sha256"] in other_hashes or v["sha256_zeros"] in other_hashes:
            raise ValueError(f"SHA-256 collides with a prior ledger entry: {v['id']}")

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": base_build.git_sha(),
        "generator_script_sha256": base_build.sha256_file(Path(__file__)),
        "session_branch": "arena/5d597521-gemsdoe90",
        "parent": PARENT, "axis": AXIS,
        "operator": ("crowding-ranked local respacing: remove most kernel-crowded dots "
                     "(summed triangular-disk overlap within 6 px), replace each at the max-marginal-"
                     "credit eligible H19-5 pixel within 15 px (expand 30/60), min-sep 2.8 px, "
                     "d_cat>=3 px; nested sequential doses 1883/3765/5648; count fixed at 37654"),
        "claimed_parent_dti_used_only_for_prediction": CLAIMED_PARENT_DTI,
        "claimed_parent_dti_evidence_class": "CLAIM (owner-reported, no receipt on file)",
        "pool_cells": int(inp["pool"].sum()), "support_px": int(support.sum()),
        "footprint_px": int(foot.sum()),
        "predictions_frozen_before_proxies": True,
        "parent_stats": inp["parent_stats"],
        "manifest": {"manifest_path": "registry/data_manifest.json",
                     "verified_count": len(inp["input_receipt"]), "all_pins_rechecked": True},
        "variants": variants,
        "proxy_reports": {"catalogue_hide_recover": hide, "leakage_canary": canary, "sgmc_control": sgmc},
        "elapsed_s": round(time.time() - t0, 2),
    }


def update_ledgers_and_reservations(result: dict) -> None:
    with LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    ids = {v["id"] for v in result["variants"]}
    rows = [r for r in rows if r.get("id") not in ids]
    for v in result["variants"]:
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": str(v["n_dots"]), "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"],
            "parent": v["parent"], "axis": v["axis"], "value": v["value"],
            "status": "BUILT", "receipt": "N", "receipt_score": "",
            "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": (f"relocated={v['n_relocated']} dots; mean displacement "
                      f"{v['displacement_px']['mean']}px; support-credit delta "
                      f"{v['support_credit']['delta']:+.1f}; region-evenness PASS; added d_cat>=3px; "
                      "receipt_score/date filled by human; agent never submits"),
        })
    with LEDGER_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    cards = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
    cards["spacing"] = {
        "schema_version": 1, "parent": PARENT, "axis": AXIS,
        "variants": [{"id": v["id"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
                     for v in result["variants"]],
    }
    CARDS_PATH.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")

    res = json.loads(RESERVATIONS_PATH.read_text(encoding="utf-8"))
    res["spacing_reservations_20261024"] = {
        "checked_utc": "2026-10-24", "axis": AXIS, "parent": PARENT,
        "scope": ("Read-only gh api audit of ledger/submissions.csv on default branches of "
                  "buffedlizard55-lab/GEMSDOE84-88, 91, 92 (2026-10-24)."),
        "cross_repo_occupied_values": list(CROSS_REPO_SPACING_VALUES),
        "selected_values": [v["tag"] for v in result["variants"]],
        "why_distinct": (
            "Sibling SPACING values are global arrangements (lattice/Poisson-disk/along-strike "
            "resampling of the whole field, ~37-40% changed) or ring-2 micro-moves at 2.0-2.24 px "
            "(spread40/clump40/jitter40). These values respace only the most kernel-crowded dots, "
            "each to the max-marginal-credit support pixel within 15 px at the parent's 2.8 px "
            "separation -- a local, dose-nested arrangement edit at 10/20/30% symmetric diff. "
            "No sibling ledger row uses a crowding rank, a 15 px window, or these tags."
        ),
        "caveat": ("Default-branch public audit is not proof of every private or unindexed entity "
                   "submission. Human must check any missing entity ledger before spending a slot."),
    }
    RESERVATIONS_PATH.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")


def verify_all() -> int:
    inp = load_inputs()
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    built = build_masks(inp)
    spec_by_tag = {s["tag"]: s for s in VARIANT_SPECS}
    our_ids = {v["id"] for v in receipt["variants"]}
    other_hashes = existing_ledger_hashes(exclude_ids=our_ids)
    tmp_dir = ROOT / ".cache" / "verify_spacing_bytes"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for v in receipt["variants"]:
        spec = spec_by_tag[v["tag"]]
        expected = built["snapshots"][spec["n_move"]]
        if int(expected.sum()) != R0_DOTS:
            raise ValueError(f"recomputed {v['id']} count != {R0_DOTS}")
        pct_changed = 100.0 * float((expected ^ inp["r0"]).sum()) / float(R0_DOTS)
        if abs(pct_changed - float(v["pct_changed"])) > 1e-6:
            raise ValueError(f"recomputed {v['id']} parent-diff mismatch")
        if not block_report(inp["r0"], expected, inp["foot"])["pass"]:
            raise ValueError(f"recomputed {v['id']} fails region-evenness gate")
        dose_moves = built["moves"][: spec["n_move"]]
        for mode_name in ("nan", "zeros"):
            fpath = ROOT / v["files"][mode_name]["path"]
            audit = validate_spacing_file(fpath, expected, inp, dose_moves, inp["template"], mode_name)
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"disk SHA-256 mismatch for {v['id']} [{mode_name}]")
            if audit["sha256"] in other_hashes:
                raise ValueError(f"SHA-256 collides with prior ledger entry: {v['id']} [{mode_name}]")
            tmp_file = tmp_dir / f"{v['id']}-{mode_name}.tif"
            try:
                base_build.emit(expected, inp["foot"], inp["template"], v["id"], mode_name, tmp_file)
                if base_build.sha256_file(tmp_file) != audit["sha256"]:
                    raise ValueError(f"deterministic byte re-emission failed for {v['id']} [{mode_name}]")
            finally:
                tmp_file.unlink(missing_ok=True)
    verified_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verified_utc"] = verified_utc
    receipt["verification_git_sha"] = base_build.git_sha()
    receipt["generator_script_sha256"] = base_build.sha256_file(Path(__file__))
    receipt["self_check"] = {
        "all_26_manifest_pins_verified": True,
        "r0_rebuilt_byte_identically": bool(inp["parent_stats"]["r0_byte_identity_passed"]),
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "region_evenness_gate_pass": True,
        "no_sha256_collision_with_other_ledger_rows": True,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} spacing pairs from disk; R0 rebuilt byte-identically")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.build:
        result = build()
        RECEIPT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        update_ledgers_and_reservations(result)
        print(f"Built {len(result['variants'])} SPACING variants from exact R0; receipt -> {RECEIPT_PATH.relative_to(ROOT)}")
        for v in result["variants"]:
            print(f"  {v['id']}: {v['n_dots']} dots, relocated {v['n_relocated']}, "
                  f"{v['pct_changed']:.3f}% diff, pred {v['pred_short']}")
        return 0
    return verify_all()


if __name__ == "__main__":
    sys.exit(main())
