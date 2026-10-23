#!/usr/bin/env python3
"""Build three strike-aware PRUNE variants of R0 (anisotropic catalogue collar).

Parent: `h33-h33-2-b2` (R0), 37,654 unit-mass dots, >2 px Euclidean from the catalogue.
Axis: PRUNE. Value family: collar across-strike radius A in {4, 5, 6} px with the parent's
own 2 px radius kept along strike. Each variant

  1. removes every R0 dot inside the strike-aligned collar (along/2)^2 + (across/A)^2 <= 1,
  2. refills the exact same number of dots from the pinned H19-5 support, outside the
     collar, using the deterministically recovered FIFO-BFS thinning order,
  3. is re-read from disk and checked against the format gate before it is recorded.

Local TIFFs go to ignored `releases/`; competition rasters are never added to Git.

Run:  .venv/bin/python scripts/build_aniso_prune_variants.py --build [--canary]
Check: .venv/bin/python scripts/build_aniso_prune_variants.py --verify
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_r0_variants as R0  # noqa: E402  (pinned input verification + exact parent rebuild)
from aniso_prune import (  # noqa: E402
    build_strike_field,
    collar_membership,
    isotropic_membership,
    parent_diff_stats,
    refill_mask,
)
from src.validate import validate as format_gate  # noqa: E402

DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "PRUNE"
DATE = "20261023"
ALONG_PX = 2.0
ACROSS_PX = (4.0, 5.0, 6.0)
R0_DOTS = R0.R0_DOTS
LEDGER = ROOT / "ledger" / "submissions.csv"
RECEIPT = ROOT / "evidence" / "build_aniso_receipt.json"
LEDGER_FIELDS = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
                 "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
                 "receipt_score", "predicted_change", "date", "form_note", "notes"]

PREDICTIONS = {
    4.0: ("+0.003", "+0.003 DTI (MODEL; plausible -0.010 to +0.010; not a score)"),
    5.0: ("+0.002", "+0.002 DTI (MODEL; plausible -0.010 to +0.010; not a score)"),
    6.0: ("+0.000", "+0.000 DTI (MODEL; plausible -0.010 to +0.010; not a score)"),
}

DECOMPOSITION = {
    4.0: "collar term +0.004 to +0.006 (2632 dots at median 2.8 px across strike removed), "
         "refill dilution -0.001 to -0.003 (2632 dots added a median 1.0 px from a retained dot), "
         "net +0.003",
    5.0: "collar term +0.005 to +0.007 (3663 removed, median 3.0 px across strike), "
         "refill dilution -0.002 to -0.004 (3663 added a median 1.0 px from a retained dot), "
         "net +0.002",
    6.0: "collar term +0.006 to +0.008 (4625 removed, median 3.2 px across strike), "
         "refill dilution -0.003 to -0.005, plus first-order loss of genuine adjacent truth; "
         "net +0.000",
}

CONFOUNDER = (
    "A dot a few pixels across strike from a mapped trace may be a real parallel strand, a "
    "step-over, or the surface expression of a steeply dipping strand whose surface trace is "
    "offset from the mapped line; the refill pixels are H19-5 thinning-order picks, which are "
    "lithologic contacts or drainage lineaments as often as faults."
)
MECHANISM = (
    "Known catalogue pixels are masked pixel-exactly while new-fault truth can sit within 300 m "
    "of a known trace, so the collar trades false-positive mass against adjacent true credit. "
    "The parent's 2 px collar is direction-free: it removes flank mass and along-strike "
    "continuation alike. On a 400 m-spacing survey the positional error that matters is "
    "cross-strike, and along-strike continuation of a mapped trace is real (unmapped geometry of "
    "existing systems is explicitly scored). This family therefore widens the collar only across "
    "strike, holding the parent's 2 px radius along strike, at fixed dot count."
)
GEOLOGIST_NOTE = (
    "Read the removed set as two populations: flank dots at 2-3 px across strike from mapped "
    "traces (the predicted false mass) and along-strike continuations beyond mapped tips (which "
    "this edit deliberately keeps). Check whether the kept continuations look like real "
    "projections of the mapped geometry or like an artefact of the structure-tensor window."
)


def axis_value(across_px: float, along_px: float = ALONG_PX) -> str:
    return f"collar across<={across_px:g}px, along<={along_px:g}px (strike-aligned); fixed-count H19-5 refill"


def slug_for(across_px: float, along_px: float = ALONG_PX) -> str:
    a = f"{across_px:g}".replace(".", "p")
    l = f"{along_px:g}".replace(".", "p")
    return f"{PARENT}-PRUNEanisoA{a}L{l}-{DATE}"


def check_reservations() -> dict:
    """Fail closed if this (AXIS, value) family is already recorded locally or in a sibling ledger.

    The numeric-collision convention from ledger/experiment_reservations.json applies to
    *isotropic* single-radius cutoffs. No sibling ledger contains an anisotropic collar with
    along != across, so the pair (A, L=2) is new; the isotropic comparators are still recorded
    per variant so the human can see exactly what the anisotropy adds.
    """
    # Re-running this script reproduces its own rows (same slug, new sha8 is impossible because
    # emission is byte-deterministic); any *other* strike-aligned collar is a collision.
    own_slugs = {slug_for(across) for across in ACROSS_PX}
    hits = []
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                value = row.get("value") or ""
                if "along<=" not in value and "strike-aligned" not in value:
                    continue
                if (row.get("id") or "").rsplit("-", 1)[0] not in own_slugs:
                    hits.append(row.get("id"))
    if hits:
        raise ValueError(f"duplicate (AXIS,value) reservation already in ledger: {hits}")
    return {"checked_local_ledger": str(LEDGER.relative_to(ROOT)),
            "anisotropic_pairs_found": 0,
            "collision_convention": "numeric-collision rule applies to isotropic radii only; see ledger/experiment_reservations.json"}


def canary(max_samples: int = 250_000, seed: int = 20261023) -> dict:
    """REPORT-ONLY single-feature leakage canary (never a gate, never a score).

    All known catalogue positives plus a seeded sample of off-catalogue footprint pixels.
    A single feature with symmetric AUC > 0.90 would mean stop and investigate.
    """
    with rasterio.open(DATA / "sample_submission.tif") as src:
        foot = np.isfinite(src.read(1))
    with rasterio.open(DATA / "existing_faults.tif") as src:
        cat = (src.read(1) > 0) & foot
    rng = np.random.default_rng(seed)
    off = np.flatnonzero(foot.ravel() & ~cat.ravel())
    take = rng.choice(off, size=min(max_samples, off.size), replace=False)
    pos_rows, pos_cols = np.nonzero(cat)
    sample = np.concatenate([np.flatnonzero(cat.ravel()), take])
    y = np.zeros(sample.size, dtype=bool)
    y[:pos_rows.size] = True
    results = []
    with rasterio.open(DATA / "training_features.tif") as src:
        for band in range(1, src.count + 1):
            a = src.read(band).astype(np.float64).ravel()[sample]
            finite = np.isfinite(a) & (a > -1e30)
            if finite.sum() < 1000 or y[finite].sum() < 100 or (~y[finite]).sum() < 100:
                results.append({"band": band, "note": "insufficient finite samples"})
                continue
            rank = np.argsort(np.argsort(a[finite], kind="stable"), kind="stable")
            n1, n0 = int(y[finite].sum()), int((~y[finite]).sum())
            u = float(rank[y[finite]].sum()) - n1 * (n1 - 1) / 2.0
            auc = u / (n1 * n0)
            results.append({"band": band, "auc": round(auc, 4), "symmetric_auc": round(max(auc, 1 - auc), 4)})
    scored = [r for r in results if "symmetric_auc" in r]
    best = max(scored, key=lambda r: r["symmetric_auc"]) if scored else None
    return {
        "status": "REPORT ONLY",
        "seed": seed,
        "n_positive": int(pos_rows.size),
        "n_negative_sampled": int(take.size),
        "features_tested": len(scored),
        "sentinel_handling": "non-finite and <= -1e30 masked out per band before ranking",
        "max_symmetric_auc": best["symmetric_auc"] if best else None,
        "max_feature_band": best["band"] if best else None,
        "auc_gt_0_90": bool(best and best["symmetric_auc"] > 0.90),
        "per_band": results,
        "note": "Single-feature separability on the known catalogue only; no live-score inference.",
    }


def refill_diagnostics(kept: np.ndarray, refill: np.ndarray, field) -> dict:
    """Quantify the inherited refill policy's confound.

    The H19-5 support is the *unthinned* source field, so pixels the parent lineage dropped
    during 2.8 px thinning are by construction within 2.8 px of a dot it kept. Refilling with
    them adds mass that covers little new ground: the 0.2*(S-M) penalty term grows while T
    barely moves. Reporting it keeps the collar effect from being read as a refill effect.
    """
    rr, rc = np.nonzero(refill)
    if rr.size == 0:
        return {"n_refill": 0}
    d_kept = ndi.distance_transform_edt(~kept)
    to_kept = d_kept[rr, rc]
    return {
        "n_refill": int(rr.size),
        "refill_dist_to_nearest_retained_median_px": float(np.median(to_kept)),
        "refill_dist_to_nearest_retained_max_px": float(to_kept.max()),
        "refill_within_3px_of_retained_pct": 100.0 * float((to_kept <= 3.0).mean()),
        "refill_within_kernel_of_retained_pct": 100.0 * float((to_kept <= 3.0).mean()),
        "min_catalogue_distance_of_final_set_px": float(field.dist[np.nonzero(kept | refill)].min()),
        "interpretation": (
            "High 'within 3 px of retained' means refills are largely redundant mass (penalty, "
            "little fresh kernel credit). It is a property of the inherited refill policy, not of "
            "the collar geometry under test; there is no live score behind it."
        ),
    }


def emit_pair(mask: np.ndarray, foot: np.ndarray, template: dict, base: str) -> tuple[Path, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    nan_tmp = OUT / f".{base}-nan.tmp.tif"
    zeros_tmp = OUT / f".{base}-zeros.tmp.tif"
    R0.emit(mask, foot, template, base, "nan", nan_tmp)
    R0.emit(mask, foot, template, base, "zeros", zeros_tmp)
    sha8 = R0.sha256_file(nan_tmp)[:8]
    nan_path = OUT / f"{base}-{sha8}.tif"
    zeros_path = OUT / f"{base}-{sha8}-zeros.tif"
    nan_tmp.replace(nan_path)
    zeros_tmp.replace(zeros_path)
    return nan_path, zeros_path


def audit_file(path: Path, expected: np.ndarray, foot: np.ndarray, cat: np.ndarray,
               template: dict, mode: str, collar: np.ndarray) -> dict:
    """Re-read from disk, then apply the format gate plus this experiment's own rules."""
    gate = format_gate(str(path), str(DATA / "sample_submission.tif"),
                       str(DATA / "existing_faults.tif"), zeros_outside=(mode == "zeros"))
    with rasterio.open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs, transform = src.crs, src.transform
    mask_on_disk = (a > 0.5) & foot
    checks = {
        "format_gate_pass": bool(gate["pass"]),
        "crs_matches_sample": crs == template["crs"],
        "transform_matches_sample": transform == template["transform"],
        "shape_matches_sample": a.shape == (template["height"], template["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(a[foot]).all()),
        "inside_foot_range_0_1": bool(np.all((a[foot] >= 0) & (a[foot] <= 1))),
        "outside_nan" if mode == "nan" else "outside_zeros": (
            bool(np.isnan(a[~foot]).all()) if mode == "nan" else bool(np.all(a[~foot] == 0))),
        "mask_matches_expected_after_disk_read": bool(np.array_equal(mask_on_disk, expected)),
        "zero_catalogue_mass": bool(gate["catalogue_mass"] == 0.0),
        "no_dot_inside_collar": bool(not np.any(mask_on_disk & collar)),
        "count_held": int(mask_on_disk.sum()) == R0_DOTS,
    }
    if not all(checks.values()):
        raise ValueError(f"audit failed for {path.name}: {[k for k, v in checks.items() if not v]} {gate['fails']}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": R0.sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(mask_on_disk.sum()),
        "checks": checks,
        "format_gate": gate,
    }


def build(with_canary: bool = False) -> dict:
    t0 = time.time()
    reservation = check_reservations()
    manifest = R0.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = R0.exact_parent_rebuild()

    field = build_strike_field(cat)
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    rank = R0.fifo_bfs_visit_rank(h19)
    if np.any(rank[h19] < 0) or np.any(rank[~h19] != -1):
        raise RuntimeError("FIFO-BFS ranking does not cover the H19-5 support exactly")

    own_ids = {slug_for(across) for across in ACROSS_PX}
    foreign_sha: set[str] = set()
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("id") or "").rsplit("-", 1)[0] in own_ids:
                    continue  # this script's own previous build; byte-identical re-emit is expected
                for key in ("sha256", "sha256_zeros"):
                    if row.get(key):
                        foreign_sha.add(row[key])
    ledger = LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else ""
    variants = []
    for across in ACROSS_PX:
        inside, diag = collar_membership(*np.nonzero(r0), field, across, ALONG_PX)
        collar = np.zeros_like(r0)
        collar[np.nonzero(r0)[0][inside], np.nonzero(r0)[1][inside]] = True
        kept = r0 & ~collar
        n_refill = int(collar.sum())
        if n_refill == 0:
            raise ValueError(f"A={across}: collar removes no parent dots")

        # Refill pool: the parent lineage's own H19-5 support, outside the collar, not a
        # catalogue pixel, not already kept. Only pixels within A of the catalogue can lie
        # inside the collar, so membership is evaluated on that subset and removed.
        pool = foot & h19 & ~cat & ~kept
        near = np.nonzero(pool & (field.dist <= across + 1e-9))
        inside_pool, _ = collar_membership(near[0], near[1], field, across, ALONG_PX)
        pool[near[0][inside_pool], near[1][inside_pool]] = False
        if int(pool.sum()) < n_refill:
            raise ValueError(f"A={across}: refill pool {int(pool.sum())} < {n_refill}")
        refill = refill_mask(pool, rank, n_refill)
        candidate = kept | refill
        if int(candidate.sum()) != R0_DOTS:
            raise AssertionError("fixed-count refill did not hold the parent dot count")
        if np.any(candidate & cat):
            raise AssertionError("refill produced catalogue mass")

        diff = parent_diff_stats(r0, candidate, field)
        diag_refill = refill_diagnostics(kept, refill, field)
        if not 1.0 <= diff["pct_changed_of_parent"] <= 50.0:
            raise ValueError(f"A={across}: changes {diff['pct_changed_of_parent']:.3f}% of R0 (need 1-50%)")

        # Isotropic comparator counts: what the same across-radius would remove with no
        # along-strike exemption, and what the parent's 2 px rule removes.
        iso = np.zeros_like(r0)
        iso_dots = isotropic_membership(*np.nonzero(r0), field, across)
        iso[np.nonzero(r0)[0][iso_dots], np.nonzero(r0)[1][iso_dots]] = True
        base = slug_for(across)
        nan_path, zeros_path = emit_pair(candidate, foot, template, base)
        nan_audit = audit_file(nan_path, candidate, foot, cat, template, "nan", collar)
        zeros_audit = audit_file(zeros_path, candidate, foot, cat, template, "zeros", collar)
        for audit in (nan_audit, zeros_audit):
            if audit["sha256"] in foreign_sha:
                raise ValueError(f"sha256 already present in ledger for another file: {audit['sha256']}")

        short, full = PREDICTIONS[across]
        note = (f"{PARENT}; PRUNE strike-aligned collar across<={across:g}px along<={ALONG_PX:g}px, "
                f"fixed-count refill; predicted {short} DTI MODEL")
        if len(note) > 140:
            raise AssertionError(f"form note is {len(note)} characters")
        card = {
            "hypothesis": (
                f"R0's isotropic 2 px collar removes across-strike flank mass and along-strike "
                f"continuation with equal force. Widening the collar to {across:g} px across strike only, "
                "at fixed dot count, should raise DTI if near-catalogue flank dots are predominantly "
                "false mass while along-strike continuations are predominantly real unmapped geometry."
            ),
            "mechanism": MECHANISM,
            "non_fault_confounder": CONFOUNDER,
            "predicted_live_change": full,
            "prediction_decomposition": DECOMPOSITION[across],
            "refill_confound": (
                f"{diag_refill['refill_within_3px_of_retained_pct']:.1f}% of the "
                f"{diag_refill['n_refill']} refill dots sit within 3 px of a retained dot "
                f"(median {diag_refill['refill_dist_to_nearest_retained_median_px']:.2f} px), so the "
                "fixed-count refill adds mostly penalty, little fresh kernel credit. The removed "
                "dots are non-local replacements (median displaced "
                f"{diff['removed_to_nearest_added_median_px']:.0f} px). Both terms are inherited "
                "from the parent lineage's refill policy, not from the collar geometry under test."
            ),
            "falsifier": (
                "A paired, same-week live receipt against R0 with delta <= -0.010 falsifies the "
                "across-strike-only collar at this dose; any |delta| < 0.010 is no evidence under the "
                "session rule. A monotone decline across A = 4, 5, 6 would additionally reject the "
                "dose-response implied by the mechanism."
            ),
            "structural_geologist_note": GEOLOGIST_NOTE,
            "information_value": (
                "Separates 'wider collar pays' from 'along-strike collateral costs' only together with "
                "the isotropic rungs; on its own it says whether the across-strike-only collar moves "
                "the live score at all."
            ),
        }
        variants.append({
            "id": nan_path.name[:-4],
            "parent": PARENT,
            "axis": AXIS,
            "value": axis_value(across),
            "across_px": across,
            "along_px": ALONG_PX,
            "n_dots": R0_DOTS,
            "pct_changed": diff["pct_changed_of_parent"],
            "status": "BUILT",
            "predicted_change": full,
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": diff,
            "collar_diagnostics": diag,
            "isotropic_comparator": {
                "radius_px": across,
                "parent_dots_inside_isotropic_radius": int(iso.sum()),
                "along_strike_dots_preserved_vs_isotropic": int(iso.sum() - collar.sum()),
                "note": "Isotropic count is the comparator; it is not an edit applied to any file.",
            },
            "refill_diagnostics": diag_refill,
            "refill": {
                "n_refill": n_refill,
                "pool_size": int(pool.sum()),
                "pool_rule": "H19-5 support, footprint, not catalogue, outside the collar, not already kept",
                "ordering": "recovered FIFO-BFS thinning visit rank (deterministic tie-break, not a probability)",
            },
            "mechanism_card": card,
        })

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": R0.git_sha(),
        "axis": AXIS,
        "value_family": "strike-aligned (anisotropic) collar: along held at the parent's 2 px, across = A",
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": R0.R0_ZEROS_SHA,
            "nan_sha256": R0.R0_NAN_SHA,
            **parent_stats,
        },
        "manifest": {"manifest_path": "registry/data_manifest.json",
                     "verified_count": len(manifest), "all_pins_rechecked": True},
        "strike_field": {
            "method": "structure tensor of the catalogue binary mask (smooth sigma 1.0, tensor sigma 3.0)",
            "along_strike": "(cos theta, -sin theta) in (row, col)",
            "coherence_rule": "pixels below coherence 0.3 at their nearest catalogue pixel get no along-strike exemption",
        },
        "reservation": reservation,
        "proxy_reports": {
            "leakage_canary": canary() if with_canary else {
                "status": "REPORT ONLY", "run_this_session": False,
                "reason": "re-run requested only with --canary; prior session value 0.5700 kept in ledger"},
            "catalogue_hide_recover": {
                "status": "NOT RUN",
                "reason": "no fold-clean instrument calibrated for a collar-geometry comparison; never a gate or score"},
            "sgmc_control": {"status": "NOT RUN", "reason": "not a calibrated control for this collar geometry"},
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
        "agent_never_submits": True,
    }
    return result


