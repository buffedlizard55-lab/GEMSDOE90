#!/usr/bin/env python3
"""Re-emit all recorded BUILT candidates (PRUNE + RELIEF) from pinned inputs, fail-closed.

Why this exists: `releases/*.tif` is gitignored (this repo is public and the brief
forbids committing competition rasters), so the built candidates do not survive a
fresh clone or a new sandbox. This script reproduces the *same* recorded
(AXIS, value) pairs -- it does not create a new experiment -- and refuses to
finish unless every re-emitted file matches the SHA-256 already recorded in
`evidence/build_receipt.json`, `evidence/relief_build_receipt.json`, and
`ledger/submissions.csv`.

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

import build_r0_variants as build  # noqa: E402
import build_relief_variants as relief_build  # noqa: E402

PRUNE_RECEIPT = ROOT / "evidence" / "build_receipt.json"
RELIEF_RECEIPT = ROOT / "evidence" / "relief_build_receipt.json"
LEDGER = ROOT / "ledger" / "submissions.csv"


def ledger_hashes() -> dict[str, tuple[str, str]]:
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        rows = [row for row in csv.DictReader(fh) if row.get("status") == "BUILT"]
    return {row["id"]: (row["sha256"], row["sha256_zeros"]) for row in rows}


def main() -> int:
    prune_receipt = json.loads(PRUNE_RECEIPT.read_text(encoding="utf-8"))
    relief_receipt = json.loads(RELIEF_RECEIPT.read_text(encoding="utf-8"))
    expected_ledger = ledger_hashes()
    recorded_ids = {v["id"] for v in prune_receipt["variants"]} | {v["id"] for v in relief_receipt["variants"]}
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

    out = ROOT / "evidence" / "releases_restore_receipt.json"
    out.write_text(json.dumps({
        "schema_version": 1,
        "note": ("Local, gitignored candidate rasters re-emitted from pinned inputs. This is a "
                 "reproduction of already-recorded (PRUNE, value) and (RELIEF, value) pairs, not a "
                 "new experiment. Each file must equal the SHA-256 recorded in its build receipt and "
                 "ledger/submissions.csv."),
        "prune_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_r0_variants.py"),
        "relief_generator_script_sha256": build.sha256_file(ROOT / "scripts" / "build_relief_variants.py"),
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
