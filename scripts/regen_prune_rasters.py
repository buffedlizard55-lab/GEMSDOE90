#!/usr/bin/env python3
"""Regenerate the prior session's three PRUNE release rasters byte-identically.

The PRUNE candidates (GEMSDOE90 session arena/bfdb587e, ledger rows status=BUILT) were
built in a previous sandbox whose ignored `releases/` GeoTIFFs did not persist to this
checkout. This script re-emits them with the recorded recipe (scripts/build_r0_variants.py)
and fails unless every byte hash matches the SHA-256 values already recorded in
ledger/submissions.csv. No ledger row is created, changed, or removed. The rasters stay
under ignored `releases/`; the human uploads at most one file per scored slot.

Run: `.venv/bin/python scripts/regen_prune_rasters.py`
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "releases"


def _load_build_r0() -> object:
    spec = importlib.util.spec_from_file_location("build_r0_variants", ROOT / "scripts" / "build_r0_variants.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


B = _load_build_r0()


def recorded_prune_rows() -> dict[float, dict]:
    rows = {}
    with (ROOT / "ledger" / "submissions.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("axis") or "").strip().upper() == "PRUNE" and (row.get("site") or "").strip() == "GEMSDOE90":
                for cutoff in (3.5, 4.5, 5.5):
                    if f"PRUNE{str(cutoff).replace('.', 'p')}px" in row.get("id", ""):
                        rows[cutoff] = row
    if set(rows) != {3.5, 4.5, 5.5}:
        raise ValueError(f"recorded PRUNE ledger rows not found: {sorted(rows)}")
    return rows


def main() -> int:
    rows = recorded_prune_rows()
    B.verify_manifest_inputs()
    template, foot, cat, r0, _stats = B.exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~cat)
    h19 = B.read_binary(B.DATA / B.PIN_PATHS["h19_5"], foot)
    rank = B.fifo_bfs_visit_rank(h19)
    OUT.mkdir(parents=True, exist_ok=True)
    for cutoff, row in sorted(rows.items()):
        kept = r0 & (distance > cutoff)
        removed = r0 & ~kept
        n_refill = int(removed.sum())
        eligible = h19 & foot & ~cat & (distance > cutoff) & ~kept
        ey, ex = np.nonzero(eligible)
        order = np.argsort(rank[ey, ex], kind="stable")[:n_refill]
        candidate = kept.copy()
        candidate[ey[order], ex[order]] = True
        if int(candidate.sum()) != B.R0_DOTS:
            raise ValueError(f"PRUNE {cutoff}: count mismatch")
        base = Path(row["id"])
        nan_path = OUT / f"{base.name}.tif"
        zeros_path = OUT / f"{base.name}-zeros.tif"
        B.emit(candidate, foot, template, base.name, "nan", nan_path)
        B.emit(candidate, foot, template, base.name, "zeros", zeros_path)
        got_nan = B.sha256_file(nan_path)
        got_zeros = B.sha256_file(zeros_path)
        if got_nan != row["sha256"] or got_zeros != row["sha256_zeros"]:
            nan_path.unlink(missing_ok=True)
            zeros_path.unlink(missing_ok=True)
            raise ValueError(
                f"PRUNE {cutoff} bytes do not match the ledger: "
                f"nan={got_nan} vs {row['sha256']}; zeros={got_zeros} vs {row['sha256_zeros']}"
            )
        audit = B.validate_file(nan_path, candidate, foot, cat, template, "nan")
        audit_z = B.validate_file(zeros_path, candidate, foot, cat, template, "zeros")
        print(f"[regenerated+verified] {base.name}  nan={got_nan[:12]}...  zeros={got_zeros[:12]}...")
        del audit, audit_z
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