def write_outputs(result: dict) -> None:
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    rows = list(csv.DictReader(LEDGER.open(newline="", encoding="utf-8"))) if LEDGER.exists() else []
    new_ids = {v["id"] for v in result["variants"]}
    rows = [r for r in rows if r.get("id") not in new_ids]
    for v in result["variants"]:
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": v["n_dots"], "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["files"]["nan"]["sha256"], "sha256_zeros": v["files"]["zeros"]["sha256"],
            "parent": v["parent"], "axis": v["axis"], "value": v["value"], "status": "BUILT",
            "receipt": "N", "receipt_score": "",
            "predicted_change": v["predicted_change"], "date": "", "form_note": v["form_note"],
            "notes": "receipt_score/date to be filled by human; agent never submits",
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    cards_path = ROOT / "ledger" / "mechanism_cards.json"
    cards = json.loads(cards_path.read_text()) if cards_path.exists() else {"variants": []}
    cards["variants"] = [c for c in cards.get("variants", []) if c.get("id") not in new_ids]
    cards["variants"] += [{"id": v["id"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
                          for v in result["variants"]]
    cards["aniso_prune"] = {"schema_version": 1, "parent": PARENT, "axis": AXIS,
                            "value_family": result["value_family"],
                            "variants": [v["id"] for v in result["variants"]]}
    cards_path.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def verify() -> int:
    receipt = json.loads(RECEIPT.read_text())
    R0.verify_manifest_inputs()
    template, foot, cat, r0, _stats = R0.exact_parent_rebuild()
    field = build_strike_field(cat)
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    rank = R0.fifo_bfs_visit_rank(h19)
    problems = []
    for v in receipt["variants"]:
        across = float(v["across_px"])
        rows, cols = np.nonzero(r0)
        inside, _ = collar_membership(rows, cols, field, across, float(v["along_px"]))
        collar = np.zeros_like(r0)
        collar[rows[inside], cols[inside]] = True
        kept = r0 & ~collar
        n_refill = int(collar.sum())
        pool = foot & h19 & ~cat & ~kept
        near = np.nonzero(pool & (field.dist <= across + 1e-9))
        inside_pool, _ = collar_membership(near[0], near[1], field, across, float(v["along_px"]))
        pool[near[0][inside_pool], near[1][inside_pool]] = False
        expected = kept | refill_mask(pool, rank, n_refill)
        for mode in ("nan", "zeros"):
            audit = audit_file(ROOT / v["files"][mode]["path"], expected, foot, cat, template, mode, collar)
            if audit["sha256"] != v["files"][mode]["sha256"]:
                problems.append(f"{v['id']} {mode}: re-read sha mismatch")
            tmp = ROOT / ".cache" / "verify_aniso"
            tmp.mkdir(parents=True, exist_ok=True)
            probe = tmp / f"{v['id']}-{mode}.tif"
            try:
                R0.emit(expected, foot, template, v["id"], mode, probe)
                if R0.sha256_file(probe) != audit["sha256"]:
                    problems.append(f"{v['id']} {mode}: byte-for-byte re-emit mismatch")
            finally:
                probe.unlink(missing_ok=True)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"Verified {len(receipt['variants'])} variant pairs from disk; bytes reproduce exactly.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true")
    group.add_argument("--verify", action="store_true")
    ap.add_argument("--canary", action="store_true", help="re-run the report-only leakage canary")
    args = ap.parse_args()
    if args.verify:
        return verify()
    result = build(with_canary=args.canary)
    write_outputs(result)
    print(f"Built {len(result['variants'])} strike-aligned PRUNE variants; receipt -> {RECEIPT.relative_to(ROOT)}")
    for v in result["variants"]:
        print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.2f}% changed, "
              f"sha256={v['files']['nan']['sha256'][:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
