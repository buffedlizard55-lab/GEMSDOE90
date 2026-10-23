#!/usr/bin/env python3
"""Build MASS variants of R0 (`h33-h33-2-b2`) at fixed collar policy.

Session axis: MASS. Three files, one change each from the same parent:

  fifo20  drop 7,531 dots (20.0% of R0) from the bottom of the parent's own
          FIFO-BFS visit ranking -- the brief's literal MASS rule.
  uniq20  drop the same number of dots, but chosen by the metric algebra:
          lowest UNIQUE 300 m kernel credit against the parent's own support
          (spatially neutral; the FIFO tail is not).
  uniq30  the uniq rule at 30.0% of R0 (11,296 dots) -- dose response, and the
          smallest expected change that can plausibly clear the 0.01 live bar.

Every file first receives the mandatory collar normalisation (hard constraint 4:
d_cat >= 3 px, which removes 1,611 R0 dots that sit at 2.236 / 2.828 px). That
dose is identical in all three files, so the only differences between them are
(which dots) at equal mass -- fifo20 vs uniq20 -- and (how many) -- uniq20 vs
uniq30. No dot is added, no dot moves, spacing of retained dots is untouched.

Nothing here uses hidden truth, public-test labels or any score endpoint. The
only inputs are the pinned manifest files (SHA-256 re-verified). Rasters land in
gitignored `releases/`; never commit them (this repository is public).

Run:   .venv/bin/python scripts/build_mass_variants.py --build
Check: .venv/bin/python scripts/build_mass_variants.py --verify
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "MASS"
DATE = "20261023"
R0_DOTS = 37_654
R0_NAN_SHA = "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd"
COLLAR_PX = 3.0  # hard constraint 4: keep >= 3 px from the catalogue

# value -> (dose fraction of R0's dot count, selection rule, label)
VARIANTS = {
    "fifo20": (0.20, "fifo", "20% of R0 by lowest parent FIFO-BFS rank"),
    "uniq20": (0.20, "uniq", "20% of R0 by lowest unique 300 m kernel credit"),
    "uniq30": (0.30, "uniq", "30% of R0 by lowest unique 300 m kernel credit"),
}


def _load_base_module():
    spec = importlib.util.spec_from_file_location(
        "build_r0_variants", ROOT / "scripts" / "build_r0_variants.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B0 = _load_base_module()


def sha256_file(path: Path) -> str:
    return B0.sha256_file(path)


def git_sha() -> str:
    return B0.git_sha()


# --------------------------------------------------------------------------- #
# ranking and selection
# --------------------------------------------------------------------------- #
def unique_kernel_credit(dots: np.ndarray, support: np.ndarray) -> np.ndarray:
    """Unique triangular-kernel credit each dot supplies to `support`.

    Credit of dot i at support pixel g is k(|g-i|) = max(0, 1 - d/3). Under the
    metric's max-plus numerator T, pixel g is credited to its nearest dot only,
    so a dot's unique credit is the kernel mass of the support pixels for which
    it is the nearest dot. Neighbour-claimed pixels contribute 0. This is
    measured against the parent's own H19-5 support, i.e. the field the dots were
    thinned from; it uses no hidden labels and it is spatially neutral (every
    region has redundant and non-redundant dots).
    """
    height, width = support.shape
    index = np.full((height, width), -1, dtype=np.int32)
    ys, xs = np.nonzero(dots)
    index[ys, xs] = np.arange(len(ys), dtype=np.int32)
    dist, near = ndi.distance_transform_edt(index < 0, return_indices=True)
    k = np.maximum(0.0, 1.0 - dist / 3.0)
    owner = index[near[0], near[1]]
    take = (k > 0) & (owner >= 0) & support
    credit = np.bincount(owner[take], weights=k[take], minlength=len(ys))
    return credit, (ys, xs)


def select_drops(base_idx: np.ndarray, ys, xs, fifo_rank: np.ndarray, credit: np.ndarray,
                 rule: str, n: int) -> np.ndarray:
    """Deterministic drop order over the collar-normalised base; returns the first n."""
    sub_rank = fifo_rank[ys[base_idx], xs[base_idx]].astype(np.int64)
    sub_credit = credit[base_idx]
    if rule == "fifo":
        # brief-literal: last visited in the parent's own ranking first.
        order = np.lexsort((base_idx, -sub_rank))
    elif rule == "uniq":
        # least unique credit first; ties broken by the parent's own ranking (last
        # visited first), then by flat index, so the file is reproducible.
        order = np.lexsort((base_idx, -sub_rank, sub_credit))
    else:  # pragma: no cover - guarded by VARIANTS
        raise ValueError(rule)
    return base_idx[order[:n]]


def block_density_cv(dots: np.ndarray, foot: np.ndarray, block: int = 10) -> float:
    """CV of dot count per `block`-pixel (1 km) square over blocks with footprint."""
    hb, wb = dots.shape[0] // block, dots.shape[1] // block
    trim = dots[: hb * block, : wb * block].reshape(hb, block, wb, block)
    ft = foot[: hb * block, : wb * block].reshape(hb, block, wb, block)
    n = trim.sum(axis=(1, 3)).astype(float)
    has = ft.sum(axis=(1, 3)) > 0
    v = n[has]
    return float(v.std() / v.mean()) if v.mean() else 0.0


def patch_loss(dots: np.ndarray, support: np.ndarray) -> dict:
    """How much of the parent field's 8-connected structure loses every dot."""
    lab, n_comp = ndi.label(support, structure=np.ones((3, 3), dtype=np.uint8))
    kept = np.unique(lab[support & dots])
    sizes = np.bincount(lab.ravel())
    emptied = [c for c in range(1, n_comp + 1) if c not in set(kept.tolist())]
    return {
        "support_patches": int(n_comp),
        "patches_with_no_dot_after": len(emptied),
        "support_px_in_emptied_patches": int(sum(sizes[c] for c in emptied)),
    }


