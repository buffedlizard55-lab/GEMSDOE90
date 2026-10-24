#!/usr/bin/env python3
"""Re-emit the 18 core BUILT candidates recorded at this branch's start, fail-closed.

Why this exists: `releases/*.tif` is gitignored (this repo is public and the brief
forbids committing competition rasters), so the built candidates do not survive a
fresh clone or a new sandbox. This script reproduces the *same* recorded
(AXIS, value) pairs -- it does not create a new experiment -- and refuses to
finish unless every re-emitted file matches the SHA-256 already recorded in
`evidence/build_receipt.json`, `evidence/relief_build_receipt.json`,
`evidence/concentration_build_receipt.json`, `evidence/mass_build_receipt.json`,
`evidence/mass_high_dose_receipt.json`, `evidence/build_aniso_receipt.json`, and
`ledger/submissions.csv`. Main's later MASS-add, continuity and A5-refill families
have their own generators/verifiers; run those for the slotted candidates.

The original PRUNE generator `scripts/build_r0_variants.py` is deliberately NOT
modified: its SHA-256 (06f667c1...) remains pinned in `evidence/r0_rebuild_receipt.json`
and `evidence/build_receipt.json`. `--build` on both generators stays refused by
the (AXIS, value) reservation guards.

Run: .venv/bin/python scripts/restore_releases.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src import mass as mass_core  # noqa: E402

import build_r0_variants as build  # noqa: E402
import build_relief_variants as relief_build  # noqa: E402
import build_concentration_variants as conc_build  # noqa: E402
import build_mass_shadow as mass_shadow  # noqa: E402
import build_mass_high_dose as mass_high  # noqa: E402
import build_aniso_prune_variants as aniso  # noqa: E402

PRUNE_RECEIPT = ROOT / "evidence" / "build_receipt.json"
RELIEF_RECEIPT = ROOT / "evidence" / "relief_build_receipt.json"
CONCENTRATION_RECEIPT = ROOT / "evidence" / "concentration_build_receipt.json"
MASS_RECEIPT = ROOT / "evidence" / "mass_build_receipt.json"
MASS_HIGH_RECEIPT = ROOT / "evidence" / "mass_high_dose_receipt.json"
ANISO_RECEIPT = ROOT / "evidence" / "build_aniso_receipt.json"
LEDGER = ROOT / "ledger" / "submissions.csv"


def ledger_hashes() -> dict[str, tuple[str, str]]:
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        rows = [row for row in csv.DictReader(fh) if row.get("status") == "BUILT"]
    return {row["id"]: (row["sha256"], row["sha256_zeros"]) for row in rows}


def main() -> int:
    prune_receipt = json.loads(PRUNE_RECEIPT.read_text(encoding="utf-8"))
    relief_receipt = json.loads(RELIEF_RECEIPT.read_text(encoding="utf-8"))
    concentration_receipt = json.loads(CONCENTRATION_RECEIPT.read_text(encoding="utf-8"))
    mass_receipt = json.loads(MASS_RECEIPT.read_text(encoding="utf-8"))
    mass_high_receipt = json.loads(MASS_HIGH_RECEIPT.read_text(encoding="utf-8"))
    aniso_receipt = json.loads(ANISO_RECEIPT.read_text(encoding="utf-8"))
    expected_ledger = ledger_hashes()
    recorded_ids = set()
    for receipt in (
        prune_receipt, relief_receipt, concentration_receipt,
        mass_receipt, mass_high_receipt, aniso_receipt,
    ):
        recorded_ids |= {v["id"] for v in receipt["variants"]}
    if not recorded_ids.issubset(expected_ledger):
        raise SystemExit("STOP: ledger BUILT rows and build receipts disagree")

    build.verify_manifest_inputs()  # rechecks all 26 pins, aborts on any mismatch
    template, foot, cat, r0, parent_stats = build.exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~cat)
    h19 = build.read_binary(build.DATA / build.PIN_PATHS["h19_5"], foot)
    rank = build.fifo_bfs_visit_rank(h19)

    build.OUT.mkdir(parents=True, exist_ok=True)
    tmp_dir = ROOT / ".cache" / "restore_releases"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    report = []

    def restore_files(variant: dict, mask: np.ndarray, audit_fn) -> dict:
        """Emit a recorded pair, require its recorded bytes, then audit it from disk."""
        nan_path = ROOT / variant["files"]["nan"]["path"]
        zeros_path = ROOT / variant["files"]["zeros"]["path"]
        produced = {}
        for mode, target in (("nan", nan_path), ("zeros", zeros_path)):
            tmp = tmp_dir / f"{variant['id']}-{mode}.tif"
            build.emit(mask, foot, template, variant["id"], mode, tmp)
            got = build.sha256_file(tmp)
            want = variant["files"][mode]["sha256"]
            if got != want:
                tmp.unlink(missing_ok=True)
                raise SystemExit(
                    f"STOP: byte reproduction failed for {variant['id']} [{mode}]: {got} != {want}"
                )
            tmp.replace(target)
            audit = audit_fn(target, mode)
            if audit["sha256"] != want:
                raise SystemExit(f"STOP: post-write audit failed for {target.name}")
            produced[mode] = audit
        if (produced["nan"]["sha256"], produced["zeros"]["sha256"]) != expected_ledger[variant["id"]]:
            raise SystemExit(f"STOP: {variant['id']} disagrees with ledger/submissions.csv")
        return produced

    # 1. Restore recorded PRUNE candidates
    for variant in prune_receipt["variants"]:
        cutoff = float(variant["threshold_px"])
        kept = r0 & (distance > cutoff)
        removed = r0 & ~kept
        eligible = h19 & foot & ~cat & (distance > cutoff) & ~kept
        ey, ex = np.nonzero(eligible)
        n_refill = int(removed.sum())
        if n_refill > len(ey):
            raise SystemExit(f"STOP: insufficient refill support for {variant['id']}")
        order = np.argsort(rank[ey, ex], kind="stable")[:n_refill]
        mask = kept.copy()
        mask[ey[order], ex[order]] = True
        if int(mask.sum()) != build.R0_DOTS:
            raise SystemExit(f"STOP: rebuilt {variant['id']} does not hold {build.R0_DOTS} dots")
        changed = 100.0 * int(np.count_nonzero(mask ^ r0)) / build.R0_DOTS
        if abs(changed - float(variant["pct_changed"])) > 1e-6:
            raise SystemExit(f"STOP: parent diff drifted for {variant['id']}")

        nan_path = ROOT / variant["files"]["nan"]["path"]
        zeros_path = ROOT / variant["files"]["zeros"]["path"]
        produced = {}
        for mode, target in (("nan", nan_path), ("zeros", zeros_path)):
            tmp = tmp_dir / f"{variant['id']}-{mode}.tif"
            build.emit(mask, foot, template, variant["id"], mode, tmp)
            got = build.sha256_file(tmp)
            want = variant["files"][mode]["sha256"]
            if got != want:
                tmp.unlink(missing_ok=True)
                raise SystemExit(
                    f"STOP: byte reproduction failed for {variant['id']} [{mode}]: {got} != {want}"
                )
            tmp.replace(target)
            audit = build.validate_file(target, mask, foot, cat, template, mode)
            if audit["sha256"] != want or audit["n_dots"] != build.R0_DOTS:
                raise SystemExit(f"STOP: post-write audit failed for {target.name}")
            produced[mode] = audit

        if (produced["nan"]["sha256"], produced["zeros"]["sha256"]) != expected_ledger[variant["id"]]:
            raise SystemExit(f"STOP: {variant['id']} disagrees with ledger/submissions.csv")
        report.append({
            "id": variant["id"],
            "axis": "PRUNE",
            "threshold_px": cutoff,
            "n_dots": produced["nan"]["n_dots"],
            "pct_changed": round(changed, 6),
            "min_catalogue_distance_px": produced["nan"]["min_catalogue_distance_px"],
            "sha256": produced["nan"]["sha256"],
            "sha256_zeros": produced["zeros"]["sha256"],
            "bytes_match_recorded": True,
            "all_gate_checks": all(produced["nan"]["checks"].values())
                               and all(produced["zeros"]["checks"].values()),
            "paths": [str(nan_path.relative_to(ROOT)), str(zeros_path.relative_to(ROOT))],
        })
        print(f"[reproduced] {variant['id']}  {produced['nan']['n_dots']} dots  {changed:.3f}% changed  "
              f"sha256={produced['nan']['sha256'][:16]}...")

    # 2. Restore recorded RELIEF candidates
    support = h19 & foot & ~cat
    _relief_idx, terciles, _cuts, _meta = relief_build.load_relief_layers(foot)
    spec_by_tag = {s["tag"]: s for s in relief_build.VARIANT_SPECS}
    sample_path = build.DATA / build.PIN_PATHS["sample_submission"]
    cat_path = build.DATA / build.PIN_PATHS["catalogue"]

    for variant in relief_receipt["variants"]:
        spec = spec_by_tag[variant["tag"]]
        mask, stats = relief_build.build_mask_for_spec(spec, r0, support, terciles, distance)
        if int(mask.sum()) != build.R0_DOTS:
            raise SystemExit(f"STOP: rebuilt {variant['id']} does not hold {build.R0_DOTS} dots")
        changed = stats["pct_changed_symmetric"]
        if abs(changed - float(variant["pct_changed"])) > 1e-6:
            raise SystemExit(f"STOP: parent diff drifted for {variant['id']}")

        nan_path = ROOT / variant["files"]["nan"]["path"]
        zeros_path = ROOT / variant["files"]["zeros"]["path"]
        produced = {}
        for mode, target in (("nan", nan_path), ("zeros", zeros_path)):
            tmp = tmp_dir / f"{variant['id']}-{mode}.tif"
            build.emit(mask, foot, template, variant["id"], mode, tmp)
            got = build.sha256_file(tmp)
            want = variant["files"][mode]["sha256"]
            if got != want:
                tmp.unlink(missing_ok=True)
                raise SystemExit(
                    f"STOP: byte reproduction failed for {variant['id']} [{mode}]: {got} != {want}"
                )
            tmp.replace(target)
            audit = relief_build.validate_relief_file(
                target, mask, r0, foot, cat, distance, sample_path, cat_path, template, mode
            )
            if audit["sha256"] != want or audit["n_dots"] != build.R0_DOTS:
                raise SystemExit(f"STOP: post-write audit failed for {target.name}")
            produced[mode] = audit

        if (produced["nan"]["sha256"], produced["zeros"]["sha256"]) != expected_ledger[variant["id"]]:
            raise SystemExit(f"STOP: {variant['id']} disagrees with ledger/submissions.csv")
        report.append({
            "id": variant["id"],
            "axis": "RELIEF",
            "tag": variant["tag"],
            "n_dots": produced["nan"]["n_dots"],
            "pct_changed": round(changed, 6),
            "min_catalogue_distance_all_dots_px": produced["nan"]["min_catalogue_distance_all_dots_px"],
            "min_catalogue_distance_added_dots_px": produced["nan"]["min_catalogue_distance_added_dots_px"],
            "sha256": produced["nan"]["sha256"],
            "sha256_zeros": produced["zeros"]["sha256"],
            "bytes_match_recorded": True,
            "all_gate_checks": all(produced["nan"]["checks"].values())
                               and all(produced["zeros"]["checks"].values()),
            "paths": [str(nan_path.relative_to(ROOT)), str(zeros_path.relative_to(ROOT))],
        })
        print(f"[reproduced] {variant['id']}  {produced['nan']['n_dots']} dots  {changed:.3f}% changed  "
              f"added_min_d_cat={produced['nan']['min_catalogue_distance_added_dots_px']:.3f}px  "
              f"sha256={produced['nan']['sha256'][:16]}...")

    # 3. Restore recorded CONCENTRATION candidates
    conc_inputs = conc_build.load_inputs()
    conc_prior = conc_inputs["prior"]
    conc_support = conc_inputs["support"]
    conc_dist = conc_inputs["dist_cat"]
    conc_spec_by_tag = {s["tag"]: s for s in conc_build.VARIANT_SPECS}

    for variant in concentration_receipt["variants"]:
        spec = conc_spec_by_tag[variant["tag"]]
        mask, stats = conc_build.reallocate_to_high_prior(
            r0, conc_support, conc_dist, conc_prior, spec["n_shift"]
        )
        if int(mask.sum()) != build.R0_DOTS:
            raise SystemExit(f"STOP: rebuilt {variant['id']} does not hold {build.R0_DOTS} dots")
        changed = stats["pct_changed_symmetric"]
        if abs(changed - float(variant["pct_changed"])) > 1e-6:
            raise SystemExit(f"STOP: parent diff drifted for {variant['id']}")
        region = conc_build.region_evenness_report(r0, mask, conc_prior, spec["mass_frac"])
        if not region["pass"]:
            raise SystemExit(f"STOP: region-evenness gate failed for {variant['id']}")

        nan_path = ROOT / variant["files"]["nan"]["path"]
        zeros_path = ROOT / variant["files"]["zeros"]["path"]
        produced = {}
        for mode, target in (("nan", nan_path), ("zeros", zeros_path)):
            tmp = tmp_dir / f"{variant['id']}-{mode}.tif"
            build.emit(mask, foot, template, variant["id"], mode, tmp)
            got = build.sha256_file(tmp)
            want = variant["files"][mode]["sha256"]
            if got != want:
                tmp.unlink(missing_ok=True)
                raise SystemExit(
                    f"STOP: byte reproduction failed for {variant['id']} [{mode}]: {got} != {want}"
                )
            tmp.replace(target)
            audit = conc_build.validate_concentration_file(
                target, mask, r0, foot, cat, conc_dist, conc_support, conc_prior, template, mode
            )
            if audit["sha256"] != want or audit["n_dots"] != build.R0_DOTS:
                raise SystemExit(f"STOP: post-write audit failed for {target.name}")
            produced[mode] = audit

        if (produced["nan"]["sha256"], produced["zeros"]["sha256"]) != expected_ledger[variant["id"]]:
            raise SystemExit(f"STOP: {variant['id']} disagrees with ledger/submissions.csv")
        report.append({
            "id": variant["id"],
            "axis": "CONCENTRATION",
            "tag": variant["tag"],
            "n_dots": produced["nan"]["n_dots"],
            "pct_changed": round(changed, 6),
            "block_density_cv_before": variant["block_density_cv"]["before"],
            "block_density_cv_after": variant["block_density_cv"]["after"],
            "min_catalogue_distance_all_dots_px": produced["nan"]["min_catalogue_distance_all_dots_px"],
            "min_catalogue_distance_added_dots_px": produced["nan"]["min_catalogue_distance_added_dots_px"],
            "sha256": produced["nan"]["sha256"],
            "sha256_zeros": produced["zeros"]["sha256"],
            "bytes_match_recorded": True,
            "all_gate_checks": all(produced["nan"]["checks"].values())
                               and all(produced["zeros"]["checks"].values()),
            "paths": [str(nan_path.relative_to(ROOT)), str(zeros_path.relative_to(ROOT))],
        })
        print(f"[reproduced] {variant['id']}  {produced['nan']['n_dots']} dots  {changed:.3f}% changed  "
              f"CV15={variant['block_density_cv']['before']:.3f}->{variant['block_density_cv']['after']:.3f}  "
              f"sha256={produced['nan']['sha256'][:16]}...")

    # 4. Restore the 10/20/30% MASS shadow ladder
    ys, xs = np.nonzero(r0)
    pts = np.column_stack([ys, xs]).astype(float)
    neighbours = mass_core.neighbour_lists(pts)
    ladder_counts = [int(v["removed_dots"]) for v in mass_receipt["variants"]]
    ladder_res = mass_core.greedy_shadow_removal(
        pts, neighbours, n_remove=max(ladder_counts), snapshots=tuple(ladder_counts)
    )
    for variant in mass_receipt["variants"]:
        n_rem = int(variant["removed_dots"])
        mask = r0.copy()
        mask[ys, xs] = ~ladder_res["removed_masks"][n_rem]
        mask &= r0
        if int(mask.sum()) != variant["n_dots"]:
            raise SystemExit(f"STOP: rebuilt {variant['id']} dot count mismatch")
        changed = 100.0 * n_rem / build.R0_DOTS
        produced = restore_files(
            variant, mask,
            lambda target, mode, m=mask: mass_shadow.validate_candidate(
                target, m, foot, cat, template, mode, r0, distance
            ),
        )
        report.append({
            "id": variant["id"], "axis": "MASS", "dose_pct": variant["dose_pct"],
            "n_dots": produced["nan"]["n_dots"], "pct_changed": round(changed, 6),
            "min_catalogue_distance_px": produced["nan"]["min_catalogue_distance_px"],
            "sha256": produced["nan"]["sha256"], "sha256_zeros": produced["zeros"]["sha256"],
            "bytes_match_recorded": True,
            "all_gate_checks": all(produced["nan"]["checks"].values()) and all(produced["zeros"]["checks"].values()),
            "paths": [variant["files"]["nan"]["path"], variant["files"]["zeros"]["path"]],
        })
        print(f"[reproduced] {variant['id']}  {produced['nan']['n_dots']} dots  {changed:.3f}% changed  "
              f"sha256={produced['nan']['sha256'][:16]}...")

    # 5. Restore the high-dose MASS arms and seeded random control
    high_shadow_counts = [int(v["removed_dots"]) for v in mass_high_receipt["variants"] if v["selection_rule"] == "shadow"]
    high_res = mass_core.greedy_shadow_removal(
        pts, neighbours, n_remove=max(high_shadow_counts), snapshots=tuple(high_shadow_counts)
    )
    for variant in mass_high_receipt["variants"]:
        n_rem = int(variant["removed_dots"])
        mask = r0.copy()
        if variant["selection_rule"] == "shadow":
            mask[ys, xs] = ~high_res["removed_masks"][n_rem]
        else:
            pick = mass_high.random_removal(len(ys), n_rem, int(variant.get("seed") or mass_high.SEED))
            mask[ys[pick], xs[pick]] = False
        mask &= r0
        if int(mask.sum()) != variant["n_dots"]:
            raise SystemExit(f"STOP: rebuilt {variant['id']} dot count mismatch")
        if not mass_high.region_evenness_gate(variant["spatial_removal"]):
            raise SystemExit(f"STOP: recorded region-evenness gate fails for {variant['id']}")
        changed = 100.0 * n_rem / build.R0_DOTS
        produced = restore_files(
            variant, mask,
            lambda target, mode, m=mask: mass_shadow.validate_candidate(
                target, m, foot, cat, template, mode, r0, distance
            ),
        )
        report.append({
            "id": variant["id"], "axis": "MASS", "selection_rule": variant["selection_rule"],
            "dose_pct": variant["dose_pct"], "n_dots": produced["nan"]["n_dots"],
            "pct_changed": round(changed, 6),
            "min_catalogue_distance_px": produced["nan"]["min_catalogue_distance_px"],
            "sha256": produced["nan"]["sha256"], "sha256_zeros": produced["zeros"]["sha256"],
            "bytes_match_recorded": True,
            "all_gate_checks": all(produced["nan"]["checks"].values()) and all(produced["zeros"]["checks"].values()),
            "paths": [variant["files"]["nan"]["path"], variant["files"]["zeros"]["path"]],
        })
        print(f"[reproduced] {variant['id']}  {produced['nan']['n_dots']} dots  {changed:.3f}% changed  "
              f"rule={variant['selection_rule']}  sha256={produced['nan']['sha256'][:16]}...")

    # 6. Restore the strike-aligned PRUNE collar candidates
    aniso_field = aniso.build_strike_field(cat)
    for variant in aniso_receipt["variants"]:
        across = float(variant["across_px"])
        along = float(variant["along_px"])
        rows, cols = np.nonzero(r0)
        inside, _diag = aniso.collar_membership(rows, cols, aniso_field, across, along)
        collar = np.zeros_like(r0)
        collar[rows[inside], cols[inside]] = True
        kept = r0 & ~collar
        n_refill = int(collar.sum())
        pool = foot & h19 & ~cat & ~kept
        near = np.nonzero(pool & (aniso_field.dist <= across + 1e-9))
        inside_pool, _ = aniso.collar_membership(near[0], near[1], aniso_field, across, along)
        pool[near[0][inside_pool], near[1][inside_pool]] = False
        mask = kept | aniso.refill_mask(pool, rank, n_refill)
        if int(mask.sum()) != build.R0_DOTS:
            raise SystemExit(f"STOP: rebuilt {variant['id']} does not hold {build.R0_DOTS} dots")
        changed = variant["pct_changed"]
        produced = restore_files(
            variant, mask,
            lambda target, mode, m=mask, c=collar: aniso.audit_file(
                target, m, foot, cat, template, mode, c
            ),
        )
        report.append({
            "id": variant["id"], "axis": "PRUNE", "value_family": "strike-aligned collar",
            "across_px": across, "along_px": along,
            "n_dots": produced["nan"]["n_dots"], "pct_changed": round(changed, 6),
            "sha256": produced["nan"]["sha256"], "sha256_zeros": produced["zeros"]["sha256"],
            "bytes_match_recorded": True,
            "all_gate_checks": all(produced["nan"]["checks"].values()) and all(produced["zeros"]["checks"].values()),
            "paths": [variant["files"]["nan"]["path"], variant["files"]["zeros"]["path"]],
        })
        print(f"[reproduced] {variant['id']}  {produced['nan']['n_dots']} dots  {changed:.3f}% changed  "
              f"sha256={produced['nan']['sha256'][:16]}...")

    out = ROOT / "evidence" / "releases_restore_receipt.json"
    out.write_text(json.dumps({
        "schema_version": 1,
        "note": ("Local, gitignored candidate rasters re-emitted from pinned inputs. This is a "
                 "reproduction of the 18 core recorded BUILT (PRUNE, RELIEF, CONCENTRATION and MASS, "
                 "value) pairs present when this branch was cut, not a new experiment. Main's later "
                 "MASS-add, continuity and A5-refill families use their own generators. Each file must "
                 "equal the SHA-256 recorded in its build receipt and ledger/submissions.csv."),
        "prune_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_r0_variants.py"),
        "relief_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_relief_variants.py"),
        "concentration_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_concentration_variants.py"),
        "mass_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_mass_shadow.py"),
        "mass_high_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_mass_high_dose.py"),
        "aniso_prune_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_aniso_prune_variants.py"),
        "restore_script_sha256": build.sha256_file(Path(__file__)),
        "git_sha": build.git_sha(),
        "parent": {"id": build.PARENT, "r0_dots": build.R0_DOTS,
                   "r0_zeros_sha256": parent_stats["r0_rebuilt_zeros_sha256"],
                   "r0_nan_sha256": parent_stats["r0_rebuilt_nan_sha256"],
                   "r0_byte_identity_passed": parent_stats["r0_byte_identity_passed"],
                   "min_d_cat_px": parent_stats["r0_min_d_cat_px"],
                   "below_3px": parent_stats["r0_below_3px"]},
        "variants": report,
        "no_live_submission": True,
        "not_committed_to_git": True,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Reproduced {len(report)} candidate pairs -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
