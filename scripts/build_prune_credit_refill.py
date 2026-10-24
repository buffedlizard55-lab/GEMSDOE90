#!/usr/bin/env python3
"""Build fixed-count PRUNE variants whose refill uses the metric's marginal credit.

Parent: `h33-h33-2-b2` (R0), 37,654 unit-mass dots, >2 px Euclidean from the catalogue.
Axis: PRUNE. Value family: the recorded strike-aligned collar (across A in {4,5,6} px,
along held at the parent's 2 px) with the SAME fixed-count refill as the recorded
A4/A5/A6 L2 files -- but the refill *ordering* is the metric's own marginal kernel credit
(truth-free, evaluated on the pinned H19-5 proxy support) instead of the lineage's
recovered FIFO-BFS thinning order.

Why: every recorded PRUNE candidate refills with the inherited FIFO-BFS traversal order,
and 98.7-99.5 % of those refill dots land within 3 px of a dot that was already retained
(IR90-12) -- penalty without fresh credit. This family asks whether the ordering matters:
at each collar width the refill pool, the collar and the dot count are identical to the
recorded FIFO twin, so a live paired receipt isolates the refill policy.

Each variant
  1. removes every R0 dot inside the strike-aligned collar (along/2)^2 + (across/A)^2 <= 1,
  2. refills the exact same number of dots from the pinned H19-5 support, outside the
     collar, greedily by marginal kernel credit with exact local credit updates,
  3. is re-read from disk and checked against the format gate before it is recorded.

Local TIFFs go to ignored `releases/`; competition rasters are never added to Git.

Run:  .venv/bin/python scripts/build_prune_credit_refill.py --build
Check: .venv/bin/python scripts/build_prune_credit_refill.py --verify
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

import build_r0_variants as R0  # noqa: E402
from aniso_prune import build_strike_field, collar_membership, parent_diff_stats, refill_mask  # noqa: E402
from build_aniso_prune_norefill import existing_hashes, mask_digest  # noqa: E402
from build_aniso_prune_variants import (  # noqa: E402
    audit_file,
    canary,
    emit_pair,
    refill_diagnostics,
)
from build_relief_variants import compute_spatial_block_proxy  # noqa: E402
from src.prune_refill import credit_aware_refill, support_credit  # noqa: E402

DATA = R0.DATA
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "PRUNE"
DATE = "20261024"
ALONG_PX = 2.0
ACROSS_PX = (4.0, 5.0, 6.0)
R0_DOTS = R0.R0_DOTS
LEDGER = ROOT / "ledger" / "submissions.csv"
RECEIPT = ROOT / "evidence" / "prune_credit_refill_receipt.json"
SEED = 20261024

PREDICTIONS = {
    4.0: ("+0.004", "+0.004 DTI (MODEL; plausible -0.008 to +0.012; not a score)"),
    5.0: ("+0.005", "+0.005 DTI (MODEL; plausible -0.008 to +0.014; not a score)"),
    6.0: ("+0.003", "+0.003 DTI (MODEL; plausible -0.010 to +0.012; not a score)"),
}

# The recorded FIFO twins this family is matched against (same collar, same pool, same count).
FIFO_TWIN_IDS = {
    4.0: "h33-h33-2-b2-PRUNEanisoA4L2-20261023-0bf248e2",
    5.0: "h33-h33-2-b2-PRUNEanisoA5L2-20261023-15218061",
    6.0: "h33-h33-2-b2-PRUNEanisoA6L2-20261023-72dcdbd3",
}


def tag_for(across: float) -> str:
    return f"anisoA{across:g}L2Cred".replace(".", "p")


def value_string(across: float) -> str:
    return (
        f"tag={tag_for(across)}; collar across<={across:g}px, along<=2px (strike-aligned); "
        "fixed-count H19-5 credit-aware (max-marginal-kernel-credit) refill"
    )


def slug_for(across: float) -> str:
    return f"{PARENT}-PRUNE{tag_for(across)}-{DATE}"


def check_reservations() -> dict:
    expected = {value_string(a) for a in ACROSS_PX}
    own_slugs = {slug_for(a) for a in ACROSS_PX}
    own, foreign = [], []
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                value = row.get("value") or ""
                if "credit-aware" not in value:
                    continue
                ident = row.get("id") or ""
                if value in expected and ident.rsplit("-", 1)[0] in own_slugs:
                    own.append(ident)
                else:
                    foreign.append(ident or value)
    if foreign:
        raise ValueError(f"duplicate (AXIS, value) reservation already in ledger: {foreign}")
    return {
        "local_ledger_checked": True,
        "sibling_ledgers_checked_2026_10_23": [f"GEMSDOE{i}" for i in range(84, 93)],
        "selected_values": sorted(expected),
        "foreign_duplicates": foreign,
        "own_reproduction_rows_present": len(own),
        "distinctness": (
            "No audited sibling ledger contains a strike-aligned collar refilled by marginal "
            "kernel credit; every recorded anisotropic PRUNE row refills in the recovered "
            "FIFO-BFS thinning order. The collar pair (A, L=2) is the same geometry as the "
            "recorded A4/A5/A6 L2 files, so each variant is a matched placement contrast "
            "against its recorded FIFO twin."
        ),
        "matched_control_ids": {str(a): FIFO_TWIN_IDS[a] for a in ACROSS_PX},
    }


def make_candidate(r0, h19, foot, cat, field, across):
    """Apply one collar and refill the parent count by marginal kernel credit."""
    rows, cols = np.nonzero(r0)
    inside, diag = collar_membership(rows, cols, field, across, ALONG_PX)
    collar = np.zeros_like(r0)
    collar[rows[inside], cols[inside]] = True
    kept = r0 & ~collar
    n_refill = int(collar.sum())
    if n_refill == 0:
        raise ValueError(f"A={across:g}: collar removes no parent dots")

    # Same pool rule as the recorded FIFO twin: H19-5 support, footprint, not catalogue,
    # not already kept, outside the collar.
    pool = foot & h19 & ~cat & ~kept
    near = np.nonzero(pool & (field.dist <= across + 1e-9))
    inside_pool, _ = collar_membership(near[0], near[1], field, across, ALONG_PX)
    pool[near[0][inside_pool], near[1][inside_pool]] = False
    if int(pool.sum()) < n_refill:
        raise ValueError(f"A={across:g}: refill pool {int(pool.sum())} < {n_refill}")

    refill = credit_aware_refill(pool, kept, h19, n_refill, radius=3.0)
    candidate = kept | refill
    if int(candidate.sum()) != R0_DOTS:
        raise AssertionError("credit-aware refill did not hold the parent dot count")
    if np.any(candidate & cat) or np.any(candidate & collar) or np.any(candidate & ~foot):
        raise AssertionError("candidate violates catalogue/collar/footprint rule")
    if np.any(candidate & (field.dist <= 2.0)):
        raise AssertionError("candidate reintroduced mass inside R0's isotropic >2 px baseline")
    # The matched FIFO comparator on the identical pool (report-only).
    refill_fifo = refill_mask(pool, R0.fifo_bfs_visit_rank(h19), n_refill)
    return candidate, collar, refill, refill_fifo, pool, diag


def refill_credit_report(kept, refill_cred, refill_fifo, support, radius=3.0) -> dict:
    """Truth-free comparison of the two refill orderings on the H19-5 proxy support.

    Report-only: it measures kernel credit over the parent's own corroborated-ridge
    support, never over undisclosed truth, and never ranks a file.
    """
    base = float(support_credit(kept, support, radius).sum())
    cred = float(support_credit(kept | refill_cred, support, radius).sum())
    fifo = float(support_credit(kept | refill_fifo, support, radius).sum())
    return {
        "kept_credit": base,
        "credit_aware_refill_credit": cred,
        "fifo_refill_credit": fifo,
        "credit_aware_marginal_credit": cred - base,
        "fifo_marginal_credit": fifo - base,
        "credit_aware_minus_fifo": cred - fifo,
        "note": (
            "REPORT ONLY: total triangular-kernel credit over the pinned H19-5 proxy support. "
            "A larger marginal credit means the refill covers more currently-uncredited "
            "support pixels; it is not a score and does not rank a file."
        ),
    }


def mechanism_card(across, removed, refill_diag, credit_report) -> dict:
    short, full = PREDICTIONS[across]
    return {
        "hypothesis": (
            f"The recorded A{across:g}/L2 collar deletes {removed:,} near-catalogue R0 dots and then "
            "restores the same count with the lineage's FIFO-BFS traversal order, which places "
            "98.7-99.5 % of replacements within 3 px of a dot already retained. That ordering is a "
            "tie-break, not the metric: it adds the 0.2*(S-M) penalty while supplying almost no "
            "fresh kernel credit. Replacing it with the metric's own marginal kernel credit -- "
            "evaluated truth-free on the same H19-5 proxy support -- should put each replacement "
            "where it covers currently-uncredited corroborated-ridge pixels, i.e. the pixels the "
            "collar deletion orphaned, and therefore recover more coverage per replacement."
        ),
        "mechanism": (
            f"Ellipse (along/2)^2 + (across/{across:g})^2 <= 1 removes the collar dots; the exact "
            f"{R0_DOTS} dot count is restored from outside-collar H19-5 support (d_cat>2 px, the "
            "parent baseline) by a greedy max-marginal-credit rule with exact local credit updates "
            "inside the 300 m kernel. Marginal credit of a candidate q is "
            "sum_offsets max(0, k*support[q+off] - credit[q+off]) + own-pixel term, with credit the "
            "current best kernel credit from dots already placed. Ties break on flat raster index, so "
            "the file is byte-reproducible. Catalogue pixels remain exactly zero mass."
        ),
        "non_fault_confounder": (
            "The orphaned pixels the credit-aware refill targets are adjacent to mapped traces, where "
            "lithologic contacts, drainage divides and shoreline/road alignments mimic faults; a "
            "refill that concentrates mass there can simply re-add the false mass the collar removed. "
            "H19-5 is also the parent's own support, so 'covering H19-5 pixels' is not the same as "
            "covering undisclosed truth, and the H19-5 field itself fires on the known catalogue."
        ),
        "predicted_live_change": full,
        "prediction_decomposition": (
            f"MODEL: the collar term is unchanged from the recorded FIFO twin (same collar, same pool, "
            f"same count); only the refill term changes. On the H19-5 proxy the credit-aware refill "
            f"supplies {credit_report['credit_aware_marginal_credit']:.0f} kernel credit versus "
            f"{credit_report['fifo_marginal_credit']:.0f} for the FIFO ordering "
            f"(difference {credit_report['credit_aware_minus_fifo']:+.0f}), so the prediction is the "
            "recorded twin's collar gain plus a refill term proportional to that difference, discounted "
            "because proxy-support credit is not truth credit."
        ),
        "falsifier": (
            f"A paired same-week live receipt against the recorded FIFO twin "
            f"({FIFO_TWIN_IDS[across]}) with delta <= -0.010 rejects the refill-ordering mechanism at "
            "this collar width; |delta| < 0.010 is no evidence. A monotone decline across A4->A6 would "
            "also falsify the mechanism, since the credit-aware refill's advantage should persist while "
            "the collar widens."
        ),
        "structural_geologist_note": (
            "Inspect where the credit-aware refill placed mass relative to the retained strands: the "
            "prediction is that it fills the gaps the collar deletion opened beside mapped traces, not "
            "that it invents new structures. If the replacements simply re-occupy the deleted flank "
            "positions, the collar and the refill are cancelling and the edit is a no-op."
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
        raise RuntimeError("FIFO-BFS ranking does not cover the H19-5 support exactly")
    field = build_strike_field(cat)
    dist_cat = ndi.distance_transform_edt(~cat)

    own_ids = {slug_for(a) for a in ACROSS_PX}
    foreign_hashes = existing_hashes(exclude_ids=set())
    own_hashes_prior: set[str] = set()
    if RECEIPT.is_file():
        own_hashes_prior = {
            v["sha256"] for v in json.loads(RECEIPT.read_text(encoding="utf-8"))["variants"]
        }
    variants = []
    masks = {"R0": r0}

    for across in ACROSS_PX:
        candidate, collar, refill, refill_fifo, pool, collar_diag = make_candidate(
            r0, h19, foot, cat, field, across)
        diff = parent_diff_stats(r0, candidate, field)
        if not 1.0 <= diff["pct_changed_of_parent"] <= 50.0:
            raise ValueError(f"A={across:g} changes {diff['pct_changed_of_parent']:.3f}% (need 1-50%)")
        refill_diag = refill_diagnostics(r0 & ~collar, refill, field)
        credit_report = refill_credit_report(r0 & ~collar, refill, refill_fifo, h19)

        slug = slug_for(across)
        nan_path, zeros_path = emit_pair(candidate, foot, template, slug)
        nan_audit = audit_file(nan_path, candidate, foot, cat, template, "nan", collar)
        zeros_audit = audit_file(zeros_path, candidate, foot, cat, template, "zeros", collar)
        for audit in (nan_audit, zeros_audit):
            if audit["sha256"] in foreign_hashes and audit["sha256"] not in own_hashes_prior:
                raise ValueError(f"SHA-256 already in ledger: {audit['sha256']}")
            foreign_hashes.add(audit["sha256"])

        short, full = PREDICTIONS[across]
        note = (
            f"{PARENT}; PRUNE strike-aligned collar across<={across:g}px along<=2px, "
            f"credit-aware refill; predicted {short} DTI MODEL"
        )
        if len(note) > 140:
            raise AssertionError(f"form note is {len(note)} characters")
        variants.append({
            "id": f"{slug}-{nan_audit['sha256'][:8]}",
            "axis": AXIS,
            "tag": tag_for(across),
            "across_px": across,
            "along_px": ALONG_PX,
            "value": value_string(across),
            "n_dots": nan_audit["n_dots"],
            "pct_changed": round(diff["pct_changed_of_parent"], 6),
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "predicted_change": full,
            "form_note": note,
            "matched_fifo_twin_id": FIFO_TWIN_IDS[across],
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": diff,
            "removed_mask_sha256_packbits": mask_digest(collar),
            "refill_mask_sha256_packbits": mask_digest(refill),
            "collar_diagnostics": collar_diag,
            "refill": {
                "n_refill": int(refill.sum()),
                "pool_size": int(pool.sum()),
                "ordering": "metric marginal kernel credit, greedy, exact local credit updates (src/prune_refill.py)",
                "pool_rule": "H19-5 support, footprint, d_cat>2px (R0 baseline), outside collar, not retained",
                "matched_fifo_twin": FIFO_TWIN_IDS[across],
            },
            "refill_diagnostics": refill_diag,
            "refill_credit_comparison": credit_report,
            "removed_geometry": {
                "below_3px_removed": int((collar & (dist_cat < 3.0)).sum()),
                "below_3px_in_final": int((candidate & (dist_cat < 3.0)).sum()),
                "note": "PRUNE is the brief's explicit exception to the >=3 px rule; zero catalogue mass remains mandatory.",
            },
            "mechanism_card": mechanism_card(
                across, diff["n_removed"], refill_diag, credit_report),
        })
        masks[tag_for(across)] = candidate
        print(f"[built] {variants[-1]['id']}  {variants[-1]['n_dots']} dots  "
              f"{variants[-1]['pct_changed']:.4f}% diff  "
              f"cred/fifo credit {credit_report['credit_aware_marginal_credit']:.0f}/"
              f"{credit_report['fifo_marginal_credit']:.0f}  sha256={nan_audit['sha256'][:16]}...")

    leakage = canary(max_samples=250_000, seed=SEED)
    if leakage.get("auc_gt_0_90"):
        raise RuntimeError("STOP AND INVESTIGATE: leakage canary AUC > 0.90")
    catalogue_proxy = compute_spatial_block_proxy(
        masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000)
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (dist_cat > 3.0)
    sgmc_proxy = compute_spatial_block_proxy(
        masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000)
    sgmc_proxy["n_positives_evaluated"] = sgmc_proxy.pop("n_withheld_positives")
    catalogue_proxy["caveat"] = (
        "PROXY only: known catalogue labels are live-masked and this holdout has collar blind "
        "spots; never a gate or score.")
    sgmc_proxy["caveat"] = (
        "PROXY only: SGMC has bedrock/mapping bias and is not undisclosed test truth; "
        "never a gate or score.")

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": R0.git_sha(),
        "generator_script_sha256": R0.sha256_file(Path(__file__)),
        "prune_refill_module_sha256": R0.sha256_file(ROOT / "src" / "prune_refill.py"),
        "axis": AXIS,
        "value_family": (
            "strike-aligned collar across in {4,5,6} px, along 2 px; fixed-count H19-5 "
            "credit-aware (max-marginal-kernel-credit) refill"),
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
            "zero_catalogue_mass": True,
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
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": str(v["n_dots"]), "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"], "parent": PARENT,
            "axis": AXIS, "value": v["value"], "status": "BUILT", "receipt": "N",
            "receipt_score": "", "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": (
                "fixed 37,654 count; strike-aligned collar; credit-aware marginal-kernel-credit "
                "refill; matched FIFO-twin contrast; receipt_score/date filled by human; "
                "agent never submits"),
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    res_path = ROOT / "ledger" / "experiment_reservations.json"
    reservations = json.loads(res_path.read_text(encoding="utf-8"))
    reservations["prune_credit_refill_reservations"] = {
        "checked_utc": "2026-10-24", "axis": AXIS, "parent": PARENT,
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "sibling_ledgers_checked": [f"GEMSDOE{i}" for i in range(84, 93)],
        "matched_fifo_twins": {str(v["across_px"]): v["matched_fifo_twin_id"]
                               for v in result["variants"]},
        "note": (
            "All three pairs hold 37,654 dots and reuse the recorded A4/A5/A6 L2 collar geometry "
            "and pool. They are distinct (AXIS, value) rows because the refill ordering is part of "
            "the value string; each is a matched placement contrast against its recorded FIFO twin."),
    }
    res_path.write_text(json.dumps(reservations, indent=2) + "\n", encoding="utf-8")

    cards_path = ROOT / "ledger" / "mechanism_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    cards["prune_credit_refill"] = {
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
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    field = build_strike_field(cat)
    own_ids = {v["id"] for v in receipt["variants"]}
    foreign = existing_hashes(exclude_ids=own_ids)
    temp_dir = ROOT / ".cache" / "verify_prune_credit_refill"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for v in receipt["variants"]:
        expected, collar, refill, _fifo, _pool, _diag = make_candidate(
            r0, h19, foot, cat, field, float(v["across_px"]))
        if mask_digest(collar) != v["removed_mask_sha256_packbits"] \
                or mask_digest(refill) != v["refill_mask_sha256_packbits"]:
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
    print(f"Verified {len(receipt['variants'])} credit-aware-refill PRUNE pairs byte-for-byte.")
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
    print(f"Built {len(result['variants'])} credit-aware-refill PRUNE variants -> "
          f"{RECEIPT.relative_to(ROOT)}")
    for v in result["variants"]:
        print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.4f}% diff, "
              f"sha256={v['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