def model_prediction(n_drop: int, dti: float = 0.2778, g_lo: float = 20_000,
                     g_mid: float = 40_000, g_hi: float = 60_000,
                     r: float = 0.45, credit_on_truth: float = 0.5) -> dict:
    """MODEL sensitivity of DTI to removing `n_drop` dots, from the brief's algebra.

    DTI = T/(0.2T + 0.2(S-M) + 0.8|G|). Den is not observable (|G| is hidden), so
    it is reconstructed from the claimed DTI for a range of |G| and of the
    fractional penalty (S-M)/N = r. Two scenarios per |G|: every removed dot is
    >3 px from hidden truth (pure gain, q=1) or half of them sit on truth with
    mean credit 0.5 (q=0.5, loss).
    """
    N = R0_DOTS
    out = {}
    for label, g in (("g20k", g_lo), ("g40k", g_mid), ("g60k", g_hi)):
        den = (0.2 * r * N + 0.8 * g) / (1.0 - 0.2 * dti)
        T = dti * den
        gain = T / (den - 0.2 * n_drop) - dti
        lost_credit = 0.5 * n_drop * credit_on_truth
        loss = (T - lost_credit) / (den - 0.2 * 0.5 * n_drop) - dti
        out[label] = {"denominator_assumed": round(den, 1),
                      "all_dropped_dots_off_truth": round(gain, 4),
                      "half_dropped_dots_on_truth": round(loss, 4)}
    return {"scenarios": out, "authors_note": "MODEL projection, not a score; |G| and r are hidden."}


