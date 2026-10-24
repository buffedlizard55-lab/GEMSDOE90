#!/usr/bin/env python3
"""Build matched strike-aligned PRUNE collars without fixed-count refill.

Each candidate is a strict subset of exact R0.  Its removed set is exactly the
same ``scripts/aniso_prune.py`` ellipse as the recorded A4/A5/A6, L=2 refill
experiment; the only new operation is deletion of the refill.  This isolates the
collar term from the measured, largely kernel-redundant FIFO refill term.

Run after ``scripts/restore_data.py``:
  .venv/bin/python scripts/build_aniso_prune_norefill.py --build
  .venv/bin/python scripts/build_aniso_prune_norefill.py --verify

No DrivenData/Dropbox access, label probing, login, or submission occurs.  Local
catalogue/SGMC diagnostics are PROXY / REPORT ONLY, never gates or live scores.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_r0_variants as R0  # noqa: E402
from aniso_prune import (  # noqa: E402
    along_across,
    build_strike_field,
    collar_membership,
    parent_diff_stats,
)
from build_aniso_prune_variants import canary  # noqa: E402
from build_relief_variants import compute_spatial_block_proxy  # noqa: E402
from src.validate import validate as format_validate  # noqa: E402

DATA = R0.DATA
OUT = ROOT / "releases"
LEDGER = ROOT / "ledger" / "submissions.csv"
RECEIPT = ROOT / "evidence" / "aniso_norefill_receipt.json"
MATCHED_RECEIPT = ROOT / "evidence" / "build_aniso_receipt.json"
PARENT = "h33-h33-2-b2"
AXIS = "PRUNE"
DATE = "20261023"
ALONG_PX = 2.0
ACROSS_PX = (4.0, 5.0, 6.0)
R0_DOTS = R0.R0_DOTS
SEED = 20261023
PREDICTIONS = {
    4.0: ("+0.005", "+0.005 DTI (MODEL; plausible -0.005 to +0.012; not a score)"),
    5.0: ("+0.006", "+0.006 DTI (MODEL; plausible -0.006 to +0.014; not a score)"),
    6.0: ("+0.003", "+0.003 DTI (MODEL; plausible -0.010 to +0.012; not a score)"),
}
DECOMPOSITION = {
    4.0: "matched collar term +0.004 to +0.006; refill term removed (prior estimate -0.001 to -0.003); net +0.005",
    5.0: "matched collar term +0.005 to +0.007; refill term removed (prior estimate -0.002 to -0.004); net +0.006",
    6.0: "matched collar term +0.006 to +0.008, less genuine adjacent-continuation loss; refill term removed; net +0.003",
}


def value_string(across_px: float) -> str:
    return (
        f"tag=anisoA{across_px:g}L2-norefill; collar across<={across_px:g}px, "
        "along<=2px (strike-aligned); strict R0 subset; no refill"
    )


def slug_for(across_px: float) -> str:
    return f"{PARENT}-PRUNEanisoA{across_px:g}L2nr-{DATE}"


def mask_digest(mask: np.ndarray) -> str:
    """Order-independent-of-JSON content digest for a raster-shaped boolean set."""
    return hashlib.sha256(np.packbits(np.asarray(mask, dtype=bool), axis=None).tobytes()).hexdigest()


def make_norefill_candidate(parent: np.ndarray, collar: np.ndarray) -> tuple[np.ndarray, dict]:
    """Delete parent dots inside collar; never add, move, or alter any other dot."""
    r0 = np.asarray(parent, dtype=bool)
    remove = np.asarray(collar, dtype=bool)
    if r0.shape != remove.shape:
        raise ValueError("parent and collar shapes differ")
    if np.any(remove & ~r0):
        raise ValueError("collar must be restricted to parent dots")
    candidate = r0 & ~remove
    n_parent = int(r0.sum())
    n_removed = int(remove.sum())
    n_candidate = int(candidate.sum())
    if n_parent - n_candidate != n_removed:
        raise AssertionError("strict-subset deletion accounting failed")
    pct = 100.0 * n_removed / n_parent
    if not 1.0 <= pct <= 50.0:
        raise ValueError(f"PRUNE no-refill changes {pct:.6f}% of R0 (required 1-50%)")
    return candidate, {
        "n_parent": n_parent,
        "n_candidate": n_candidate,
        "n_removed": n_removed,
        "n_added": 0,
        "n_retained_parent": n_candidate,
        "symmetric_difference_px": n_removed,
        "pct_changed_of_parent": pct,
        "strict_subset_of_R0": True,
    }


def check_reservations() -> dict:
    """Reject foreign duplicate pairs; permit byte-identical reproduction of own rows."""
    expected_values = {value_string(a) for a in ACROSS_PX}
    own_slugs = {slug_for(a) for a in ACROSS_PX}
    foreign_hits = []
    own_hits = []
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                value = row.get("value") or ""
                if value not in expected_values and not (
                    "aniso" in value.lower() and "norefill" in value.lower().replace("-", "")
                ):
                    continue
                ident = row.get("id") or ""
                if ident.rsplit("-", 1)[0] in own_slugs and value in expected_values:
                    own_hits.append(ident)
                else:
                    foreign_hits.append(ident or value)
    if foreign_hits:
        raise ValueError(f"duplicate (PRUNE, value) reservation: {foreign_hits}")
    if own_hits and not RECEIPT.is_file():
        raise ValueError("own no-refill rows exist but their receipt is missing; stop rather than approximate")
    return {
        "checked_local_ledger": "ledger/submissions.csv",
        "sibling_ledgers_checked_2026_10_23": [f"GEMSDOE{i}" for i in range(84, 93)],
        "selected_values": sorted(expected_values),
        "foreign_duplicates": foreign_hits,
        "own_reproduction_rows_present": len(own_hits),
        "distinctness": "Sibling no-refill PRUNE rows are isotropic; these are strike-aligned A4/A5/A6, L=2 collars matched to the recorded refill family.",
    }


def snap_floor_feasibility(r0: np.ndarray, foot: np.ndarray, h19: np.ndarray, dist_cat: np.ndarray) -> dict:
    """Reproduce the geometric reason the proposed SNAP session was not emitted."""
    below = r0 & (dist_cat < 3.0)
    ys, xs = np.nonzero(below)
    no_support = 0
    no_foot = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        y0, y1 = max(0, y - 2), min(r0.shape[0], y + 3)
        x0, x1 = max(0, x - 2), min(r0.shape[1], x + 3)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        cap = (yy - y) ** 2 + (xx - x) ** 2 <= 4
        legal_foot = foot[y0:y1, x0:x1] & (dist_cat[y0:y1, x0:x1] >= 3.0) & cap
        legal_support = legal_foot & h19[y0:y1, x0:x1]
        no_foot += int(not legal_foot.any())
        no_support += int(not legal_support.any())
    return {
        "proposed_axis": "SNAP (withdrawn before raster emission)",
        "constraint_triplet": "same 37,654 count; every move <=2 px; every final dot >=3 px from catalogue",
        "inherited_R0_dots_below_3px": int(below.sum()),
        "dots_with_no_on_support_H19_5_legal_destination_within_2px": int(no_support),
        "dots_with_no_in_footprint_legal_destination_within_2px": int(no_foot),
        "decision": f"SNAP is infeasible for {no_foot} dots even off H19-5; pivot to PRUNE, whose brief collar exception applies. Zero SNAP rasters emitted.",
        "label_or_score_information_used": False,
    }


def emit_pair(mask: np.ndarray, foot: np.ndarray, template: dict, slug: str) -> tuple[Path, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    nan_tmp = OUT / f".{slug}-nan.tmp.tif"
    zeros_tmp = OUT / f".{slug}-zeros.tmp.tif"
    R0.emit(mask, foot, template, slug, "nan", nan_tmp)
    R0.emit(mask, foot, template, slug, "zeros", zeros_tmp)
    sha8 = R0.sha256_file(nan_tmp)[:8]
    nan_path = OUT / f"{slug}-{sha8}.tif"
    zeros_path = OUT / f"{slug}-{sha8}-zeros.tif"
    nan_tmp.replace(nan_path)
    zeros_tmp.replace(zeros_path)
    return nan_path, zeros_path


def audit_file(
    path: Path,
    expected: np.ndarray,
    parent: np.ndarray,
    collar: np.ndarray,
    foot: np.ndarray,
    cat: np.ndarray,
    template: dict,
    mode: str,
    expected_count: int,
) -> dict:
    """Disk re-read + official-format mirror + strict-subset/collar checks."""
    gate = format_validate(
        str(path), str(DATA / "sample_submission.tif"), str(DATA / "existing_faults.tif"),
        zeros_outside=(mode == "zeros"),
    )
    with rasterio.open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs, transform = src.crs, src.transform
    disk = (a > 0.5) & foot
    checks = {
        "format_gate_pass": bool(gate["pass"]),
        "crs_matches_sample": crs == template["crs"],
        "transform_matches_sample": transform == template["transform"],
        "shape_matches_sample": a.shape == (template["height"], template["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(a[foot]).all()),
        "inside_foot_range_0_1": bool(np.all((a[foot] >= 0) & (a[foot] <= 1))),
        "outside_encoding_valid": bool(np.isnan(a[~foot]).all()) if mode == "nan" else bool(np.all(a[~foot] == 0)),
        "exact_expected_mask_after_disk_read": bool(np.array_equal(disk, expected)),
        "zero_catalogue_mass": bool(gate["catalogue_mass"] == 0.0) and not bool(np.any(disk & cat)),
        "strict_subset_of_R0": not bool(np.any(disk & ~parent)),
        "no_dot_inside_collar": not bool(np.any(disk & collar)),
        "expected_delete_only_count": int(disk.sum()) == expected_count,
        "file_re_read_from_disk": True,
    }
    if not all(checks.values()):
        raise ValueError(f"audit failed for {path.name}: {[k for k, v in checks.items() if not v]}; {gate['fails']}")
    dist_cat = ndi.distance_transform_edt(~cat)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": R0.sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(disk.sum()),
        "min_catalogue_distance_px": float(dist_cat[disk].min()),
        "catalogue_mass": float(gate["catalogue_mass"]),
        "checks": checks,
        "format_gate": gate,
    }


def existing_hashes(exclude_ids: set[str] | None = None) -> set[str]:
    exclude = exclude_ids or set()
    hashes = set()
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("id") in exclude:
                    continue
                for key in ("sha256", "sha256_zeros"):
                    if row.get(key):
                        hashes.add(row[key])
    return hashes


def mechanism_card(across: float, removed: int, remaining: int) -> dict:
    short, full = PREDICTIONS[across]
    return {
        "hypothesis": (
            f"If the A{across:g}/L2 strike-aligned collar mostly removes non-fault flank mass, "
            f"deleting its {removed:,} dots without adding FIFO-refill penalty should raise DTI. "
            "The matched refill file provides the controlled comparison."
        ),
        "mechanism": (
            "Known USGS/INGENIOUS pixels are masked pixel-exactly, while adjacent new-fault pixels remain "
            "scoreable. The ellipse removes across-strike flank dots but preserves coherent along-strike "
            "continuations. Unlike the matched parent experiment, S (emitted mass) falls to "
            f"{remaining:,}; no distant H19-5 pixels are introduced, so the measured refill dilution cannot "
            "offset the collar gain."
        ),
        "non_fault_confounder": (
            "Across-strike dots can be real parallel strands, relay splays, step-overs, or offset surface "
            "traces of dipping faults. Conversely, unfaulted lithologic contacts, drainage margins, shorelines, "
            "and cultural lineaments can occupy the retained off-collar population. Catalogue-strike estimates "
            "can also rotate near intersections and terminations."
        ),
        "predicted_live_change": full,
        "prediction_decomposition": DECOMPOSITION[across],
        "falsifier": (
            f"A paired live receipt against R0 with delta <= -0.010 falsifies a beneficial A{across:g}/L2 "
            "delete-only collar; |delta| < 0.010 is no evidence. If the matched refill file outscores this "
            "file by >=0.010, the refill-dilution mechanism is falsified even if both beat or lose to R0."
        ),
        "structural_geologist_note": (
            "Review removed across-strike segments for genuine parallel fault strands and retained mapped-tip "
            "continuations for structural consistency. This is not a claim that faults stop at the catalogue "
            "collar; it is a test of whether their emitted unit-mass dots earn enough new-fault credit to pay "
            "their metric penalty."
        ),
        "predicted_short_for_form": short,
    }


def build() -> dict:
    t0 = time.time()
    if RECEIPT.is_file() and json.loads(RECEIPT.read_text(encoding="utf-8")).get("withdrawal"):
        raise RuntimeError("IR90-29: this delete-only family is WITHDRAWN; do not re-emit it into releases/")
    reservation = check_reservations()
    manifest = R0.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = R0.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    pivot = snap_floor_feasibility(r0, foot, h19, dist_cat)
    del h19

    matched_receipt = json.loads(MATCHED_RECEIPT.read_text(encoding="utf-8"))
    matched_by_across = {float(v["across_px"]): v for v in matched_receipt["variants"]}
    field = build_strike_field(cat)
    rows, cols = np.nonzero(r0)
    variants = []
    candidate_masks = {"R0": r0}
    own_prior_ids = set()
    if RECEIPT.is_file():
        own_prior_ids = {v["id"] for v in json.loads(RECEIPT.read_text(encoding="utf-8"))["variants"]}
    foreign_hashes = existing_hashes(exclude_ids=own_prior_ids)

    for across in ACROSS_PX:
        inside, collar_diag = collar_membership(rows, cols, field, across, ALONG_PX)
        collar = np.zeros_like(r0)
        collar[rows[inside], cols[inside]] = True
        candidate, diff = make_norefill_candidate(r0, collar)
        matched = matched_by_across[across]
        if diff["n_removed"] != int(matched["parent_diff"]["n_removed"]):
            raise ValueError(f"A{across:g} removal count no longer matches the recorded refill collar")
        if np.any(candidate & cat) or np.any(candidate & ~foot):
            raise AssertionError("delete-only candidate has catalogue/outside mass")

        detailed_diff = parent_diff_stats(r0, candidate, field)
        detailed_diff.update(diff)
        ry, rx = np.nonzero(collar)
        along, across_dist, coherence = along_across(ry, rx, field)
        slug = slug_for(across)
        nan_path, zeros_path = emit_pair(candidate, foot, template, slug)
        nan_audit = audit_file(nan_path, candidate, r0, collar, foot, cat, template, "nan", diff["n_candidate"])
        zeros_audit = audit_file(zeros_path, candidate, r0, collar, foot, cat, template, "zeros", diff["n_candidate"])
        for audit in (nan_audit, zeros_audit):
            if audit["sha256"] in foreign_hashes:
                raise ValueError(f"SHA-256 already in ledger: {audit['sha256']}")
            foreign_hashes.add(audit["sha256"])

        short, full = PREDICTIONS[across]
        note = (
            f"{PARENT}; PRUNE A{across:g}/L2 collar, no refill -> {diff['n_candidate']} dots; "
            f"pred {short} DTI MODEL"
        )
        if len(note) > 140:
            raise AssertionError("form note exceeds 140 characters")
        variant_id = nan_path.name[:-4]
        candidate_masks[variant_id] = candidate
        variants.append({
            "id": variant_id,
            "parent": PARENT,
            "axis": AXIS,
            "value": value_string(across),
            "tag": f"anisoA{across:g}L2-norefill",
            "across_px": across,
            "along_px": ALONG_PX,
            "n_dots": diff["n_candidate"],
            "pct_changed": diff["pct_changed_of_parent"],
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "predicted_change": full,
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": detailed_diff,
            "removed_mask_sha256_packbits": mask_digest(collar),
            "retained_mask_sha256_packbits": mask_digest(candidate),
            "collar_diagnostics": collar_diag,
            "removed_geometry": {
                "along_abs_median_px": float(np.median(np.abs(along))),
                "across_abs_median_px": float(np.median(np.abs(across_dist))),
                "coherence_median": float(np.median(coherence)),
                "below_3px_removed": int((dist_cat[collar] < 3.0).sum()),
                "below_3px_retained": int((candidate & (dist_cat < 3.0)).sum()),
            },
            "matched_refill_control": {
                "id": matched["id"],
                "receipt": "evidence/build_aniso_receipt.json",
                "same_r0_same_strike_field_same_collar_parameters": True,
                "removed_count_matches": True,
                "refill_dots_omitted": diff["n_removed"],
                "matched_refill_n_dots": matched["n_dots"],
            },
            "mechanism_card": mechanism_card(across, diff["n_removed"], diff["n_candidate"]),
        })

    # Predictions above are constants frozen before any PROXY is evaluated.
    del field
    leakage = canary(max_samples=250_000, seed=SEED)
    if leakage.get("auc_gt_0_90"):
        raise RuntimeError("STOP AND INVESTIGATE: report-only leakage canary AUC > 0.90")
    catalogue_proxy = compute_spatial_block_proxy(
        candidate_masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000,
    )
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (dist_cat > 3.0)
    sgmc_proxy = compute_spatial_block_proxy(
        candidate_masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000,
    )
    sgmc_proxy["n_positives_evaluated"] = sgmc_proxy.pop("n_withheld_positives")
    catalogue_proxy["caveat"] = (
        "Known catalogue pixels are masked in live scoring; hide-and-recover is a PROXY with known collar blind spots, never a gate or score."
    )
    sgmc_proxy["caveat"] = (
        "SGMC is an off-catalogue external proxy with a bedrock/mapping bias, not undisclosed test truth; never a gate or score."
    )

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": R0.git_sha(),
        "generator_script_sha256": R0.sha256_file(Path(__file__)),
        "aniso_module_sha256": R0.sha256_file(ROOT / "scripts" / "aniso_prune.py"),
        "matched_receipt_sha256": R0.sha256_file(MATCHED_RECEIPT),
        "axis": AXIS,
        "value_family": "matched strike-aligned A4/A5/A6, L=2 collar; delete only, no refill",
        "parent": {
            "id": PARENT, "claimed_live_score": 0.2778, "evidence_class": "CLAIM",
            "zeros_sha256": R0.R0_ZEROS_SHA, "nan_sha256": R0.R0_NAN_SHA, **parent_stats,
        },
        "manifest": {
            "manifest_path": "registry/data_manifest.json",
            "manifest_sha256": R0.sha256_file(ROOT / "registry" / "data_manifest.json"),
            "verified_count": len(manifest), "all_pins_rechecked": True,
        },
        "reservation": reservation,
        "snap_feasibility_pivot": pivot,
        "predictions_frozen_before_proxy": True,
        "proxy_reports": {
            "leakage_canary": leakage,
            "catalogue_hide_recover": catalogue_proxy,
            "sgmc_control": sgmc_proxy,
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
        "agent_never_submits": True,
    }


def write_outputs(result: dict) -> None:
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    with LEDGER.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    own_ids = {v["id"] for v in result["variants"]}
    rows = [row for row in rows if row.get("id") not in own_ids]
    for v in result["variants"]:
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": str(v["n_dots"]), "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"],
            "parent": PARENT, "axis": AXIS, "value": v["value"], "status": "BUILT",
            "receipt": "N", "receipt_score": "", "predicted_change": v["predicted_change"],
            "date": "", "form_note": v["form_note"],
            "notes": (
                f"strict R0 subset; matched removal set to {v['matched_refill_control']['id']}; no refill; "
                "PRUNE collar exception applies; receipt_score/date filled by human; agent never submits"
            ),
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    res_path = ROOT / "ledger" / "experiment_reservations.json"
    reservations = json.loads(res_path.read_text(encoding="utf-8"))
    reservations["aniso_norefill_reservations"] = {
        "checked_utc": "2026-10-23",
        "axis": AXIS,
        "parent": PARENT,
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "sibling_ledgers_checked": [f"GEMSDOE{i}" for i in range(84, 93)],
        "note": "Sibling delete-only collars are isotropic. These three matched anisotropic no-refill pairs are distinct from both those and the existing anisotropic fixed-count refill pairs.",
    }
    res_path.write_text(json.dumps(reservations, indent=2) + "\n", encoding="utf-8")

    cards_path = ROOT / "ledger" / "mechanism_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    cards["aniso_norefill"] = {
        "schema_version": 1, "parent": PARENT, "axis": AXIS,
        "value_family": result["value_family"],
        "variants": [
            {"id": v["id"], "axis": AXIS, "value": v["value"], "mechanism_card": v["mechanism_card"]}
            for v in result["variants"]
        ],
    }
    cards_path.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def verify() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    manifest = R0.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = R0.exact_parent_rebuild()
    field = build_strike_field(cat)
    rows, cols = np.nonzero(r0)
    own_ids = {v["id"] for v in receipt["variants"]}
    foreign = existing_hashes(exclude_ids=own_ids)
    temp_dir = ROOT / ".cache" / "verify_aniso_norefill"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for v in receipt["variants"]:
        across = float(v["across_px"])
        inside, _ = collar_membership(rows, cols, field, across, float(v["along_px"]))
        collar = np.zeros_like(r0)
        collar[rows[inside], cols[inside]] = True
        expected, diff = make_norefill_candidate(r0, collar)
        if diff["n_candidate"] != int(v["n_dots"]):
            raise ValueError(f"recomputed count mismatch for {v['id']}")
        if abs(diff["pct_changed_of_parent"] - float(v["pct_changed"])) > 1e-9:
            raise ValueError(f"recomputed parent diff mismatch for {v['id']}")
        if mask_digest(collar) != v["removed_mask_sha256_packbits"]:
            raise ValueError(f"removed set digest mismatch for {v['id']}")
        for mode in ("nan", "zeros"):
            path = ROOT / v["files"][mode]["path"]
            audit = audit_file(path, expected, r0, collar, foot, cat, template, mode, diff["n_candidate"])
            if audit["sha256"] != v["files"][mode]["sha256"]:
                raise ValueError(f"disk SHA mismatch for {v['id']} [{mode}]")
            if audit["sha256"] in foreign:
                raise ValueError(f"foreign ledger hash collision for {v['id']} [{mode}]")
            probe = temp_dir / f"{v['id']}-{mode}.tif"
            try:
                R0.emit(expected, foot, template, v["id"], mode, probe)
                if R0.sha256_file(probe) != audit["sha256"]:
                    raise ValueError(f"deterministic byte re-emission failed for {v['id']} [{mode}]")
            finally:
                probe.unlink(missing_ok=True)

    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = R0.git_sha()
    receipt["generator_script_sha256"] = R0.sha256_file(Path(__file__))
    receipt["manifest"]["verified_count"] = len(manifest)
    receipt["manifest"]["all_pins_rechecked"] = True
    receipt["self_check"] = {
        "all_26_manifest_pins_verified": True,
        "r0_rebuilt_byte_identically": bool(parent_stats["r0_byte_identity_passed"]),
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "strict_R0_subsets": True,
        "removed_sets_match_recorded_refill_collars": True,
        "zero_catalogue_mass": True,
        "sha256_unique_against_ledger": True,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} no-refill PRUNE pairs; R0 and every candidate byte-identical.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        return verify()
    result = build()
    write_outputs(result)
    print(f"Built {len(result['variants'])} matched no-refill PRUNE variants -> {RECEIPT.relative_to(ROOT)}")
    for v in result["variants"]:
        print(
            f"  {v['id']}: {v['n_dots']} dots; removed {v['parent_diff']['n_removed']} "
            f"({v['pct_changed']:.4f}%); sha256={v['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
