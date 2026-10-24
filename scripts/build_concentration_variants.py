#!/usr/bin/env python3
"""Build three controlled AXIS=CONCENTRATION variants from byte-identical R0.

Session selection: 15 km (150 px) structural-interaction block prior built from
the pinned competition feature bands 3/4/7/18 (`tmi_hg`, `geod_2ndinv`,
`geod_shearrate`, `iso_grav_anom_hg`). R0's 15 km block-density CV is 0.5103,
inside the brief's reported 0.51-0.59 winning band. The three variants move
10%, 15% and 20% of the 37,654 dots from the lowest-prior 35% of blocks into
the highest-prior 35%, holding count on H19-5 support. All additions are at
Euclidean catalogue distance >= 3 px; untouched R0 dots retain the parent's
2.236 px floor rather than confounding CONCENTRATION with PRUNE.

This script never contacts DrivenData, never reads a leaderboard, never logs in
and never submits. Competition rasters remain in ignored `.cache/gems_data/`
and generated rasters in ignored `releases/`.

Run build:  `.venv/bin/python scripts/build_concentration_variants.py --build`
Run verify: `.venv/bin/python scripts/build_concentration_variants.py --verify`
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

import build_r0_variants as base_build  # noqa: E402
import build_relief_variants as relief_build  # noqa: E402  report-only proxy helpers
from src.concentration import (  # noqa: E402
    BLOCK_PX,
    MIN_FOOT_FRAC,
    PRIOR_BANDS,
    density_cv,
    region_evenness_report,
    reallocate_to_high_prior,
    structural_prior,
)
from src.validate import validate as format_validate  # noqa: E402

DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "CONCENTRATION"
DATE = "20261023"
SEED = 20261023
R0_DOTS = 37_654
FEATURE_PATH = DATA / "training_features.tif"
SGMC_PATH = DATA / "external" / "derived_sgmc_faults_100m_u8.tif"
RECEIPT_PATH = ROOT / "evidence" / "concentration_build_receipt.json"
RESERVATIONS_PATH = ROOT / "ledger" / "experiment_reservations.json"
LEDGER_PATH = ROOT / "ledger" / "submissions.csv"
CARDS_PATH = ROOT / "ledger" / "mechanism_cards.json"

# Cross-session audit performed read-only via gh api on 2026-10-23: the default
# branch of each public buffedlizard55-lab/GEMSDOE* repository; 9 repositories
# contained a ledger/submissions.csv and 33 CONCENTRATION values were found.
CROSS_REPO_CONCENTRATION_VALUES = (
    "10% of dots moved from lowest-prior 0.8km blocks to highest-prior",
    "15% of dots moved from lowest-prior 0.8km blocks to highest-prior",
    "20% of dots moved from lowest-prior 0.8km blocks to highest-prior",
    "5km-t25-move2400",
    "5km-t50-move3765",
    "spread5km-move2400",
    "b1km-move15",
    "spr15",
    "dens15",
    "rand15",
    "15pct-1km-grad",
    "b5km-move10",
    "b5km-move15",
    "b5km-move20",
    "b5km-ridge-up4",
    "b5km-ridge-up8",
    "b5km-cvband-down4",
    "c10",
    "c15",
    "c20",
    "b10px-m10",
    "b10px-m20",
    "b50px-m20",
    "gdr25m10",
    "gdr10m10",
    "gdr25rm10",
)

VARIANT_SPECS = (
    {
        "tag": "b15km-struct-move10pct",
        "file_value": "b15kmstruct10pct",
        "mass_frac": 0.10,
        "n_shift": 3_765,
        "pred_short": "+0.002",
        "predicted_change": "+0.002 DTI (MODEL; plausible interval -0.008 to +0.012; not a score)",
        "hypothesis": (
            "A 10% shift from the lowest-prior 15 km structural blocks to the highest-prior 15 km blocks "
            "will move R0 mass toward active-deformation and potential-field edge corridors, where new "
            "fault pixels are more likely, without yet over-concentrating the point field."
        ),
        "predicted_sign_reason": (
            "At the lowest dose the block-density CV rises only modestly above R0's 0.510; the gain from "
            "putting dots in higher-prior corridors can outweigh the extra max-kernel redundancy."
        ),
    },
    {
        "tag": "b15km-struct-move15pct",
        "file_value": "b15kmstruct15pct",
        "mass_frac": 0.15,
        "n_shift": 5_648,
        "pred_short": "-0.002",
        "predicted_change": "-0.002 DTI (MODEL; plausible interval -0.013 to +0.009; not a score)",
        "hypothesis": (
            "If the 15 km structural prior is predictive, doubling most of the way from a 10% to a 15% "
            "reallocation should improve DTI; if the winning CV band is a hard constraint, redundancy "
            "will instead make the middle dose neutral-to-negative."
        ),
        "predicted_sign_reason": (
            "The 15 km density CV moves further beyond the reported 0.51-0.59 band and high-prior blocks "
            "already start denser than low-prior blocks, so the model centre is slightly negative."
        ),
    },
    {
        "tag": "b15km-struct-move20pct",
        "file_value": "b15kmstruct20pct",
        "mass_frac": 0.20,
        "n_shift": 7_531,
        "pred_short": "-0.006",
        "predicted_change": "-0.006 DTI (MODEL; plausible interval -0.018 to +0.006; not a score)",
        "hypothesis": (
            "A 20% shift is the strong-dose counterpoint: if the prior is wrong or the 0.51-0.59 "
            "block-density band is causal, concentrated additions will be redundant under the max "
            "kernel and the score should fall."
        ),
        "predicted_sign_reason": (
            "At 20% the 15 km CV is expected to overshoot the reported winning band substantially; "
            "the dose response, not any one projection, is the experiment."
        ),
    },
)


def value_string(spec: dict) -> str:
    return (
        f"{spec['tag']}; lowest 35% -> highest 35% by equal-rank strain/edge prior on 15km blocks; "
        f"fixed count 37654; added d_cat>=3px"
    )


def check_concentration_reservations() -> None:
    """Fail closed if any selected (AXIS, value) pair is already occupied."""
    res = json.loads(RESERVATIONS_PATH.read_text(encoding="utf-8")) if RESERVATIONS_PATH.is_file() else {}
    block = res.get("concentration_reservations_20261023", {})
    occupied_tags = set(block.get("occupied_tags", []))
    occupied_values = set(block.get("occupied_values", [])) | set(block.get("cross_repo_occupied_values", []))
    for spec in VARIANT_SPECS:
        if spec["tag"] in occupied_tags:
            raise ValueError(f"duplicate experiment reservation: (CONCENTRATION, {spec['tag']}) already reserved")
        val = value_string(spec)
        if val in occupied_values:
            raise ValueError(f"duplicate experiment reservation: (CONCENTRATION, {val}) already reserved")
        if spec["file_value"] in occupied_values:
            raise ValueError(f"duplicate experiment reservation: (CONCENTRATION, {spec['file_value']}) already reserved")

    with LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if (row.get("axis") or "").strip().upper() != AXIS:
                continue
            val = row.get("value") or ""
            for spec in VARIANT_SPECS:
                if spec["tag"] in val or value_string(spec) == val:
                    raise ValueError(
                        f"duplicate experiment in ledger/submissions.csv: (CONCENTRATION, {spec['tag']})"
                    )


def existing_ledger_hashes(exclude_ids: set[str] | None = None) -> set[str]:
    exclude = exclude_ids or set()
    hashes: set[str] = set()
    with LEDGER_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("id") in exclude:
                continue
            for col in ("sha256", "sha256_zeros"):
                val = (row.get(col) or "").strip()
                if val:
                    hashes.add(val)
    return hashes


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
    prior = structural_prior(str(FEATURE_PATH), foot)
    return {
        "input_receipt": input_receipt,
        "template": template,
        "foot": foot,
        "cat": cat,
        "r0": r0,
        "parent_stats": parent_stats,
        "dist_cat": dist_cat,
        "h19": h19,
        "support": support,
        "prior": prior,
    }


def validate_concentration_file(
    path: Path,
    expected_mask: np.ndarray,
    r0: np.ndarray,
    foot: np.ndarray,
    cat: np.ndarray,
    dist_cat: np.ndarray,
    support: np.ndarray,
    prior: dict,
    sample_profile: dict,
    mode: str,
) -> dict:
    audit = relief_build.validate_relief_file(
        path, expected_mask, r0, foot, cat, dist_cat,
        DATA / base_build.PIN_PATHS["sample_submission"],
        DATA / base_build.PIN_PATHS["catalogue"],
        sample_profile,
        mode,
    )
    with rasterio.open(path) as src:
        a = src.read(1)
    disk_mask = (a > 0.5) & foot
    added = disk_mask & ~r0
    removed = r0 & ~disk_mask
    extra = {
        "all_added_dots_on_h19_support": bool(np.all(support[added])),
        "all_added_dots_in_high_prior_blocks": bool(np.all(prior["recipient_mask"][added])),
        "all_removed_dots_in_low_prior_blocks": bool(np.all(prior["donor_mask"][removed])),
        "inside_foot_values_are_binary": bool(np.all(np.isin(a[foot], (0.0, 1.0)))),
        "format_gate_revalidated_from_disk": bool(format_validate(
            str(path), str(DATA / base_build.PIN_PATHS["sample_submission"]),
            str(DATA / base_build.PIN_PATHS["catalogue"]), zeros_outside=(mode == "zeros")
        )["pass"]),
    }
    if not all(extra.values()):
        raise ValueError(f"concentration validator failed for {path.name}: {[k for k, v in extra.items() if not v]}")
    audit["checks"].update(extra)
    audit["added_dots"] = int(added.sum())
    audit["removed_dots"] = int(removed.sum())
    audit["retained_parent_dots"] = int((disk_mask & r0).sum())
    return audit


def mechanism_card(spec: dict, cv_before: float, cv_after: float) -> dict:
    return {
        "hypothesis": spec["hypothesis"],
        "mechanism": (
            "Block prior = equal mean of in-footprint percentile ranks of |tmi_hg|, |geod_2ndinv|, "
            "|geod_shearrate| and |iso_grav_anom_hg| from pinned training_features.tif, averaged over "
            "15 km (150 px) blocks with >=50% footprint. Dots are removed from the lowest-prior 35% "
            "of blocks by minimum exclusive R=3 px triangular-kernel credit and added in the "
            f"highest-prior 35% by maximum marginal credit on H19-5. {spec['n_shift']:,} unit-mass "
            f"dots ({100*spec['mass_frac']:.0f}% of R0) move at fixed count 37,654; "
            f"15 km density CV {cv_before:.4f}->{cv_after:.4f}."
        ),
        "non_fault_confounder": (
            "Geodetic strain gradients can follow groundwater withdrawal, volcanic inflation or "
            "basin-edge sediment compaction; magnetic and gravity gradients can mark dikes, resistant "
            "lithologic contacts, pluvial shorelines, roads or pipelines rather than faults. High-prior "
            "blocks may also be dense in mapped faults whose exact pixels are masked."
        ),
        "predicted_sign_and_size": spec["predicted_change"],
        "why_this_sign": spec["predicted_sign_reason"],
        "falsifier": (
            "A same-week paired live receipt against R0 with Delta <= -0.010 DTI rejects this "
            "structural-prior concentration dose. If the 10% arm is >= +0.010 but 15/20% are worse, "
            "the prior has a narrow optimum; if all |Delta| < 0.010, the axis has no evidence."
        ),
        "structural_geologist_note": (
            "Inspect the removed low-prior strands for blind basin faults and the added high-prior "
            "strands for unfaulted lithologic or cultural edges. The 400 m GeoDAWN line spacing "
            "(https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7) makes the "
            "potential-field positions uncertain by about one kernel radius; this is a block-allocation "
            "experiment, not a new fault map."
        ),
    }


def emit_pair(mask: np.ndarray, foot: np.ndarray, template: dict, slug: str) -> tuple[Path, Path, str, str]:
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


def build() -> dict:
    t0 = time.time()
    check_concentration_reservations()
    inp = load_inputs()
    foot, cat, r0 = inp["foot"], inp["cat"], inp["r0"]
    dist_cat, support, prior = inp["dist_cat"], inp["support"], inp["prior"]
    template, parent_stats = inp["template"], inp["parent_stats"]
    cv_before = density_cv(r0, foot)
    candidate_masks = {"R0": r0}
    variants = []

    for spec in VARIANT_SPECS:
        cand, shift_stats = reallocate_to_high_prior(r0, support, dist_cat, prior, spec["n_shift"])
        if int(cand.sum()) != R0_DOTS:
            raise AssertionError("fixed-count invariant failed")
        added, removed = cand & ~r0, r0 & ~cand
        if int(added.sum()) != spec["n_shift"] or int(removed.sum()) != spec["n_shift"]:
            raise AssertionError("moved-dot count invariant failed")
        pct_changed = 100.0 * float((cand ^ r0).sum()) / float(R0_DOTS)
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"{spec['tag']} changes {pct_changed:.6f}% of R0, outside 1-50%")
        region = region_evenness_report(r0, cand, prior, spec["mass_frac"])
        if not region["pass"]:
            raise ValueError(f"{spec['tag']} fails region-evenness gate: {region['checks']}")
        cv_after = density_cv(cand, foot)
        card = mechanism_card(spec, cv_before, cv_after)

        slug = f"{PARENT}-{AXIS}{spec['file_value']}-{DATE}"
        nan_path, zeros_path, nan_sha, zeros_sha = emit_pair(cand, foot, template, slug)
        other_hashes = existing_ledger_hashes()
        if nan_sha in other_hashes or zeros_sha in other_hashes:
            raise ValueError(f"SHA-256 collision with an existing ledger row for {slug}")
        nan_audit = validate_concentration_file(
            nan_path, cand, r0, foot, cat, dist_cat, support, prior, template, "nan"
        )
        zeros_audit = validate_concentration_file(
            zeros_path, cand, r0, foot, cat, dist_cat, support, prior, template, "zeros"
        )
        if nan_audit["sha256"] != nan_sha or zeros_audit["sha256"] != zeros_sha:
            raise ValueError("re-read SHA-256 differs from emitted SHA-256")
        if nan_audit["added_dots_below_3px"] or zeros_audit["added_dots_below_3px"]:
            raise ValueError("an added dot violates the 3 px catalogue collar")

        note = (
            f"{PARENT}; CONC 15km structural-prior move {100*spec['mass_frac']:.0f}% low->high; "
            f"37654 dots; pred {spec['pred_short']} MODEL"
        )
        if len(note) > 140:
            raise AssertionError(f"form note is {len(note)} chars: {note}")
        base = nan_path.stem
        candidate_masks[base] = cand
        variants.append({
            "id": base,
            "parent": PARENT,
            "axis": AXIS,
            "value": value_string(spec),
            "tag": spec["tag"],
            "n_dots": R0_DOTS,
            "n_shift": spec["n_shift"],
            "mass_shifted_pct": 100.0 * spec["n_shift"] / R0_DOTS,
            "pct_changed": pct_changed,
            "removed_dots": int(removed.sum()),
            "added_dots": int(added.sum()),
            "retained_dots": int((cand & r0).sum()),
            "sha256": nan_sha,
            "sha256_zeros": zeros_sha,
            "status": "BUILT",
            "predicted_change": spec["predicted_change"],
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": {
                "removed_from_parent": int(removed.sum()),
                "added_to_candidate": int(added.sum()),
                "retained_from_parent": int((cand & r0).sum()),
                "symmetric_difference_px": int((cand ^ r0).sum()),
                "pct_changed_of_R0": pct_changed,
            },
            "reallocation": shift_stats,
            "block_density_cv": {
                "block_px": BLOCK_PX,
                "block_km": BLOCK_PX / 10.0,
                "min_footprint_fraction": MIN_FOOT_FRAC,
                "before": round(cv_before, 6),
                "after": round(cv_after, 6),
                "delta": round(cv_after - cv_before, 6),
            },
            "region_evenness": region,
            "mechanism_card": card,
        })

    # Report-only diagnostics: never gates, never scores, never rank the variants.
    canary = relief_build.compute_leakage_canary(foot, cat, prior["composite"], seed=SEED)
    canary["features"]["structural_edge_strain_prior_15km_inputs"] = canary["features"].pop(
        "composite_landform_relief_idx"
    )
    if canary["max_feature"] == "composite_landform_relief_idx":
        canary["max_feature"] = "structural_edge_strain_prior_15km_inputs"
    canary["structural_prior_symmetric_auc"] = canary["features"][
        "structural_edge_strain_prior_15km_inputs"
    ]["symmetric_auc"]
    with rasterio.open(SGMC_PATH) as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (dist_cat > 3.0)
    hide = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000
    )
    hide["caveat"] = (
        "Known catalogue pixels are masked pixel-exactly; all added dots are >=3 px away and earn zero "
        "R=3 px kernel credit on withheld catalogue positives. PROXY ONLY, never a gate or score."
    )
    sgmc = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000
    )
    sgmc["caveat"] = (
        "Off-catalogue USGS SGMC geologic-map faults over-represent exposed bedrock and are not the "
        "hidden new-fault labels. PROXY ONLY, never a gate or score."
    )

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": base_build.git_sha(),
        "generator_script": "scripts/build_concentration_variants.py",
        "generator_script_sha256": base_build.sha256_file(Path(__file__)),
        "axis": AXIS,
        "session_selection_reason": (
            "Read-only audit of 79 public buffedlizard55-lab/GEMSDOE* default branches found 33 occupied "
            "CONCENTRATION values, none at 15 km with this pinned strain/edge prior. R0's 15 km CV "
            "0.5103 lies in the brief's reported 0.51-0.59 band."
        ),
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": base_build.R0_ZEROS_SHA,
            "nan_sha256": base_build.R0_NAN_SHA,
            **parent_stats,
        },
        "prior_definition": {
            "source": "registry/data_manifest.json:training_features; owner-supplied competition mirror",
            "bands": list(PRIOR_BANDS),
            **prior["meta"],
            "leakage_policy": "no hidden/public test truth; no geothermal wells, springs or vents",
        },
        "reallocation_operator": {
            "support": "off-catalogue H19-5 corroborated ridge mask",
            "drop_rule": "greedy minimum exclusive R=3 px triangular-kernel credit in low-prior blocks, donor dots restricted to d_cat>=3 px",
            "add_rule": "greedy maximum marginal R=3 px credit in high-prior blocks, all additions d_cat>=3 px",
            "deterministic_tie_break": "(row, col) ascending",
            "seed_used_in_variant_construction": None,
        },
        "manifest": {
            "manifest_path": "registry/data_manifest.json",
            "verified_count": len(inp["input_receipt"]),
            "all_pins_rechecked": True,
            "files": inp["input_receipt"],
        },
        "r0_block_density_cv": round(cv_before, 6),
        "proxy_reports": {
            "catalogue_hide_recover": hide,
            "leakage_canary": canary,
            "sgmc_control": sgmc,
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
        "not_committed_to_git": True,
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
            "id": v["id"],
            "site": "GEMSDOE90",
            "name": v["id"],
            "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback",
            "n_dots": str(v["n_dots"]),
            "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"],
            "sha256_zeros": v["sha256_zeros"],
            "parent": v["parent"],
            "axis": v["axis"],
            "value": v["value"],
            "status": "BUILT",
            "receipt": "N",
            "receipt_score": "",
            "predicted_change": v["predicted_change"],
            "date": "",
            "form_note": v["form_note"],
            "notes": (
                f"moved={v['n_shift']} dots ({v['mass_shifted_pct']:.3f}%); 15km CV "
                f"{v['block_density_cv']['before']:.4f}->{v['block_density_cv']['after']:.4f}; "
                "region-evenness PASS; added d_cat>=3px; receipt_score/date filled by human; agent never submits"
            ),
        })
    with LEDGER_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    cards = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
    cards["active_session_axis"] = AXIS
    cards["concentration"] = {
        "schema_version": 1,
        "parent": PARENT,
        "axis": AXIS,
        "variants": [
            {"id": v["id"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
            for v in result["variants"]
        ],
    }
    CARDS_PATH.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")

    res = json.loads(RESERVATIONS_PATH.read_text(encoding="utf-8"))
    res["concentration_reservations_20261023"] = {
        "checked_utc": "2026-10-23",
        "axis": AXIS,
        "parent": PARENT,
        "scope": (
            "Read-only gh api audit of default-branch ledger/submissions.csv in 79 public "
            "buffedlizard55-lab/GEMSDOE* repos; 9 files present, 255 axis rows, 33 CONCENTRATION rows."
        ),
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "cross_repo_occupied_values": sorted(set(CROSS_REPO_CONCENTRATION_VALUES)),
        "selected_values": [v["tag"] for v in result["variants"]],
        "why_distinct": (
            "No indexed sibling builds a 15 km block prior from the four pinned strain/potential-field "
            "bands; existing values use 0.8/1/5 km or 10/50 px blocks, thermal/GDR priors, or generic "
            "density/CV moves. Repeat builds of these exact tags fail closed."
        ),
        "caveat": (
            "Default-branch public repository audit is not proof of every private or unindexed entity "
            "submission. Human must check any missing entity ledger before spending a scored slot."
        ),
    }
    RESERVATIONS_PATH.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")


def verify_all() -> int:
    inp = load_inputs()
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    template, foot, cat, r0, parent_stats = inp["template"], inp["foot"], inp["cat"], inp["r0"], inp["parent_stats"]
    dist_cat, support, prior = inp["dist_cat"], inp["support"], inp["prior"]
    spec_by_tag = {s["tag"]: s for s in VARIANT_SPECS}
    our_ids = {v["id"] for v in receipt["variants"]}
    other_hashes = existing_ledger_hashes(exclude_ids=our_ids)
    tmp_dir = ROOT / ".cache" / "verify_concentration_bytes"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for v in receipt["variants"]:
        spec = spec_by_tag[v["tag"]]
        expected, stats = reallocate_to_high_prior(r0, support, dist_cat, prior, spec["n_shift"])
        if int(expected.sum()) != R0_DOTS:
            raise ValueError(f"recomputed {v['id']} count != {R0_DOTS}")
        pct_changed = 100.0 * float((expected ^ r0).sum()) / float(R0_DOTS)
        if abs(pct_changed - float(v["pct_changed"])) > 1e-6:
            raise ValueError(f"recomputed {v['id']} parent-diff mismatch")
        region = region_evenness_report(r0, expected, prior, spec["mass_frac"])
        if not region["pass"]:
            raise ValueError(f"recomputed {v['id']} fails region-evenness gate")
        for mode_name in ("nan", "zeros"):
            fpath = ROOT / v["files"][mode_name]["path"]
            audit = validate_concentration_file(
                fpath, expected, r0, foot, cat, dist_cat, support, prior, template, mode_name
            )
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"disk SHA-256 mismatch for {v['id']} [{mode_name}]")
            if audit["sha256"] in other_hashes:
                raise ValueError(f"SHA-256 collides with prior ledger entry: {v['id']} [{mode_name}]")
            tmp_file = tmp_dir / f"{v['id']}-{mode_name}.tif"
            try:
                base_build.emit(expected, foot, template, v["id"], mode_name, tmp_file)
                if base_build.sha256_file(tmp_file) != audit["sha256"]:
                    raise ValueError(f"deterministic byte re-emission failed for {v['id']} [{mode_name}]")
            finally:
                tmp_file.unlink(missing_ok=True)

    verified_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verified_utc"] = verified_utc
    receipt["verification_git_sha"] = base_build.git_sha()
    receipt["generator_script_sha256"] = base_build.sha256_file(Path(__file__))
    receipt["manifest"]["verified_count"] = len(inp["input_receipt"])
    receipt["manifest"]["all_pins_rechecked"] = True
    receipt["self_check"] = {
        "all_26_manifest_pins_verified": True,
        "r0_rebuilt_byte_identically": bool(parent_stats["r0_byte_identity_passed"]),
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "region_evenness_gate_pass": True,
        "no_sha256_collision_with_other_ledger_rows": True,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    r0_receipt = {
        "generated_utc": verified_utc,
        "git_sha": base_build.git_sha(),
        "generator_script_sha256": base_build.sha256_file(ROOT / "scripts" / "build_r0_variants.py"),
        "parent": PARENT,
        "method": "reconstruct h33-h33-2-b2 as pinned h27-4 solo-d2.8 & (Euclidean distance to catalogue > 2 px), then re-emit with sample_submission.tif profile",
        "rebuilt": {
            "zeros_sha256": parent_stats["r0_rebuilt_zeros_sha256"],
            "nan_sha256": parent_stats["r0_rebuilt_nan_sha256"],
            "dots": parent_stats["r0_dots"],
            "below_3px": parent_stats["r0_below_3px"],
        },
        "expected": {
            "zeros_sha256": base_build.R0_ZEROS_SHA,
            "nan_sha256": base_build.R0_NAN_SHA,
            "dots": R0_DOTS,
        },
        "all_checks_passed": bool(parent_stats["r0_byte_identity_passed"] and parent_stats["d28_symmetric_difference_px"] == 0),
        "manifest_verified_count": len(inp["input_receipt"]),
        "no_competition_inputs_added_to_git": True,
    }
    (ROOT / "evidence" / "r0_rebuild_receipt.json").write_text(json.dumps(r0_receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} concentration pairs from disk; R0 rebuilt byte-identically")
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
        print(f"Built {len(result['variants'])} CONCENTRATION variants from exact R0; receipt -> {RECEIPT_PATH.relative_to(ROOT)}")
        for v in result["variants"]:
            print(
                f"  {v['id']}: {v['n_dots']} dots, moved {v['n_shift']}, "
                f"{v['pct_changed']:.3f}% diff, CV {v['block_density_cv']['before']:.4f}->"
                f"{v['block_density_cv']['after']:.4f}, sha256={v['sha256']}"
            )
        return 0
    return verify_all()


if __name__ == "__main__":
    raise SystemExit(main())