def mechanism_card(value: str, rule: str, n_drop: int, n_keep: int, credit_drop: float,
                   credit_keep: float, pred: dict, patches: dict) -> dict:
    common = (
        "DTI = T/(0.2T + 0.2(S-M) + 0.8|G|): a dot within 3 px of hidden truth adds up to 1.0 to T "
        "and only (1 - max k) to the penalty S-M, while a dot further than 3 px adds nothing to T "
        "and a full 1.0 to S-M. Mass is therefore not neutral: every non-paying dot costs 0.2 of "
        "denominator, and T is a max-plus quantity, so a dot whose kernel disc is already claimed by "
        "a neighbour supplies no unique credit at all. Both variants test that algebra at constant "
        "placement and constant collar."
    )
    if rule == "fifo":
        hypothesis = (
            "The brief-literal MASS rule: R0 carries mass that does not pay, and the parent's own "
            "FIFO-BFS thinning order is an acceptable proxy for 'least useful first'."
        )
        mechanism = common + (
            " Removal order is the reversed H19-5 FIFO-BFS visit rank (the documented d2.8 thinning "
            "tie-break). Measured against the parent's own support, the removed dots average "
            f"{credit_drop:.2f} unique kernel credit versus {credit_keep:.2f} for the dots kept: the "
            "FIFO tail is NOT a redundancy ordering, so this file is effectively a spatially "
            "arbitrary 20% mass cut. That is the point of pairing it with uniq20 at identical count."
        )
        predicted = "+0.001 DTI (MODEL; interval -0.012 to +0.009)"
        falsifier = (
            "Because the dropped set is nearly unbiased in unique credit, a live gain >= +0.01 here "
            "would mean mass matters and dot choice does not; a live drop <= -0.01 would mean R0's "
            "dots are paying and mass reduction is the wrong direction for every selection rule."
        )
    else:
        hypothesis = (
            "R0 carries redundant mass: the dots whose 300 m kernel disc is fully claimed by a "
            "neighbour cannot add to T, so removing them is free unless they sit on hidden truth, "
            "and each removal pays 0.2/Den of denominator."
        )
        mechanism = common + (
            " Selection is spatially neutral: unique triangular-kernel credit is computed for every "
            "dot against the parent's H19-5 support (the field it was thinned from), and only the "
            f"lowest-credit dots are dropped (dropped mean {credit_drop:.2f} vs kept {credit_keep:.2f} "
            "credit per dot). Ties follow the parent's FIFO rank, so the file is reproducible."
        )
        predicted = "+0.005 DTI (MODEL; interval -0.010 to +0.012)" if value == "uniq20" else \
                    "+0.007 DTI (MODEL; interval -0.015 to +0.018)"
        falsifier = (
            "A live drop <= -0.01 means the removed redundant dots were sitting on hidden truth and "
            "carrying T, i.e. the test faults are dense enough that redundancy at 3 px is not waste; "
            "a gain >= +0.01 supports pushing mass lower. |change| < 0.01 = no evidence."
        )
    return {
        "hypothesis": hypothesis,
        "mechanism": mechanism,
        "non_fault_mimic": (
            "Thin, isolated H19-5 support is produced as readily by road/rail corridors, DEM "
            "artefacts, lithologic contacts and drainage as by short fault strands, so 'redundant' "
            "and 'noise' are not the same set. Removing duplicate dots can equally delete the second "
            "strand of a real step-over, which the 3 px kernel cannot distinguish."
        ),
        "predicted_live_change": predicted,
        "model_sensitivity": pred,
        "spatial_side_effect": patches,
        "falsifier": falsifier,
        "structural_geologist_note": (
            "Check whether the removed dots concentrate on one structural trend or region; the "
            f"patch statistics say {patches['patches_with_no_dot_after']} of "
            f"{patches['support_patches']} support patches lose every dot."
        ),
    }


