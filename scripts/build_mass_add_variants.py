#!/usr/bin/env python3
"""Build the AXIS=MASS add rungs from R0: region-even, block-budgeted additions.

Three arms, one parent (byte-identical rebuild of `h33-h33-2-b2`), one mechanism:

  add10pctBlocknext  3,765 dots (+10 %)  parent's FIFO rank inside each 5 km block
  add20pctBlocknext  7,531 dots (+20 %)  same rule, deeper dose
  add10pctGapmax     3,765 dots (+10 %)  greatest marginal kernel credit per block

Why the add half of the dose curve: every valid MASS rung in the ledger is a deletion.
The FIFO-ranked add rungs were withdrawn because the global visit order puts every
added cell in a northern strip (IR90-20). Quotas proportional to each block's own R0
count (capped at +50 %, zero where R0 has no dots) make the same ranking region-even.

What the arms decide
--------------------
* `add10pctBlocknext` tests the brief's literal recipe ("add the next-ranked 10 %")
  with the geography repaired.
* `add20pctBlocknext` gives the dose slope.
* `add10pctGapmax` is the placement contrast at matched dose and matched geography: if
  additions can pay at all, they pay where the kernel has room. If gapmax is also null,
  the H19-5 support is saturated at R0's density and mass placement is dead.

Run:  .venv/bin/python scripts/build_mass_add_variants.py --build
      .venv/bin/python scripts/build_mass_add_variants.py --verify
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

import build_r0_variants as base_build  # noqa: E402  (audited exact-rebuild path)
from src import mass_add  # noqa: E402
from src.dti import dti_from_components  # noqa: E402
from src.relief import block_density_cv  # noqa: E402
from src.validate import validate as format_validate  # noqa: E402

PARENT = "h33-h33-2-b2"
AXIS = "MASS"
DATE = "20261023"
R0_DOTS = 37_654
DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
RECEIPT = ROOT / "evidence" / "mass_add_receipt.json"
SEED = 20261023
R0_NAN_SHA = base_build.R0_NAN_SHA
R0_ZEROS_SHA = base_build.R0_ZEROS_SHA
SGMC_PIN = "external/derived_sgmc_faults_100m_u8.tif"

# (tag, dose fraction, selection rule)
VARIANT_SPECS = (
    ("add10pctBlocknext", 0.10, "blocknext"),
    ("add20pctBlocknext", 0.20, "blocknext"),
    ("add10pctGapmax", 0.10, "gapmax"),
)


def n_add_for(dose: float) -> int:
    return int(round(dose * R0_DOTS))


def value_string(tag: str, n_add: int, rule: str) -> str:
    rule_txt = (
        "parent FIFO rank per 5km block quota propto R0 count, cap +50%/block"
        if rule == "blocknext"
        else "max marginal R=3px kernel credit per 5km block quota propto R0 count, cap +50%/block"
    )
    return f"tag={tag}; add {n_add} dots (+{100.0 * n_add / R0_DOTS:.4g}% of R0) on H19-5; {rule_txt}; added d_cat>=3px"


def mechanism_card(tag: str, rule: str, n_add: int, pred: dict, report: dict) -> dict:
    placement = (
        "the parent's own thinning rank (the cells its d2.8 recipe suppressed, earliest visit first) "
        "inside a per-block quota"
        if rule == "blocknext"
        else "the cells with the largest remaining R=3 px kernel credit inside a per-block quota"
    )
    return {
        "hypothesis": (
            f"R0 is under-massed, not over-massed, at the margin: {n_add} additional unit dots placed on the "
            "parent's own H19-5 evidence, following the parent's regional distribution, should add more truth "
            "credit T than the 0.2 mass each dot costs, raising DTI."
        ),
        "mechanism": (
            "DTI = T/(0.2T + 0.2(S-M) + 0.8|G|). For one added unit dot dDTI = [E(D-0.2T) - 0.2T(1-c)]/D^2, so "
            "an addition pays iff its exclusive truth credit E exceeds ~0.056 (0.2*DTI at the claimed 0.2778). "
            "Additions can never reduce T (T is a max over dots), so unlike a deletion the failure mode is bounded "
            "by the mass penalty alone. Placement here is " + placement + "."
        ),
        "non_fault_confounder": (
            "The H19-5 field is a topographic/structural-ridge response, not a fault map: ridges from lithologic "
            "contacts, erosion-resistant beds, drainage margins and shoreline features carry the same signature, and "
            "the parent lineage's 0.2778 CLAIM cannot separate them. If the field is < 11% precise for new faults, "
            "the mass penalty dominates and the addition loses; if the belt is largely non-fault ridge, R0 is already "
            "over-placed there and the gapmax arm simply re-covers the same ridges more evenly."
        ),
        "predicted_live_change": (
            f"{pred['point']:+.4f} DTI point (MODEL; bracket {pred['low']:+.4f} to {pred['high']:+.4f}; not a score)"
        ),
        "falsifier": (
            "Paired same-week live receipt against R0: Delta <= -0.010 falsifies the under-massed hypothesis at this "
            "dose and supports the deletion ladder; |Delta| < 0.010 is no evidence under the session rule. The "
            "decisive contrast is gapmax10 vs blocknext10 at identical dose and geography: gapmax >= +0.010 with "
            "blocknext null means placement (kernel room) matters; both null means the support is saturated."
        ),
        "structural_geologist_note": (
            f"Additions are {100.0 * n_add / R0_DOTS:.1f}% of the parent, all on the corroborated H19-5 ridge "
            f"support, all >= 3 px from mapped USGS/INGENIOUS traces, quota-proportional to the parent's own 5 km "
            f"block counts (p05 share {report['add_share_p05']:.3f}, max {report['add_share_max']:.3f}). Read the "
            "rendered file as a denser sampling of the same ridge network, not as a new structural interpretation."
        ),
    }


def check_reservations(allow_rebuild: bool = False) -> dict[str, str]:
    """Fail closed on a reused (MASS, tag), unless it is an asserted byte-identical rebuild."""
    reserved: dict[str, str] = {}
    res_path = ROOT / "ledger" / "experiment_reservations.json"
    if res_path.is_file():
        res = json.loads(res_path.read_text(encoding="utf-8"))
        taken = set(res.get("mass_add_reservations", {}).get("occupied_tags", []))
        if RECEIPT.is_file():
            reserved = {v["tag"]: v["sha256"] for v in json.loads(RECEIPT.read_text(encoding="utf-8"))["variants"]}
        for tag, _dose, _rule in VARIANT_SPECS:
            if tag in taken and not (allow_rebuild and tag in reserved):
                raise ValueError(f"duplicate experiment reservation: (MASS, {tag}) already reserved")
    ledger_path = ROOT / "ledger" / "submissions.csv"
    if ledger_path.is_file():
        with ledger_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                val = row.get("value") or ""
                for tag, _dose, _rule in VARIANT_SPECS:
                    if tag in val and not allow_rebuild:
                        raise ValueError(f"duplicate experiment in ledger/submissions.csv: (MASS, {tag})")
    return reserved


def ledger_hashes(exclude_ids: set[str] | None = None) -> set[str]:
    exclude = exclude_ids or set()
    out: set[str] = set()
    path = ROOT / "ledger" / "submissions.csv"
    if path.is_file():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("id") in exclude:
                    continue
                for col in ("sha256", "sha256_zeros"):
                    val = (row.get(col) or "").strip()
                    if val:
                        out.add(val)
    return out


def sequential_marginal_gains(
    ys: np.ndarray, xs: np.ndarray, support: np.ndarray, base: np.ndarray, radius: int = 3
) -> np.ndarray:
    """Exact marginal support credit of each added dot in its own insertion order."""
    sup = np.asarray(support, dtype=bool)
    cov = mass_add.coverage(base, sup, radius)
    offs = mass_add.kernel_offsets(radius)
    h, w = cov.shape
    out = np.zeros(ys.size, dtype=np.float64)
    for i in range(ys.size):
        y, x = int(ys[i]), int(xs[i])
        g = 0.0
        for dy, dx, k in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and sup[yy, xx]:
                d = k - cov[yy, xx]
                if d > 0.0:
                    g += d
        out[i] = g
        for dy, dx, k in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and sup[yy, xx] and k > cov[yy, xx]:
                cov[yy, xx] = k
    return out


def validate_candidate(
    path: Path,
    expected: np.ndarray,
    r0: np.ndarray,
    foot: np.ndarray,
    cat: np.ndarray,
    dist_cat: np.ndarray,
    sample_path: Path,
    cat_path: Path,
    sample_profile: dict,
    mode: str,
    support: np.ndarray | None = None,
) -> dict:
    fmt = format_validate(str(path), str(sample_path), str(cat_path), zeros_outside=(mode == "zeros"))
    if not fmt["pass"]:
        raise ValueError(f"src.validate failed for {path.name}: {fmt['fails']}")
    with rasterio.open(path) as src:
        a = src.read(1)
        profile = src.profile
        crs, transform = src.crs, src.transform
    disk = (a > 0.5) & foot
    added = disk & ~r0
    retained = disk & r0
    checks = {
        "src_validate_gate_pass": bool(fmt["pass"]),
        "crs_matches_sample": crs == sample_profile["crs"],
        "transform_matches_sample": transform == sample_profile["transform"],
        "shape_matches_sample": a.shape == (sample_profile["height"], sample_profile["width"]),
        "float32_single_band": profile["dtype"] == "float32" and profile["count"] == 1,
        "inside_foot_finite": bool(np.isfinite(a[foot]).all()),
        "inside_foot_range_0_1": bool(np.all((a[foot] >= 0.0) & (a[foot] <= 1.0))),
        "outside_encoding_valid": bool(np.isnan(a[~foot]).all()) if mode == "nan" else bool(np.all(a[~foot] == 0.0)),
        "exact_expected_mask_after_disk_read": bool(np.array_equal(disk, expected)),
        "zero_catalogue_mass": not bool(np.any(disk & cat)),
        "added_dots_min_cat_dist_ge_3px": bool(float(dist_cat[added].min()) >= 3.0) if added.any() else True,
        "retained_dots_preserve_r0_collar_gt_2px": bool(float(dist_cat[retained].min()) > 2.0),
        "added_dots_on_h19_support": bool(np.all(support[added])) if support is not None else True,
        "file_re_read_from_disk": True,
    }
    if not all(checks.values()):
        raise ValueError(f"validator failed for {path.name}: {[k for k, v in checks.items() if not v]}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": base_build.sha256_file(path),
        "bytes": path.stat().st_size,
        "encoding": mode,
        "n_dots": int(disk.sum()),
        "min_catalogue_distance_all_dots_px": round(float(dist_cat[disk].min()), 6),
        "min_catalogue_distance_added_dots_px": round(float(dist_cat[added].min()), 6) if added.any() else None,
        "added_dots_below_3px": int((added & (dist_cat < 3.0)).sum()),
        "inherited_r0_dots_below_3px": int((retained & (dist_cat < 3.0)).sum()),
        "checks": checks,
    }


def build(allow_rebuild: bool = False) -> dict:
    t0 = time.time()
    reserved = check_reservations(allow_rebuild) if not allow_rebuild else check_reservations(True)
    input_receipt = base_build.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    rank = base_build.fifo_bfs_visit_rank(h19)

    if not np.all(~r0 | support):
        raise ValueError("R0 has pixels outside the off-catalogue H19-5 support")

    eligible = support & ~r0 & (dist_cat >= 3.0)
    if int(eligible.sum()) < max(n_add_for(d) for _t, d, _r in VARIANT_SPECS):
        raise ValueError("eligible addition pool smaller than the deepest requested dose")

    counts = mass_add.block_counts(r0)
    capacity = mass_add.block_counts(eligible)
    r0_cv_5km = block_density_cv(r0, foot, block_px=50)
    r0_cv_10km = block_density_cv(r0, foot, block_px=100)

    with rasterio.open(DATA / SGMC_PIN) as ds:
        sgmc = (ds.read(1) > 0) & foot & (dist_cat > 3.0)
    cov_r0 = mass_add.coverage(r0, support)
    sgmc_r0_credit = float(cov_r0[sgmc].sum())

    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]
    prior_ids = set()
    if allow_rebuild and RECEIPT.is_file():
        prior_ids = {v["id"] for v in json.loads(RECEIPT.read_text(encoding="utf-8"))["variants"]}
    seen = ledger_hashes(exclude_ids=prior_ids)
    OUT.mkdir(parents=True, exist_ok=True)

    variants = []
    candidate_masks = {"R0": r0}
    for tag, dose, rule in VARIANT_SPECS:
        n_add = n_add_for(dose)
        quotas = mass_add.allocate_quotas(counts, capacity, n_add)
        if int(quotas.sum()) != n_add:
            raise AssertionError("quota sum mismatch")
        if rule == "blocknext":
            add_y, add_x = mass_add.fifo_pick_within_blocks(eligible, rank, quotas)
            gains = sequential_marginal_gains(add_y, add_x, support, r0)
        else:
            add_y, add_x, gains = mass_add.gapmax_pick_within_blocks(eligible, support, r0, quotas)
        if add_y.size != n_add:
            raise AssertionError(f"{tag}: {add_y.size} picks != {n_add} requested")
        added_mask = np.zeros_like(r0)
        added_mask[add_y, add_x] = True
        if int(added_mask.sum()) != n_add:
            raise AssertionError(f"{tag}: duplicate picks")
        if np.any(added_mask & (dist_cat < 3.0)):
            raise AssertionError(f"{tag}: an addition violates the 3 px catalogue collar")
        if np.any(added_mask & ~support):
            raise AssertionError(f"{tag}: an addition is off the H19-5 support")
        candidate = r0 | added_mask
        if int(candidate.sum()) != R0_DOTS + n_add:
            raise AssertionError(f"{tag}: count mismatch")

        full_credit = mass_add.full_support_credit(add_y, add_x, support)
        pred = mass_add.prediction_bracket(gains, full_credit)
        report = mass_add.addition_report(added_mask, r0)
        report["passes_addition_evenness_gate"] = mass_add.addition_evenness_gate(report)
        if not report["passes_addition_evenness_gate"]:
            raise ValueError(f"{tag} fails the addition evenness gate: {report}")

        cv_after_5km = block_density_cv(candidate, foot, block_px=50)
        cv_after_10km = block_density_cv(candidate, foot, block_px=100)
        cov_cand = mass_add.coverage(candidate, support)
        sgmc_credit = float(cov_cand[sgmc].sum())
        card = mechanism_card(tag, rule, n_add, pred, report)

        slug = f"{PARENT}-MASS{tag}-{DATE}"
        audits = {}
        shas = {}
        nam = ""
        for mode in ("nan", "zeros"):
            tmp = ROOT / ".cache" / "candidate_bytes" / f"{slug}-{mode}.tif"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            base_build.emit(candidate, foot, template, slug, mode, tmp)
            if mode == "nan":
                nam = base_build.sha256_file(tmp)[:8]
            final = OUT / f"{slug}-{nam}{'' if mode == 'nan' else '-zeros'}.tif"
            final.parent.mkdir(parents=True, exist_ok=True)
            tmp.replace(final)
            audit = validate_candidate(final, candidate, r0, foot, cat, dist_cat, sample_path, cat_path, template, mode, support)
            audits[mode] = audit
            shas[mode] = audit["sha256"]
        for mode in ("nan", "zeros"):
            if shas[mode] in seen:
                raise ValueError(f"{tag}: sha256 already present in ledger ({mode})")
            seen.add(shas[mode])
        if shas["nan"] == R0_NAN_SHA or shas["zeros"] == R0_ZEROS_SHA:
            raise ValueError(f"{tag}: candidate is byte-identical to R0")

        if allow_rebuild and tag in reserved and reserved[tag] != shas["nan"]:
            raise ValueError(
                f"{tag}: rebuild is not byte-identical to the reserved raster "
                f"({shas['nan']} != {reserved[tag]}); refusing to create a new experiment under a used tag"
            )
        vid = f"{slug}-{shas['nan'][:8]}"
        pct_changed = 100.0 * float(n_add) / float(R0_DOTS)
        predicted = f"{pred['point']:+.4f} DTI (MODEL; bracket {pred['low']:+.4f} to {pred['high']:+.4f}; not a score)"
        form_note = (
            f"{PARENT}; MASS add {100.0 * n_add / R0_DOTS:.0f}% ({n_add}d) {rule}; "
            f"pred {pred['point']:+.3f} DTI MODEL"
        )
        if len(form_note) > 140:
            raise ValueError(f"{tag}: form note too long ({len(form_note)} chars)")
        variants.append(
            {
                "id": vid,
                "tag": tag,
                "parent": PARENT,
                "axis": AXIS,
                "value": value_string(tag, n_add, rule),
                "selection_rule": rule,
                "dose_fraction": dose,
                "n_added": n_add,
                "n_dots": int(candidate.sum()),
                "pct_changed": pct_changed,
                "sha256": shas["nan"],
                "sha256_zeros": shas["zeros"],
                "status": "BUILT",
                "predicted_change": predicted,
                "predicted_model": pred,
                "form_note": form_note,
                "files": audits,
                "parent_diff": {
                    "n_added": n_add,
                    "n_removed": 0,
                    "retained_dots": R0_DOTS,
                    "symmetric_difference_px": n_add,
                    "pct_changed_symmetric": pct_changed,
                    "mean_marginal_support_credit_per_added_dot": round(float(gains.mean()), 4),
                    "median_marginal_support_credit_per_added_dot": round(float(np.median(gains)), 4),
                    "sum_marginal_support_credit": round(float(gains.sum()), 2),
                    "mean_full_support_credit_per_added_dot": round(float(full_credit.mean()), 4),
                    "min_catalogue_distance_added_px": round(float(dist_cat[added_mask].min()), 6),
                    "added_below_3px": int((added_mask & (dist_cat < 3.0)).sum()),
                    "block_density_cv_5km_before": round(r0_cv_5km, 6),
                    "block_density_cv_5km_after": round(cv_after_5km, 6),
                    "block_density_cv_10km_before": round(r0_cv_10km, 6),
                    "block_density_cv_10km_after": round(cv_after_10km, 6),
                },
                "addition_report": report,
                "proxy_reports": {
                    "sgmc_off_catalogue_credit": {
                        "evidence_class": "PROXY",
                        "status": "REPORT ONLY (never a gate, never a live score)",
                        "r0_credit": round(sgmc_r0_credit, 4),
                        "candidate_credit": round(sgmc_credit, 4),
                        "delta": round(sgmc_credit - sgmc_r0_credit, 4),
                        "n_pixels": int(sgmc.sum()),
                    },
                    "catalogue_hide_recover": {
                        "evidence_class": "PROXY",
                        "status": "REPORT ONLY (never a gate, never a live score)",
                        "delta_vs_r0": 0.0,
                        "reason": (
                            "Analytic, not measured: every added dot has Euclidean d_cat >= 3.0 px and the kernel "
                            "radius is 3 px, so additions supply exactly zero kernel credit to any known catalogue "
                            "pixel. The instrument is blind to this axis by construction (same caveat as IR90-19)."
                        ),
                    },
                },
                "mechanism_card": card,
            }
        )
        candidate_masks[vid] = candidate

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": base_build.git_sha(),
        "generator_script": "scripts/build_mass_add_variants.py",
        "generator_script_sha256": base_build.sha256_file(Path(__file__)),
        "axis": AXIS,
        "axis_direction": "ADD (region-even block-budgeted)",
        "session_note": (
            "AXIS chosen by the agent as MASS/ADD: the only untested half of the dose curve in this ledger, and the "
            "only arm whose failure mode is bounded by the mass penalty alone (T is a max over dots)."
        ),
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": R0_ZEROS_SHA,
            "nan_sha256": R0_NAN_SHA,
            **parent_stats,
            "block_density_cv_5km": round(r0_cv_5km, 6),
            "block_density_cv_10km": round(r0_cv_10km, 6),
        },
        "operator": {
            "block_px": mass_add.BLOCK_PX,
            "block_km": mass_add.BLOCK_PX * 0.1,
            "cap_fraction_per_block": mass_add.CAP_FRAC,
            "quota_rule": "quota_b = n_add * r0_dots_b / R0_DOTS, largest remainder, capped at min(capacity_b, 0.5*r0_dots_b); zero where r0_dots_b = 0",
            "eligibility": "H19-5 support & footprint & ~catalogue & Euclidean d_cat >= 3.0 px & unoccupied",
            "blocknext_rule": "ascending parent FIFO-BFS visit rank within each block quota",
            "gapmax_rule": "greedy maximum marginal R=3 px triangular-kernel credit on the support within each block quota",
            "model": {
                "algebra": "dDTI_i = [E_i(D-0.2T) - 0.2T(1-c_i)]/D^2 with E_i = precision * marginal_support_credit_i, c_i = precision * full_support_credit_i",
                "support_precision_note": (
                    "precision = P(a support pixel is a new-fault truth pixel); point 0.20 is the value implied by "
                    "T/(support_px*0.7) under the point parent fit, bracketed 0.10-0.35"
                ),
                "point_fit": parent_fit_point(),
            },
        },
        "manifest": {
            "manifest_path": "registry/data_manifest.json",
            "verified_count": len(input_receipt),
            "all_pins_rechecked": True,
            "files": input_receipt,
        },
        "proxies": {
            "catalogue_hide_recover": "analytically zero for additions (d_cat >= 3 px, R = 3 px) - REPORT ONLY",
            "sgmc_control_r0_credit": round(sgmc_r0_credit, 4),
            "leakage_canary": "not re-run this session: no new feature was introduced (additions are placed on the existing H19-5 support)",
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
        "not_committed_to_git": True,
    }


def parent_fit_point() -> dict:
    fit = mass_add.parent_fit(0.2778, R0_DOTS, 65000, 0.44)
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in fit.items()}


def update_ledgers_and_reservations(result: dict) -> None:
    ledger_path = ROOT / "ledger" / "submissions.csv"
    with ledger_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        existing = list(reader)

    new_ids = {v["id"] for v in result["variants"]}
    rows = [r for r in existing if r.get("id") not in new_ids]
    for v in result["variants"]:
        rows.append(
            {
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
                    f"add-only rung: {v['n_added']} dots added, 0 removed; quota-proportional to parent 5km block "
                    f"counts (p05 share {v['addition_report']['add_share_p05']:.3f}, max "
                    f"{v['addition_report']['add_share_max']:.3f}); receipt_score/date filled by human; agent never submits"
                ),
            }
        )
    with ledger_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    res_path = ROOT / "ledger" / "experiment_reservations.json"
    res = json.loads(res_path.read_text(encoding="utf-8")) if res_path.is_file() else {}
    res["mass_add_reservations"] = {
        "checked_utc": "2026-10-23",
        "axis": AXIS,
        "direction": "ADD",
        "parent": PARENT,
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "note": (
            "No prior MASS add row exists in this ledger (the three FIFO add/drop rungs are WITHDRAWN, IR90-20). "
            "Sibling GEMSDOE84/86/87 'MASS +10%/+20%' rows use the global FIFO order and are not region-even; "
            "these values are string- and mechanism-distinct (per-block quotas propto R0 count). Repeat builds of "
            "these (MASS, tag) pairs fail closed."
        ),
    }
    res_path.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    cards_path = ROOT / "ledger" / "mechanism_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8")) if cards_path.is_file() else {}
    cards["mass_add"] = {
        "session": "2026-10-23e",
        "axis": AXIS,
        "direction": "ADD",
        "parent": PARENT,
        "variants": [
            {"id": v["id"], "tag": v["tag"], "value": v["value"], "mechanism_card": v["mechanism_card"]}
            for v in result["variants"]
        ],
    }
    cards_path.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def verify_all() -> int:
    input_receipt = base_build.verify_manifest_inputs()
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    eligible = support & ~r0 & (dist_cat >= 3.0)
    counts = mass_add.block_counts(r0)
    capacity = mass_add.block_counts(eligible)
    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]
    for v in receipt["variants"]:
        doses = dict((t, d) for t, d, _r in VARIANT_SPECS)
        rule = v["selection_rule"]
        quotas = mass_add.allocate_quotas(counts, capacity, n_add_for(doses[v["tag"]]))
        if rule == "blocknext":
            ay, ax = mass_add.fifo_pick_within_blocks(eligible, base_build.fifo_bfs_visit_rank(h19), quotas)
        else:
            ay, ax, _g = mass_add.gapmax_pick_within_blocks(eligible, support, r0, quotas)
        added = np.zeros_like(r0)
        added[ay, ax] = True
        expected = r0 | added
        for mode in ("nan", "zeros"):
            audit = v["files"][mode]
            path = ROOT / audit["path"]
            if base_build.sha256_file(path) != audit["sha256"]:
                raise ValueError(f"re-read SHA mismatch for {v['id']} {mode}")
            recheck = validate_candidate(path, expected, r0, foot, cat, dist_cat, sample_path, cat_path, template, mode, support)
            if recheck["sha256"] != audit["sha256"]:
                raise ValueError(f"validator SHA mismatch for {v['id']} {mode}")
            tmp = ROOT / ".cache" / "verify_candidate_bytes" / f"{v['id']}-{mode}.tif"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            try:
                base_build.emit(expected, foot, template, v["id"], mode, tmp)
                if base_build.sha256_file(tmp) != audit["sha256"]:
                    raise ValueError(f"byte-for-byte deterministic re-emit failed for {v['id']} {mode}")
            finally:
                tmp.unlink(missing_ok=True)
    receipt["parent"].update(parent_stats)
    receipt["manifest"] = {
        "manifest_path": "registry/data_manifest.json",
        "verified_count": len(input_receipt),
        "all_pins_rechecked": True,
        "files": input_receipt,
    }
    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = base_build.git_sha()
    receipt["self_check"] = {
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "r0_rebuilt_byte_identically": True,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} MASS-add pairs from disk; R0 rebuilt byte-identically to {R0_ZEROS_SHA}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    ap.add_argument(
        "--rebuild-reserved",
        action="store_true",
        help="re-emit the already-reserved tags and assert the rasters are byte-identical to the receipt "
             "(artifact/naming repair only; cannot create a new experiment)",
    )
    args = ap.parse_args()
    if args.build:
        result = build(allow_rebuild=args.rebuild_reserved)
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        update_ledgers_and_reservations(result)
        print(f"Built {len(result['variants'])} MASS-add variants from exact R0; evidence -> {RECEIPT.relative_to(ROOT)}")
        for v in result["variants"]:
            print(
                f"  {v['id']}: {v['n_dots']} dots (+{v['n_added']}), {v['pct_changed']:.3f}% changed, "
                f"pred {v['predicted_model']['point']:+.4f} [{v['predicted_model']['low']:+.4f},"
                f"{v['predicted_model']['high']:+.4f}] sha256={v['sha256']}"
            )
        return 0
    return verify_all()


if __name__ == "__main__":
    raise SystemExit(main())
