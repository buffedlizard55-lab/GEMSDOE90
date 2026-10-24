#!/usr/bin/env python3
"""Build ONE frontier PRUNE collar rung: radius 3.4 px, fixed count, max-marginal refill.

Session choice (agent-selected, 2026-10-24): AXIS = PRUNE.

The entity already holds outward collar rungs at 3.0 / 3.5 / 4.5 / 5.5 px and several 3.0 px
fixed-count collar+refill files (GEMSDOE84 `dcat>=3px-refill` / `dcat>3px-refill` / `d3p0`,
GEMSDOE86 `3` / `3r`, GEMSDOE88 `3` / `p3px`). All of them refill in the lineage's FIFO-BFS
thinning order. This script therefore builds the smallest **unoccupied** radius step beyond that
ladder (3.4 px) and changes exactly one other thing: the refill destination rule, from FIFO-BFS
order to maximum marginal kernel credit inside region-even 5 km quotas.

Measured headroom (this session, exact max-plus kernel on the pinned binary H19-5 support):
  FIFO-BFS refill  : 0.60 support credit per refilled dot at a 3.5 px collar
  max-marginal     : 1.38 support credit per refilled dot at a 3.0 px collar
Both are reported in the receipt for the same collar and count, so the refill term is not confounded
with the collar term. The collar term itself is truth-dependent and is reported as two named
scenarios (src/collar.py) rather than one number.

Hard constraints honoured here: every final dot lies strictly outside the 3.4 px collar (so this is
the first candidate in this repository whose own collar is stricter than Hard Constraint #4's
`>= 3 px`), zero catalogue mass, fixed count, zero NaN inside the footprint, NaN (or zeros in the
fallback twin) outside it, and no truth/label/leaderboard information of any kind.

Run:  .venv/bin/python scripts/build_prune_collar_gapmax.py --build
Check .venv/bin/python scripts/build_prune_collar_gapmax.py --verify   (re-emits bytes, compares)
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
from build_aniso_prune_variants import audit_file, canary, emit_pair  # noqa: E402
from build_aniso_prune_norefill import existing_hashes  # noqa: E402
from build_relief_variants import compute_spatial_block_proxy  # noqa: E402
from src.collar import (  # noqa: E402
    PER_CREDIT,
    exclusive_credit,
    prediction_scenarios,
    rebalance_quotas,
    refill_max_marginal,
    region_even_quotas,
)
from src.mass_add import addition_evenness_gate, addition_report, block_counts  # noqa: E402

DATA = R0.DATA
OUT = R0.OUT
LEDGER = ROOT / "ledger" / "submissions.csv"
RESERVATIONS = ROOT / "ledger" / "experiment_reservations.json"
RECEIPT = ROOT / "evidence" / "prune_collar_gapmax_receipt.json"
PARENT = "h33-h33-2-b2"
AXIS = "PRUNE"
DATE = "20261024"
RADIUS_PX = 3.4
R0_DOTS = R0.R0_DOTS
SEED = 20261024
SLUG = f"{PARENT}-PRUNEcollar3p4Gapmax-{DATE}"
TAG = "collar3p4Gapmax"
VALUE = (
    "tag=collar3p4Gapmax; collar d_cat<=3.4px removed (every final dot d_cat>3.4px); "
    "fixed count 37654; refill = max marginal R=3px kernel credit in region-even 5km quotas"
)


def occupied_radii() -> list[float]:
    """Every isotropic PRUNE radius the entity has already used (local ledger + reservations)."""
    out: list[float] = []
    if RESERVATIONS.exists():
        res = json.loads(RESERVATIONS.read_text())
        for source in res.get("sources", []):
            out.extend(float(x) for x in source.get("values_px", []))
        out.extend(float(x) for x in res.get("available_selected_values_px", []))
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                if (row.get("id") or "").startswith(SLUG):
                    continue  # this script's own row; re-emitting it must stay legal
                value = row.get("value") or ""
                for token in value.replace(",", " ").split():
                    token = token.replace("px", "").replace("d_cat<=", "").replace("dcat", "")
                    try:
                        out.append(float(token))
                    except ValueError:
                        continue
    return sorted(set(out))


def check_reservations() -> dict:
    """Fail closed on a repeated (parent, axis, value) and on a repeated numeric radius."""
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                if TAG in (row.get("value") or "") and not (row.get("id") or "").startswith(SLUG):
                    raise ValueError(f"duplicate (PRUNE, {TAG}) already in ledger: {row.get('id')}")
    radii = occupied_radii()
    if any(abs(RADIUS_PX - r) < 1e-9 for r in radii):
        raise ValueError(f"(PRUNE, {RADIUS_PX}px) collides numerically with an occupied radius")
    nearest = min(radii, key=lambda r: abs(r - RADIUS_PX)) if radii else None
    return {
        "occupied_radii_px": radii,
        "chosen_radius_px": RADIUS_PX,
        "nearest_occupied_radius_px": nearest,
        "numeric_collision": False,
        "value_collision": False,
        "note": (
            "3.4 px is unoccupied in this ledger and in ledger/experiment_reservations.json. The "
            "entity's 3.0 / 3.5 / 4.5 / 5.5 rungs exist, but every one of them refills in FIFO-BFS "
            "order; the pair tested here is (collar radius 3.4 px, max-marginal refill)."
        ),
    }


def diff_stats(parent: np.ndarray, candidate: np.ndarray, distance: np.ndarray, kept: np.ndarray) -> dict:
    """Parent-difference statistics required by the session gates (no strike field needed)."""
    from scipy.spatial import cKDTree

    removed = parent & ~candidate
    added = candidate & ~parent
    ry, rx = np.nonzero(removed)
    ay, ax = np.nonzero(added)
    stats = {
        "n_parent": int(parent.sum()),
        "n_candidate": int(candidate.sum()),
        "n_removed": int(ry.size),
        "n_added": int(ay.size),
        "n_retained_parent": int((parent & candidate).sum()),
        "symmetric_difference_px": int((parent ^ candidate).sum()),
        "removed_catalogue_distance_px": {
            "min": round(float(distance[ry, rx].min()), 3),
            "median": round(float(np.median(distance[ry, rx])), 3),
            "max": round(float(distance[ry, rx].max()), 3),
        } if ry.size else {},
        "added_catalogue_distance_px": {
            "min": round(float(distance[ay, ax].min()), 3),
            "median": round(float(np.median(distance[ay, ax])), 3),
            "max": round(float(distance[ay, ax].max()), 3),
        } if ay.size else {},
    }
    if ay.size:
        d_kept = ndi.distance_transform_edt(~kept)
        stats["added_distance_to_kept_px"] = {
            "min": round(float(d_kept[ay, ax].min()), 3),
            "median": round(float(np.median(d_kept[ay, ax])), 3),
            "p95": round(float(np.percentile(d_kept[ay, ax], 95)), 3),
        }
        if ry.size:
            tree = cKDTree(np.c_[ay, ax])
            disp, _ = tree.query(np.c_[ry, rx], k=1)
            stats["removed_to_nearest_added_px"] = {
                "median": round(float(np.median(disp)), 3),
                "max": round(float(disp.max()), 3),
            }
    return stats


def refill_report(kept: np.ndarray, refill: np.ndarray, distance: np.ndarray) -> dict:
    """How far the refilled mass sits from the retained dots and from the catalogue.

    A refill that lands inside a retained dot's kernel adds the 0.2*(S-M) mass term and almost no
    T; this is the statistic that says whether the *policy* (not the collar) is doing the work.
    """
    ry, rx = np.nonzero(refill)
    if ry.size == 0:
        return {"n_refill": 0}
    d_kept = ndi.distance_transform_edt(~kept)
    to_kept = d_kept[ry, rx]
    return {
        "n_refill": int(ry.size),
        "refill_dist_to_nearest_retained_median_px": round(float(np.median(to_kept)), 3),
        "refill_dist_to_nearest_retained_max_px": round(float(to_kept.max()), 3),
        "refill_within_3px_of_retained_pct": round(100.0 * float((to_kept <= 3.0).mean()), 3),
        "min_catalogue_distance_of_final_set_px": round(float(distance[kept | refill].min()), 3),
        "interpretation": (
            "A high 'within 3 px of retained' share means the refill is largely redundant mass: "
            "penalty without fresh kernel credit. It is a property of the policy, never a live score."
        ),
    }


def fifo_reference(
    pool: np.ndarray,
    support: np.ndarray,
    kept: np.ndarray,
    quotas: np.ndarray,
    rank: np.ndarray,
) -> dict:
    """Report-only: what the inherited FIFO-BFS refill buys at the same collar and count."""
    from src.mass_add import coverage, n_blocks

    h, w = pool.shape
    nr, nc = n_blocks(pool.shape, 50)
    cov = coverage(kept, support, 3)
    offs = [(dy, dx, k) for dy in range(-3, 4) for dx in range(-3, 4)
            for k in [max(0.0, 1.0 - float(np.hypot(dy, dx)) / 3.0)] if k > 0]
    total = 0.0
    for bi in range(quotas.size):
        need = int(quotas[bi])
        if need <= 0:
            continue
        r0 = (bi // nc) * 50
        c0 = (bi % nc) * 50
        ly, lx = np.nonzero(pool[r0:min(h, r0 + 50), c0:min(w, c0 + 50)])
        gy, gx = ly + r0, lx + c0
        order = np.argsort(rank[gy, gx], kind="stable")[:need]
        for y, x in zip(gy[order].tolist(), gx[order].tolist()):
            for dy, dx, k in offs:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and support[yy, xx] and k > cov[yy, xx]:
                    total += k - cov[yy, xx]
                    cov[yy, xx] = k
    return {"fifo_refill_gained_support_credit": round(float(total), 3),
            "dots": int(quotas.sum()),
            "mean_credit_per_dot": round(float(total) / max(1, int(quotas.sum())), 3)}


def build(run_proxies: bool = True) -> dict:
    t0 = time.time()
    reservation = check_reservations()
    manifest = R0.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = R0.exact_parent_rebuild()

    distance = ndi.distance_transform_edt(~cat)
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    if np.any(r0 & ~support):
        raise RuntimeError("R0 has dots off the pinned H19-5 support; the coverage model is invalid here")
    rank = R0.fifo_bfs_visit_rank(h19)

    collar = distance <= RADIUS_PX
    removed = r0 & collar
    kept = r0 & ~removed
    n_removed = int(removed.sum())
    if n_removed == 0:
        raise ValueError(f"collar {RADIUS_PX} px removes no parent dots")

    # Donor-side credit: the exact T-loss of deleting every collared dot (max-plus kernel).
    _, _, per_dot = exclusive_credit(r0, support, 3)
    lost_credit = float(per_dot[np.asarray(removed[np.nonzero(r0)], dtype=bool)].sum())

    pool = support & (distance > RADIUS_PX) & ~kept
    quotas, quota_moved = rebalance_quotas(
        region_even_quotas(r0, n_removed), block_counts(pool, 50).ravel()
    )
    ay, ax, gains = refill_max_marginal(pool, support, kept, quotas, 3)
    if ay.size != n_removed:
        raise AssertionError(f"refill placed {ay.size} of {n_removed} freed dots")

    candidate = kept.copy()
    candidate[ay, ax] = True
    if int(candidate.sum()) != R0_DOTS:
        raise AssertionError(f"fixed count failed: {int(candidate.sum())} != {R0_DOTS}")
    if np.any(candidate & collar) or np.any(candidate & cat) or np.any(candidate & ~foot):
        raise AssertionError("candidate violates its own collar / catalogue / footprint rule")

    evenness = addition_report(candidate & ~r0, r0, block_px=50)
    evenness["gate_pass"] = bool(addition_evenness_gate(evenness))
    if not evenness["gate_pass"]:
        raise SystemExit(f"STOP: refill is not region-even: {evenness}")

    from src.collar import coverage as _cov

    support_credit_r0 = _cov(r0, support, 3).sum()
    gained_credit = float(gains.sum())
    scenarios = prediction_scenarios(gained_credit, lost_credit, PER_CREDIT)
    fifo = fifo_reference(pool, support, kept, quotas, rank)

    nan_path, zeros_path = emit_pair(candidate, foot, template, SLUG)
    nan_audit = audit_file(nan_path, candidate, foot, cat, template, "nan", collar)
    zeros_audit = audit_file(zeros_path, candidate, foot, cat, template, "zeros", collar)
    own_id = f"{SLUG}-{nan_audit['sha256'][:8]}"
    own_exclusions = {own_id, nan_path.name, zeros_path.name}
    for audit in (nan_audit, zeros_audit):
        if audit["sha256"] in existing_hashes(exclude_ids=own_exclusions):
            raise SystemExit(f"STOP: sha256 already present in the ledger: {audit['sha256']}")

    diff = diff_stats(r0, candidate, distance, kept)
    removed_n = int(removed.sum())
    added_n = int((candidate & ~r0).sum())
    retained_n = int((candidate & r0).sum())
    pct_changed = 100.0 * float(np.count_nonzero(candidate ^ r0)) / R0_DOTS
    if not 1.0 <= pct_changed <= 50.0:
        raise ValueError(f"changed {pct_changed:.4f}% of R0 (recipe requires 1-50%)")

    central = scenarios["central"]
    pred_str = f"{central:+.3f}"
    predicted_change = (
        f"{pred_str} DTI (MODEL; bracket {scenarios['bracket'][0]:+.3f} to "
        f"{scenarios['bracket'][1]:+.3f}; not a score)"
    )
    form_note = (
        f"{PARENT}; PRUNE collar 3.4px, fixed count, max-marginal refill; pred {pred_str} DTI MODEL"
    )
    if len(form_note) > 140:
        raise AssertionError(f"form note is {len(form_note)} chars")

    card = {
        "hypothesis": (
            "R0's 2 px catalogue collar is the only edit in its lineage with a live-positive claim "
            "(solo-d28 0.2708 -> pruned 0.2778), so the collar frontier is the one dose-response the "
            "entity has measured. Extending the collar by 1.4 px should keep paying while the removed "
            "flank dots sit inside the mapped traces' damage zone, and should stop paying once the "
            "removed dots are far enough out to be genuine new fault."
        ),
        "mechanism": (
            "Known catalogue pixels are masked pixel-exactly; a dot there earns no T but still pays "
            "the 0.2*(S-M) mass term, and a dot beside them is scored only against new-fault truth. "
            "Deleting the 3.0-3.4 px shell removes mass whose expected truth credit is low, and "
            "re-placing the same count at the maximum marginal R=3 px kernel credit inside region-even "
            "5 km quotas adds coverage where the binary H19-5 support is un-served. Count is held at "
            "37,654 so emitted mass cannot explain a live change."
        ),
        "non_fault_confounder": (
            "H19-5 is binary, so max-marginal placement cannot distinguish a fault ridge from a "
            "lithologic contact, a drainage line or a survey-flight artefact; and new-fault truth is "
            "explicitly allowed within 300 m of known traces, so the deleted shell may hold real "
            "credit. Both confounders push the live change down, not up."
        ),
        "predicted_live_change": predicted_change,
        "falsifier": (
            "A paired live receipt against R0 with delta <= -0.010 falsifies the collar extension at "
            "this radius and, read together with the 3.0 px rungs, ends the outward collar ladder. "
            "Any |delta| < 0.010 is no evidence under the session rule and licenses no further dose "
            "guess on this axis."
        ),
        "structural_geologist_note": (
            "The deleted shell is a 340 m halo around every mapped trace; the added dots are the "
            "least-served parts of the binary H19-5 field, which is not a fault-probability ranking. "
            "Read the file as a collar test with a repaired refill, not as a claim that new faults "
            "avoid mapped traces."
        ),
    }

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": R0.git_sha(),
        "generator_script_sha256": R0.sha256_file(Path(__file__)),
        "axis": AXIS,
        "session_note": (
            "One variant, not three: see SLOT_PLAN.md / IRREGULARITIES.md IR90-35. The measured "
            "headroom of every other free collar/spacing/dose knob is below the 0.010 evidence floor, "
            "so a second and third file would spend the human's attention without buying information."
        ),
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": R0.R0_ZEROS_SHA,
            "nan_sha256": R0.R0_NAN_SHA,
            **parent_stats,
        },
        "manifest": {"manifest_path": "registry/data_manifest.json",
                     "verified_count": len(manifest), "all_pins_rechecked": True},
        "reservation": reservation,
        "collar": {
            "radius_px": RADIUS_PX,
            "radius_m": RADIUS_PX * 100,
            "removed": n_removed,
            "kept": retained_n,
            "added": added_n,
            "min_catalogue_distance_px": float(distance[candidate].min()),
            "parent_min_catalogue_distance_px": float(distance[r0].min()),
            "parent_dots_below_3px": int((r0 & (distance < 3.0)).sum()),
            "parent_diff": diff,
            "pct_changed_of_R0": round(pct_changed, 6),
            "fraction_of_R0_removed": round(100.0 * n_removed / R0_DOTS, 4),
        },
        "refill": {
            "policy": "max marginal R=3px kernel credit, region-even 5 km quotas proportional to R0",
            "quotas_rebalanced_dots": int(quota_moved),
            "gained_support_credit": round(gained_credit, 3),
            "mean_credit_per_dot": round(gained_credit / max(1, ay.size), 3),
            "fifo_reference": fifo,
            "diagnostics": refill_report(kept, candidate & ~r0, distance),
            "region_evenness": evenness,
        },
        "support_credit_ledger": {
            "lost_from_removed_dots": round(lost_credit, 3),
            "lost_per_removed_dot": round(lost_credit / max(1, n_removed), 3),
            "gained_from_refill": round(gained_credit, 3),
            "net_support_credit": round(gained_credit - lost_credit, 3),
            "support_credit_covered_by_R0": round(float(support_credit_r0), 3),
        },
        "prediction": {
            "scenarios": scenarios,
            "calibration": (
                "PER_CREDIT = 3.6e-6 dDTI per unit support credit, fitted to the three slotted MASS "
                "add rungs (1,883/3,765/7,531 dots -> 2,162/3,814/6,501 credit -> +0.008/+0.014/+0.022 "
                "MODEL). It is a MODEL constant, not a live measurement."
            ),
            "frozen_before_proxies": True,
        },
        "files": {"nan": nan_audit, "zeros": zeros_audit},
        "mechanism_card": card,
        "form_note": form_note,
        "predicted_change": predicted_change,
        "ledger_value": VALUE,
        "id": f"{SLUG}-{nan_audit['sha256'][:8]}",
        "n_dots": R0_DOTS,
    }
    # Same receipt schema as the other PRUNE families so the cross-receipt ledger test can include it.
    result["variants"] = [{
        "id": result["id"],
        "parent": PARENT,
        "axis": AXIS,
        "value": VALUE,
        "n_dots": R0_DOTS,
        "pct_changed": round(pct_changed, 6),
        "removed_dots": n_removed,
        "added_dots": added_n,
        "retained_dots": retained_n,
        "sha256": nan_audit["sha256"],
        "sha256_zeros": zeros_audit["sha256"],
        "status": "BUILT",
        "predicted_change": predicted_change,
        "form_note": form_note,
        "files": {"nan": nan_audit, "zeros": zeros_audit},
    }]

    if run_proxies:
        leakage = canary(max_samples=100_000, seed=SEED)
        if leakage.get("max_symmetric_auc", 0.0) > 0.90:
            raise RuntimeError("STOP AND INVESTIGATE: leakage canary AUC > 0.90")
        catalogue_proxy = compute_spatial_block_proxy(
            {"R0": r0, result["id"]: candidate}, foot, cat, holdout_quarter=True, seed=SEED
        )
        catalogue_proxy["caveat"] = (
            "PROXY only: known catalogue labels are live-masked and this holdout has collar blind "
            "spots; never a gate or a score."
        )
        result["proxy_reports"] = {
            "leakage_canary": leakage,
            "catalogue_hide_recover": catalogue_proxy,
            "sgmc_control": {"status": "NOT RUN", "reason": "no calibrated fold-clean SGMC instrument "
                                                           "was validated for this collar/refill design"},
        }

    result["elapsed_s"] = round(time.time() - t0, 1)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("id", "predicted_change", "form_note")}, indent=2))
    print(f"removed {n_removed} / added {added_n} / kept {retained_n} / changed {pct_changed:.4f}%")
    print(f"support credit: lost {lost_credit:.1f}, gained {gained_credit:.1f}, net "
          f"{gained_credit - lost_credit:.1f}; FIFO reference {fifo['mean_credit_per_dot']:.3f}/dot")
    print(f"min catalogue distance {result['collar']['min_catalogue_distance_px']:.3f} px")
    print(f"receipt -> {RECEIPT.relative_to(ROOT)}")
    return result


def write_ledger_row(result: dict) -> None:
    row = {
        "id": result["id"],
        "site": "GEMSDOE90",
        "name": Path(result["files"]["nan"]["path"]).name,
        "score": "",
        "evidence_class": "MODEL",
        "encoding": "nan primary; zeros fallback",
        "n_dots": result["n_dots"],
        "pct_changed": f"{result['collar']['pct_changed_of_R0']:.6f}",
        "sha256": result["files"]["nan"]["sha256"],
        "sha256_zeros": result["files"]["zeros"]["sha256"],
        "parent": PARENT,
        "axis": AXIS,
        "value": result["ledger_value"],
        "status": "BUILT",
        "receipt": "N",
        "receipt_score": "",
        "predicted_change": result["predicted_change"],
        "date": "",
        "form_note": result["form_note"],
        "notes": (
            "fixed 37,654 count; collar 3.4 px (every final dot d_cat>3.4 px, the first repo "
            "candidate stricter than the >=3 px rule); max-marginal region-even refill; "
            "receipt_score/date filled by the human; agent never submits"
        ),
    }
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    existing = next((r for r in rows if r.get("id") == row["id"]), None)
    if existing is not None:
        if (existing.get("sha256") == row["sha256"]
                and existing.get("sha256_zeros") == row["sha256_zeros"]):
            print(f"ledger row already present and hash-identical; byte re-emit verified: {row['id']}")
            return
        raise SystemExit(f"STOP: ledger has {row['id']} with different hashes")
    rows.append(row)
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"ledger row appended: {row['id']}")


def verify() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    manifest = R0.verify_manifest_inputs()
    template, foot, cat, r0, _ = R0.exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~cat)
    h19 = R0.read_binary(DATA / R0.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    collar = distance <= RADIUS_PX
    removed = r0 & collar
    kept = r0 & ~removed
    pool = support & (distance > RADIUS_PX) & ~kept
    quotas, _ = rebalance_quotas(region_even_quotas(r0, int(removed.sum())),
                                 block_counts(pool, 50).ravel())
    ay, ax, _ = refill_max_marginal(pool, support, kept, quotas, 3)
    candidate = kept.copy()
    candidate[ay, ax] = True

    checks: dict[str, bool] = {"manifest_verified": len(manifest) == 26}
    for mode in ("nan", "zeros"):
        path = ROOT / receipt["files"][mode]["path"]
        if not path.is_file():
            checks[f"{mode}_present"] = False
            continue
        audit = audit_file(path, candidate, foot, cat, template, mode, collar)
        checks[f"{mode}_sha256_matches_receipt"] = audit["sha256"] == receipt["files"][mode]["sha256"]
        checks[f"{mode}_gates_pass"] = all(audit["checks"].values())
    checks["count_held"] = int(candidate.sum()) == R0_DOTS
    checks["all_checks_passed"] = all(checks.values())
    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = R0.git_sha()
    receipt["self_check"] = checks
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))
    return 0 if checks["all_checks_passed"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--build", action="store_true")
    group.add_argument("--verify", action="store_true")
    ap.add_argument("--no-proxies", action="store_true", help="skip the report-only proxy instruments")
    args = ap.parse_args()
    if args.verify:
        return verify()
    result = build(run_proxies=not args.no_proxies)
    write_ledger_row(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