# --------------------------------------------------------------------------- #
# build / verify
# --------------------------------------------------------------------------- #
def build_variants(do_emit: bool = True) -> tuple[dict, dict, dict]:
    t0 = time.time()
    input_receipt = B0.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = B0.exact_parent_rebuild()
    if not (parent_stats["r0_byte_identity_passed"] and int(r0.sum()) == R0_DOTS):
        raise RuntimeError("parent R0 did not rebuild byte-identically; refusing to approximate it")

    distance = ndi.distance_transform_edt(~cat)
    support = B0.read_binary(DATA / B0.PIN_PATHS["h19_5"], foot)
    fifo_rank = B0.fifo_bfs_visit_rank(support)
    credit, (ys, xs) = unique_kernel_credit(r0, support)

    base = r0 & (distance >= COLLAR_PX)          # collar normalisation, identical in all files
    base_idx = np.flatnonzero(base[ys, xs])      # indices into the dot arrays
    n_collar = int(r0.sum() - base.sum())
    min_dcat = float(distance[base].min())

    results = []
    masks = {}
    for value, (dose, rule, label) in VARIANTS.items():
        n_drop = int(round(dose * R0_DOTS))
        drop = select_drops(base_idx, ys, xs, fifo_rank, credit, rule, n_drop)
        keep = np.ones(len(base_idx), dtype=bool)
        keep[np.searchsorted(base_idx, drop)] = False
        kept = base_idx[keep]
        candidate = np.zeros_like(r0)
        candidate[ys[kept], xs[kept]] = True
        if int(candidate.sum()) != len(base_idx) - n_drop:
            raise AssertionError("count drift")
        if np.any(candidate & cat):
            raise AssertionError("catalogue mass")
        removed = int(r0.sum() - candidate.sum())
        pct_changed = 100.0 * removed / R0_DOTS

        kernel3 = np.maximum(0.0, 1.0 - np.hypot(*np.mgrid[-3:4, -3:4]) / 3.0)
        thickness = ndi.convolve(support.astype(float), kernel3, mode="constant")
        drop_thick = float(thickness[ys[drop], xs[drop]].mean())
        keep_thick = float(thickness[ys[kept], xs[kept]].mean())
        drop_credit = float(credit[drop].mean())
        keep_credit = float(credit[kept].mean())
        pred = model_prediction(n_drop)
        patches = patch_loss(candidate, support)
        card = mechanism_card(value, rule, n_drop, len(kept), drop_credit, keep_credit, pred, patches)

        base_name = f"{PARENT}-{AXIS}{value}-{DATE}"
        # Emit to an ignored scratch dir first; only the build pass copies into releases/.
        tmp_dir = ROOT / ".cache" / "mass_emit"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        files = {}
        for mode in ("nan", "zeros"):
            tmp = tmp_dir / f"{base_name}-{mode}.tif"
            B0.emit(candidate, foot, template, base_name, mode, tmp)
            audit = B0.validate_file(tmp, candidate, foot, cat, template, mode)
            primary8 = (files["nan"]["sha256"][:8] if mode == "zeros"
                        else audit["sha256"][:8])
            # brief naming: <parent>-<axis><value>-<yyyymmdd>-<sha8>[-zeros].tif,
            # the twin carrying the PRIMARY's sha8 so the pair is visibly one id.
            final = OUT / f"{base_name}-{primary8}{'' if mode == 'nan' else '-zeros'}.tif"
            if do_emit:
                tmp.replace(final)
                audit = B0.validate_file(final, candidate, foot, cat, template, mode)
            else:
                audit["path"] = str(final.relative_to(ROOT))
                tmp.unlink(missing_ok=True)
            files[mode] = audit

        masks[value] = candidate
        results.append({
            "id": f"{base_name}-{files['nan']['sha256'][:8]}",
            "value": value,
            "label": label,
            "n_dots": int(candidate.sum()),
            "removed_dots": removed,
            "collar_dots": n_collar,
            "dose_dots": n_drop,
            "retained_dots": int(candidate.sum()),
            "added_dots": 0,
            "pct_changed_vs_r0": round(pct_changed, 6),
            "sha256": files["nan"]["sha256"],
            "sha256_zeros": files["zeros"]["sha256"],
            "min_catalogue_distance_px": files["nan"]["min_catalogue_distance_px"],
            "dropped_unique_credit_mean": round(drop_credit, 4),
            "kept_unique_credit_mean": round(keep_credit, 4),
            "dropped_local_support_mean": round(drop_thick, 4),
            "kept_local_support_mean": round(keep_thick, 4),
            "block1km_density_cv_before": round(block_density_cv(base, foot), 4),
            "block1km_density_cv_after": round(block_density_cv(candidate, foot), 4),
            "support_patches": patches,
            "predicted_change": card["predicted_live_change"],
            "model_sensitivity": pred,
            "mechanism_card": card,
            "files": files,
        })

    # ---- gates that span the whole set
    ledger_hashes = set()
    ledger_pairs = set()
    ledger_path = ROOT / "ledger" / "submissions.csv"
    if ledger_path.exists():
        with ledger_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("sha256"):
                    ledger_hashes.add(row["sha256"])
                if row.get("sha256_zeros"):
                    ledger_hashes.add(row["sha256_zeros"])
                if (row.get("axis") or "").upper() == AXIS:
                    ledger_pairs.add((row.get("parent"), row.get("value")))
    for v in results:
        for sha in (v["sha256"], v["sha256_zeros"]):
            if sha in ledger_hashes:
                raise ValueError(f"duplicate hash already in ledger: {sha}")
        if (PARENT, v["value"]) in ledger_pairs:
            raise ValueError(f"(AXIS, value) already reserved: {(AXIS, v['value'])}")
    if len({v["sha256"] for v in results}) != len(results):
        raise ValueError("two variants share a hash")

    receipt = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha(),
        "axis": AXIS,
        "parent": {"id": PARENT, "claimed_live_score": 0.2778, "evidence_class": "CLAIM",
                   "nan_sha256": R0_NAN_SHA, "dots": R0_DOTS, **parent_stats},
        "collar_policy": {
            "rule": "hard constraint 4: dots must satisfy d_cat >= 3.0 px",
            "dots_removed_by_collar": n_collar,
            "min_catalogue_distance_px_after_collar": min_dcat,
            "applies_to": "all three variants identically, so it is not the axis",
        },
        "ranking": {
            "fifo": "reversed H19-5 FIFO-BFS visit order (documented d2.8 thinning tie-break)",
            "uniq": "unique triangular-kernel credit vs the parent's own H19-5 support, measured "
                    "with a nearest-dot distance transform (exact under the metric's max-plus T)",
            "is_geological_probability": False,
        },
        "manifest": {"manifest_path": "registry/data_manifest.json",
                     "verified_count": len(input_receipt), "all_pins_rechecked": True},
        "generator": {
            "script": "scripts/build_mass_variants.py",
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "base_module": "scripts/build_r0_variants.py",
            "base_module_sha256": sha256_file(ROOT / "scripts" / "build_r0_variants.py"),
        },
        "variants": results,
        "no_live_submission": True,
        "elapsed_s": round(time.time() - t0, 2),
    }
    return receipt, masks, {"template": template, "foot": foot, "cat": cat, "r0": r0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    receipt, _masks, _ctx = build_variants(do_emit=args.build)
    path = ROOT / "evidence" / "build_receipt_mass.json"

    if args.build:
        path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        for v in receipt["variants"]:
            print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed_vs_r0']:.3f}% changed, "
                  f"sha256={v['sha256']}")
        print(f"receipt -> {path.relative_to(ROOT)}")
        return 0

    if not path.is_file():
        print("no build receipt to verify")
        return 2
    recorded = json.loads(path.read_text())
    by_value = {v["value"]: v for v in receipt["variants"]}
    for old in recorded["variants"]:
        new = by_value[old["value"]]
        for key in ("sha256", "sha256_zeros", "n_dots", "pct_changed_vs_r0"):
            if old[key] != new[key]:
                raise ValueError(f"{old['value']} {key} mismatch: {old[key]} != {new[key]}")
        for enc in ("nan", "zeros"):
            disk = ROOT / old["files"][enc]["path"]
            if not disk.is_file():
                raise FileNotFoundError(f"recorded raster missing: {disk}")
            audit = B0.validate_file(disk, _masks[old["value"]], _ctx["foot"], _ctx["cat"],
                                     _ctx["template"], enc)
            if audit["sha256"] != old["files"][enc]["sha256"]:
                raise ValueError(f"{disk.name} on-disk SHA-256 differs from the receipt")
    print(f"verified {len(recorded['variants'])} MASS variants: recomputed masks, on-disk bytes, "
          "and re-emitted bytes all match the receipt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
