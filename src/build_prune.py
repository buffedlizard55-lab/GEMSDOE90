"""AXIS=PRUNE session builder (chosen 2026-10-23; see SLOT_PLAN.md).

Dose-response around R0's own defining edit, all count-held at R0's n_dots and
all derived from the common PRE-PRUNE parent, so the only difference between
variants is the catalogue-distance threshold:

  P1  : prune <=1 px, drop lowest-ranked back to n_R0        (tests: was <=2 too aggressive?)
  P3  : prune <=3 px, refill highest-ranked (dist>3) to n_R0 (tests: push the incumbent direction)
  P3nr: prune <=3 px, NO refill                              (control: separates distance from mass)

Hard stops (brief s5/s6): unverified manifest -> stop; rebuilding R0 as
prune<=2 of the pre-prune dots must reproduce the R0 dot set EXACTLY (under
Euclidean or Chebyshev distance) -> otherwise stop, never approximate the
parent; sha256 already in ledger -> refuse; format gate must pass on the
file re-read from disk.

Usage: python -m src.build_prune
Outputs: releases/<id>.tif (NaN outside) + <id>-zeros.tif, rows appended to
ledger/submissions.csv with status BUILT. Rasters are gitignored (public repo).
"""
from __future__ import annotations

import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import rasterio

from src import manifest
from src.prune import distance_field, dots_of, drop_lowest_ranked, pct_changed, prune_le, refill, render
from src.validate import footprint_mask, validate

ROOT = Path(__file__).resolve().parents[1]
PARENT_ID = "h33-h33-2-b2"
REQUIRED = ["sample_submission", "r0_raster", "catalogue_raster", "preprune_dots", "ranked_candidates"]
PREDICTED = {  # MODEL, see docs/MECHANISM_CARDS.md; <0.01 live = no evidence
    "le1": "-0.005..+0.005 (MODEL)",
    "le3": "+0.000..+0.010 (MODEL)",
    "le3nr": "-0.005..+0.005 (MODEL)",
}


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        return ds.read(1)


def load_ranked(path: Path) -> list[tuple[int, int, int]]:
    out = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            out.append((int(row["row"]), int(row["col"]), int(row["rank"])))
    if not out:
        raise SystemExit("STOP: ranked_candidates.csv is empty")
    return out


def write_raster(array: np.ndarray, sample_path: Path, out_path: Path) -> None:
    with rasterio.open(sample_path) as ref:
        profile = ref.profile.copy()
    profile.update(dtype="float32", count=1, nodata=np.nan)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as ds:
        ds.write(array.astype("float32"), 1)


def ledger_shas() -> set[str]:
    p = ROOT / "ledger" / "submissions.csv"
    if not p.exists():
        return set()
    with open(p, newline="") as fh:
        return {row["sha256"] for row in csv.DictReader(fh) if row.get("sha256")}


def append_ledger(row: dict) -> None:
    p = ROOT / "ledger" / "submissions.csv"
    fields = list(row.keys())
    exists = p.exists()
    if exists:
        with open(p, newline="") as fh:
            fields = next(csv.reader(fh))
    with open(p, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writerow({k: row.get(k, "") for k in fields})


def main() -> int:
    paths = manifest.require(REQUIRED)  # hard stop if anything is missing/unpinned
    sample, inside = paths["sample_submission"], footprint_mask(str(paths["sample_submission"]))
    catalogue = read(paths["catalogue_raster"])
    r0_dots = dots_of(read(paths["r0_raster"]))
    pre_dots = dots_of(read(paths["preprune_dots"]))
    ranked = load_ranked(paths["ranked_candidates"])
    n_r0 = len(r0_dots)
    print(f"parent {PARENT_ID}: n_dots={n_r0}; pre-prune dots={len(pre_dots)}; ranked candidates={len(ranked)}")

    # --- Rebuild R0 exactly, or stop. Probe both plausible distance metrics. ---
    dist, metric_used = None, None
    for metric in ("euclidean", "chebyshev"):
        d = distance_field(catalogue, metric)
        if prune_le(pre_dots, d, 2) == r0_dots:
            dist, metric_used = d, metric
            break
    if dist is None:
        print(
            "STOP: prune<=2 of preprune_dots does not reproduce the R0 dot set under "
            "Euclidean or Chebyshev distance. The parent recipe (distance definition, "
            "tie-handling, or dot source) differs from the brief's description. "
            "Never approximate the parent (brief s5) -- supply the recorded recipe.",
            file=sys.stderr,
        )
        return 2
    print(f"R0 rebuild: EXACT match with metric={metric_used}")

    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    seen = ledger_shas()
    variants: dict[str, set[tuple[int, int]]] = {}
    p1 = prune_le(pre_dots, dist, 1)
    variants["le1"] = drop_lowest_ranked(p1, ranked, n_r0) if len(p1) > n_r0 else refill(p1, ranked, dist, 1, inside, n_r0)
    p3 = prune_le(pre_dots, dist, 3)
    variants["le3nr"] = p3
    variants["le3"] = refill(p3, ranked, dist, 3, inside, n_r0)

    for value, dots in variants.items():
        pct = pct_changed(dots, r0_dots)
        stamp = date.today().strftime("%Y%m%d")
        tmp_id = f"{PARENT_ID}-prune{value}-{stamp}"
        out = ROOT / "releases" / f"{tmp_id}.tif"
        write_raster(render(dots, inside, outside_nan=True), sample, out)
        sha = manifest.sha256_of(out)
        if sha in seen:
            out.unlink()
            print(f"{tmp_id}: sha256 already in ledger -- refused (exact repeat)")
            continue
        vid = f"{tmp_id}-{sha[:8]}"
        final = out.rename(ROOT / "releases" / f"{vid}.tif")
        zeros = ROOT / "releases" / f"{vid}-zeros.tif"
        write_raster(render(dots, inside, outside_nan=False), sample, zeros)
        rep = validate(str(final), str(sample), str(paths["catalogue_raster"]))
        repz = validate(str(zeros), str(sample), str(paths["catalogue_raster"]), zeros_outside=True)
        status = "BUILT" if (rep["pass"] and repz["pass"]) else "BUILT_FORMAT_FAIL"
        if not (1.0 <= pct <= 50.0):
            status += "_OUTSIDE_1_50_PCT"  # brief s5: still recorded, not slot-worthy as-is
        append_ledger({
            "id": vid, "parent": PARENT_ID, "axis": "PRUNE", "value": value,
            "n_dots": len(dots), "pct_changed": f"{pct:.2f}", "sha256": sha, "sha8": sha[:8],
            "status": status, "evidence": "MODEL", "claimed_score": "", "receipt_score": "",
            "receipt_date": "", "predicted_change": PREDICTED[value], "site": "GEMSDOE90",
            "name": f"{vid}.tif", "encoding": "NaN-outside (+ -zeros fallback)",
            "notes": f"metric={metric_used}; count-held={value != 'le3nr'}; git={git_sha[:8]}; seed=deterministic",
        })
        print(f"{vid}: n={len(dots)} pct_changed={pct:.2f} format_pass={rep['pass'] and repz['pass']} status={status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
