#!/usr/bin/env python3
"""Build fixed-count A5 PRUNE variants with a narrower along-strike collar.

R0 -> same catalogue strike field -> ellipse (along/L)^2 + (across/5)^2 <= 1
-> delete inside dots -> refill the exact count from pinned H19-5 in its recovered
FIFO-BFS order outside the same ellipse.  L = 1.5, 1.0, 0.5 px; the recorded
comparator is A5/L2.  Only PRUNE geometry changes.  Every output holds 37,654
unit-mass dots, as the brief's PRUNE recipe requires.

Run: .venv/bin/python scripts/build_aniso_prune_along.py --build
Disk/byte self-check: .venv/bin/python scripts/build_aniso_prune_along.py --verify
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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_r0_variants as R0  # noqa: E402
from aniso_prune import (  # noqa: E402
    build_strike_field,
    collar_membership,
    parent_diff_stats,
    refill_mask,
)
from build_aniso_prune_variants import (  # noqa: E402
    audit_file,
    canary,
    emit_pair,
    refill_diagnostics,
)
from build_aniso_prune_norefill import existing_hashes, mask_digest  # noqa: E402
from build_relief_variants import compute_spatial_block_proxy  # noqa: E402

DATA = R0.DATA
LEDGER = ROOT / "ledger" / "submissions.csv"
RECEIPT = ROOT / "evidence" / "aniso_along_refill_receipt.json"
PARENT = "h33-h33-2-b2"
AXIS = "PRUNE"
DATE = "20261023"
ACROSS_PX = 5.0
ALONG_PX = (1.5, 1.0, 0.5)
R0_DOTS = R0.R0_DOTS
SEED = 20261023
PREDICTIONS = {
    1.5: ("+0.004", "+0.004 DTI (MODEL; plausible -0.008 to +0.012; not a score)"),
    1.0: ("+0.005", "+0.005 DTI (MODEL; plausible -0.008 to +0.014; not a score)"),
    0.5: ("+0.003", "+0.003 DTI (MODEL; plausible -0.010 to +0.012; not a score)"),
}


def tag_for(along: float) -> str:
    return f"anisoA5L{along:g}".replace(".", "p")


def value_string(along: float) -> str:
    return (
        f"tag={tag_for(along)}; collar across<=5px, along<={along:g}px (strike-aligned); "
        "fixed-count H19-5 FIFO-BFS refill"
    )


def slug_for(along: float) -> str:
    return f"{PARENT}-PRUNE{tag_for(along)}-{DATE}"


def make_candidate(
    r0: np.ndarray,
    h19: np.ndarray,
    rank: np.ndarray,
    foot: np.ndarray,
    cat: np.ndarray,
    field,
    along: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict]:
    """Apply one ellipse and refill to the parent count from ranked H19-5 support."""
    rows, cols = np.nonzero(r0)
    inside, diag = collar_membership(rows, cols, field, ACROSS_PX, along)
    collar = np.zeros_like(r0)
    collar[rows[inside], cols[inside]] = True
    kept = r0 & ~collar
    n_refill = int(collar.sum())
    if n_refill == 0:
        raise ValueError(f"A5/L{along:g} removes no R0 dots")

    # Preserve R0's baseline isotropic >2 px exclusion.  Without this term a
    # narrower along-strike ellipse could reintroduce H19-5 mass at d_cat <= 2,
    # confounding the geometry test with the parent's original PRUNE decision.
    pool = foot & h19 & ~cat & ~kept & (field.dist > 2.0)
    near = np.nonzero(pool & (field.dist <= ACROSS_PX + 1e-9))
    inside_pool, _ = collar_membership(near[0], near[1], field, ACROSS_PX, along)
    pool[near[0][inside_pool], near[1][inside_pool]] = False
    if int(pool.sum()) < n_refill:
        raise ValueError(f"A5/L{along:g} refill pool {int(pool.sum())} < {n_refill}")
    refill = refill_mask(pool, rank, n_refill)
    candidate = kept | refill
    if int(candidate.sum()) != R0_DOTS:
        raise AssertionError("fixed-count refill did not hold 37,654 dots")
    if np.any(candidate & cat) or np.any(candidate & collar) or np.any(candidate & ~foot):
        raise AssertionError("candidate violates catalogue/collar/footprint rule")
    if np.any(candidate & (field.dist <= 2.0)):
        raise AssertionError("candidate reintroduced mass inside R0's isotropic >2 px baseline")
    return candidate, collar, refill, pool, diag


def check_reservations() -> dict:
    expected = {value_string(a) for a in ALONG_PX}
    own_slugs = {slug_for(a) for a in ALONG_PX}
    own = []
    foreign = []
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").upper() != AXIS:
                    continue
                value = row.get("value") or ""
                if "norefill" in value.lower().replace("-", ""):
                    continue  # IR90-29 withdrawn delete-only family is a different value
                if not value.startswith("tag=anisoA5L"):
                    continue
                ident = row.get("id") or ""
                if value in expected and ident.rsplit("-", 1)[0] in own_slugs:
                    own.append(ident)
                else:
                    foreign.append(ident or value)
    if foreign:
        raise ValueError(f"duplicate (PRUNE, value) reservation: {foreign}")
    if own and not RECEIPT.is_file():
        raise ValueError("along-ladder rows exist without their receipt")
    return {
        "local_ledger_checked": True,
        "sibling_ledgers_checked_2026_10_23": [f"GEMSDOE{i}" for i in range(84, 93)],
        "selected_values": sorted(expected),
        "foreign_duplicates": foreign,
        "own_reproduction_rows_present": len(own),
        "distinctness": "No audited sibling contains an anisotropic A5 collar with L=1.5, 1.0, or 0.5; prior anisotropic rows use L=2.",
    }


def mechanism_card(along: float, removed: int, refill_pct: float) -> dict:
    short, full = PREDICTIONS[along]
    return {
        "hypothesis": (
            f"The recorded A5/L2 collar prunes too far along mapped strike. Narrowing only the along radius "
            f"to {along:g} px should preserve genuine unmapped continuations and avoid dilutive refill while "
            "retaining the across-strike flank cleanup."
        ),
        "mechanism": (
            f"The ellipse removes {removed:,} R0 dots where (along/{along:g})^2 + (across/5)^2 <= 1 "
            "at coherent catalogue traces, then restores exactly 37,654 dots from outside-collar H19-5 "
            "support with d_cat>2 px (R0's baseline) in the recovered FIFO-BFS order. Relative to A5/L2, fewer along-strike dots are "
            "removed and fewer distant refill dots are needed. Catalogue pixels remain exactly zero mass."
        ),
        "non_fault_confounder": (
            "A mapped-tip continuation can be a real fault, but an apparently continuous magnetic/topographic "
            "lineament can also be a lithologic contact, drainage, shoreline, road, or pipeline. Preserving "
            "more along-strike dots can therefore retain false mass; the FIFO refill can also prefer unrelated "
            "geographic components rather than fault likelihood."
        ),
        "predicted_live_change": full,
        "prediction_decomposition": (
            "MODEL: across-strike collar gain approximately held from A5/L2; along-strike continuation loss "
            f"and refill dilution both decrease. {refill_pct:.1f}% of this file's refills sit within 3 px "
            "of a retained dot, so the remaining refill still offsets part of the collar gain."
        ),
        "falsifier": (
            f"A paired live receipt against R0 with delta <= -0.010 falsifies the A5/L{along:g} policy; "
            "|delta| < 0.010 is no evidence. If A5/L2 outscores the narrower-L files by >=0.010, the "
            "hypothesis that L2 over-prunes real continuations is falsified."
        ),
        "structural_geologist_note": (
            "Inspect retained mapped-tip projections and step-overs, not just across-strike flanks. "
            "The collar is a positional-uncertainty experiment, not a geological claim that continuations "
            "inside the ellipse are absent."
        ),
        "predicted_short_for_form": short,
    }


def build() -> dict:
    t0 = time.time()
    reservation = check_reservations()
    manifest = R0.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = R0.exact_parent_rebuild()
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    rank = R0.fifo_bfs_visit_rank(h19)
    if np.any(rank[h19] < 0) or np.any(rank[~h19] != -1):
        raise RuntimeError("FIFO-BFS ranking does not cover H19-5 exactly")
    field = build_strike_field(cat)
    dist_cat = ndi.distance_transform_edt(~cat)
    own_prior = set()
    if RECEIPT.is_file():
        own_prior = {v["id"] for v in json.loads(RECEIPT.read_text(encoding="utf-8"))["variants"]}
    foreign_hashes = existing_hashes(exclude_ids=own_prior)
    variants = []
    masks = {"R0": r0}

    for along in ALONG_PX:
        candidate, collar, refill, pool, collar_diag = make_candidate(r0, h19, rank, foot, cat, field, along)
        diff = parent_diff_stats(r0, candidate, field)
        if not 1.0 <= diff["pct_changed_of_parent"] <= 50.0:
            raise ValueError(f"A5/L{along:g} changes {diff['pct_changed_of_parent']:.3f}% (need 1-50%)")
        refill_diag = refill_diagnostics(r0 & ~collar, refill, field)
        slug = slug_for(along)
        nan_path, zeros_path = emit_pair(candidate, foot, template, slug)
        nan_audit = audit_file(nan_path, candidate, foot, cat, template, "nan", collar)
        zeros_audit = audit_file(zeros_path, candidate, foot, cat, template, "zeros", collar)
        for audit in (nan_audit, zeros_audit):
            if audit["sha256"] in foreign_hashes:
                raise ValueError(f"SHA-256 already in ledger: {audit['sha256']}")
            foreign_hashes.add(audit["sha256"])
        short, full = PREDICTIONS[along]
        note = f"{PARENT}; PRUNE A5/L{along:g}, fixed-count refill; pred {short} DTI MODEL"
        if len(note) > 140:
            raise AssertionError("form note exceeds 140 characters")
        variant_id = nan_path.name[:-4]
        masks[variant_id] = candidate
        variants.append({
            "id": variant_id,
            "parent": PARENT,
            "axis": AXIS,
            "value": value_string(along),
            "tag": tag_for(along),
            "across_px": ACROSS_PX,
            "along_px": along,
            "n_dots": R0_DOTS,
            "pct_changed": diff["pct_changed_of_parent"],
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "predicted_change": full,
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": diff,
            "removed_mask_sha256_packbits": mask_digest(collar),
            "refill_mask_sha256_packbits": mask_digest(refill),
            "collar_diagnostics": collar_diag,
            "refill": {
                "n_refill": int(refill.sum()), "pool_size": int(pool.sum()),
                "ordering": "recovered H19-5 8-connected FIFO-BFS visitation order",
                "pool_rule": "H19-5 & footprint & d_cat>2px (R0 baseline) & outside ellipse & not retained",
            },
            "refill_diagnostics": refill_diag,
            "removed_geometry": {
                "below_3px_removed": int((collar & (dist_cat < 3.0)).sum()),
                "below_3px_in_final": int((candidate & (dist_cat < 3.0)).sum()),
                "note": "PRUNE is the brief's explicit exception to the >=3 px rule; zero catalogue mass remains mandatory.",
            },
            "mechanism_card": mechanism_card(
                along, diff["n_removed"], refill_diag["refill_within_3px_of_retained_pct"],
            ),
        })

    del field
    leakage = canary(max_samples=250_000, seed=SEED)
    if leakage.get("auc_gt_0_90"):
        raise RuntimeError("STOP AND INVESTIGATE: leakage canary AUC > 0.90")
    catalogue_proxy = compute_spatial_block_proxy(
        masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000,
    )
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (dist_cat > 3.0)
    sgmc_proxy = compute_spatial_block_proxy(
        masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000,
    )
    sgmc_proxy["n_positives_evaluated"] = sgmc_proxy.pop("n_withheld_positives")
    catalogue_proxy["caveat"] = "PROXY only: known catalogue labels are live-masked and this holdout has collar blind spots; never a gate or score."
    sgmc_proxy["caveat"] = "PROXY only: SGMC has bedrock/mapping bias and is not undisclosed test truth; never a gate or score."

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": R0.git_sha(),
        "generator_script_sha256": R0.sha256_file(Path(__file__)),
        "aniso_module_sha256": R0.sha256_file(ROOT / "scripts" / "aniso_prune.py"),
        "axis": AXIS,
        "value_family": "A5 fixed across strike; L=1.5/1.0/0.5 along strike; fixed-count H19-5 FIFO refill",
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
        "compliance": {
            "fixed_count_required_and_satisfied": True,
            "parent_isotropic_gt_2px_floor_preserved_on_every_final_dot": True,
            "n_dots_each": R0_DOTS,
            "withdrawn_delete_only_receipt": "evidence/aniso_norefill_receipt.json",
            "withdrawn_delete_only_irregularity": "IR90-29",
        },
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
    own_values = {v["value"] for v in result["variants"]}
    rows = [r for r in rows if r.get("id") not in own_ids and r.get("value") not in own_values]
    for v in result["variants"]:
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)", "encoding": "nan primary; zeros fallback",
            "n_dots": str(v["n_dots"]), "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"], "parent": PARENT,
            "axis": AXIS, "value": v["value"], "status": "BUILT", "receipt": "N",
            "receipt_score": "", "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": "fixed 37,654 count; A5 across strike; narrower along-strike collar; receipt_score/date filled by human; agent never submits",
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    res_path = ROOT / "ledger" / "experiment_reservations.json"
    reservations = json.loads(res_path.read_text(encoding="utf-8"))
    reservations["aniso_along_refill_reservations"] = {
        "checked_utc": "2026-10-23", "axis": AXIS, "parent": PARENT,
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "sibling_ledgers_checked": [f"GEMSDOE{i}" for i in range(84, 93)],
        "note": "All three pairs hold 37,654 dots. They are distinct from the recorded A4/A5/A6 L=2 family and from all audited sibling isotropic values.",
    }
    res_path.write_text(json.dumps(reservations, indent=2) + "\n", encoding="utf-8")

    cards_path = ROOT / "ledger" / "mechanism_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    cards["aniso_along_refill"] = {
        "schema_version": 1, "parent": PARENT, "axis": AXIS, "value_family": result["value_family"],
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
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    rank = R0.fifo_bfs_visit_rank(h19)
    field = build_strike_field(cat)
    own_ids = {v["id"] for v in receipt["variants"]}
    foreign = existing_hashes(exclude_ids=own_ids)
    temp_dir = ROOT / ".cache" / "verify_aniso_along"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for v in receipt["variants"]:
        expected, collar, refill, _pool, _diag = make_candidate(
            r0, h19, rank, foot, cat, field, float(v["along_px"]),
        )
        if mask_digest(collar) != v["removed_mask_sha256_packbits"] or mask_digest(refill) != v["refill_mask_sha256_packbits"]:
            raise ValueError(f"collar/refill digest mismatch for {v['id']}")
        for mode in ("nan", "zeros"):
            path = ROOT / v["files"][mode]["path"]
            audit = audit_file(path, expected, foot, cat, template, mode, collar)
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
    receipt["self_check"] = {
        "all_26_manifest_pins_verified": True,
        "r0_rebuilt_byte_identically": bool(parent_stats["r0_byte_identity_passed"]),
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "fixed_37654_dot_count": True,
        "zero_catalogue_mass": True,
        "sha256_unique_against_ledger": True,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} fixed-count A5 along-strike PRUNE pairs byte-for-byte.")
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
    print(f"Built {len(result['variants'])} fixed-count along-strike PRUNE variants -> {RECEIPT.relative_to(ROOT)}")
    for v in result["variants"]:
        print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.4f}% diff, sha256={v['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
