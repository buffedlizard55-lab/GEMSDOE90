#!/usr/bin/env python3
"""Assemble the single JSON run card from the receipts written by this session."""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"


def load(name):
    p = EV / name
    return json.loads(p.read_text()) if p.exists() else None


def main() -> int:
    cand = load("candidate_receipt.json")
    hold = load("holdout_report.json")
    curve = load("holdout_budget_curve.json")
    cal = load("calibration_fit.json")
    band = load("band_profile.json")
    inv = load("blind_probe_inversion.json")
    canary = load("leakage_canary.json") or (hold or {}).get("leakage_canary", {})

    n = cand["n_dots"] if cand else None
    src = curve or hold
    pick = None
    if src and n is not None:
        key = str(min((int(k) for k in src["results"]["ours"]), key=lambda b: abs(b - n)))
        pick = src["results"]["ours"][key] | {"budget": int(key)}

    card = {
        "run_card_version": "1.0",
        "repo": "buffedlizard55-lab/GEMSDOE90",
        "branch": "arena/2226f0eb-gemsdoe90",
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lane": "credit-efficient adaptive emission",
        "experiments_run": 3,

        "hypothesis":
            "The DOE GEMS metric is won on credit efficiency, not on map accuracy. Because "
            "FN_w = |G| - TP_w, the index collapses to T / (0.2T + 0.2(S-M) + 0.8|G|), so each "
            "unit-mass dot that is far from truth costs a fixed 0.2 in the denominator and pays "
            "only its expected coverage credit. A fold-honest discovery model that ranks pixels "
            "by the probability of hosting an unmapped fault trace, emitted greedily until the "
            "marginal credit falls below the break-even 0.2*theta/(1-0.2*theta), should therefore "
            "beat a fixed-radius collar placed around the existing catalogue at the same budget.",

        "mechanism":
            "In the Great Basin >85% of geothermal systems sit in fault interaction zones - "
            "step-overs and relay ramps (~32-40%), horsetail terminations (~16-25%), fault "
            "intersections (~22-26%) and accommodation zones (~6-9%) - and only ~2% on main "
            "range-front segments (Faulds & Hinz 2015; Faulds et al. 2021a, 2026). Unmapped "
            "traces are therefore expected as linking strands, splays and cross-faults near but "
            "off mapped master traces, where potential-field gradients (magnetic terracing, "
            "gravity horizontal gradient over basin-floor steps), radiometric K-enrichment from "
            "up-flow alteration, lidar scarp morphometry and geodetic strain all respond. The "
            "learner combines 54 such static features with 9 catalogue-geometry features rebuilt "
            "per fold.",

        "named_non_fault_mimic":
            "Quaternary alluvial-fan toe scarps and shoreline terraces of pluvial Lake Lahontan. "
            "Both produce metre-scale, kilometres-long linear breaks in slope with a lidar "
            "signature essentially identical to a young fault scarp, and the Lahontan shorelines "
            "additionally follow elevation contours around every range front in the scene. They "
            "carry no magnetic or gravity offset, which is why the stack keeps potential-field "
            "gradients and the scarp morphometry as separate channels rather than fusing them.",

        "holdout": {
            "evaluator_version": (hold or {}).get("evaluator"),
            "protocol": (hold or {}).get("protocol"),
            "n_folds": (hold or {}).get("n_folds"),
            "buffer_px": (hold or {}).get("buffer_px"),
            "withheld_positive_px_total": pick["n_truth"] if pick else None,
            "budget": pick["budget"] if pick else None,
            "HOLDOUT_DTI": pick["dti"] if pick else None,
            "ci95": pick["ci"] if pick else None,
            "bootstrap": "spatial block x fold resampling, 2000 draws",
            "controls": {
                m: {"dti": src["results"][m][str(pick["budget"])]["dti"],
                    "ci95": src["results"][m][str(pick["budget"])]["ci"]}
                for m in ("collar", "chance", "R0_oracle")
                if src and pick and str(pick["budget"]) in src["results"].get(m, {})
            },
            "known_bias":
                "This holdout withholds catalogue segments, so its truth lies ON catalogue "
                "traces. Any prediction that deliberately avoids the 3 px neighbourhood of the "
                "catalogue - every collar-style submission, including the incumbent - scores "
                "near zero here by construction (R0 measured at 0.0048, below the 0.052 lattice "
                "chance baseline). The margin over those controls is therefore NOT evidence of a "
                "leaderboard win over them.",
        },

        "leakage_canary": canary,

        "calibration_against_real_scores": {
            "G_from_blind_lattice_probe": (inv or {}).get("G_adopted"),
            "break_even_credit_at_0.2778": (inv or {}).get("break_even_credit_at_0.2778"),
            "occupancy_capped_fit_rmse": (cal or {}).get("rmse_joint"),
            "band_inversion_rmse": ((band or {}).get("best") or {}).get("rmse"),
            "band_inversion_loo_rmse": ((band or {}).get("best") or {}).get("loo_rmse"),
            "verdict":
                "NEGATIVE. With pi constrained to a valid occupancy field (0<=pi<=1), neither the "
                "learner's field nor a model-free band inversion reproduces the 14 owner-reported "
                "scores; both under-predict every targeted raster by about a factor of two. No "
                "projected leaderboard score is claimed for this candidate.",
        },

        "candidate_geometry": (cand or {}).get("geometry"),

        "duplicate_screen": {
            "rule": "duplicate if (dot overlap within 3 px > 0.70 AND excess over chance > 0.30) "
                    "or Spearman rho > 0.90 against any registry raster",
            "max_overlap": (cand or {}).get("lane", {}).get("max_overlap"),
            "max_excess_over_chance": (cand or {}).get("lane", {}).get("max_excess_over_chance"),
            "max_spearman": (cand or {}).get("lane", {}).get("max_spearman"),
            "duplicate": (cand or {}).get("lane", {}).get("duplicate"),
        },

        "raster": {
            "file": Path((cand or {}).get("file", "")).name or None,
            "sha256": (cand or {}).get("sha256"),
            "bytes": (cand or {}).get("bytes"),
            "n_dots": n,
            "budget_source": (cand or {}).get("budget_source"),
        },
        "validator_output": (cand or {}).get("format_gate"),

        "submission_name": Path((cand or {}).get("file", "")).stem or None,
        "submission_note":
            "Fold-honest discovery model; greedy DTI-optimal dots at the holdout-optimal budget. "
            "Off-catalogue, not a collar file. No score claimed.",

        "verdict": "promote-for-human-review",
        "verdict_reason":
            "The candidate is unique, format-valid and beats both the chance lattice and a "
            "fold-honest rebuild of the collar recipe by a wide, CI-separated margin on the "
            "hide-and-recover holdout. It is NOT shown to beat the incumbent 0.2778 on the real "
            "task: the holdout is structurally blind to collar files, and the score-history "
            "calibration failed. Promotion to a weekly slot is a separate human decision.",

        "budget_spent": {
            "experiments": ["fold-honest discovery model + greedy emission",
                            "occupancy-capped calibration against 14 owner-reported scores",
                            "model-free band inversion of the hidden-fault radial profile"],
            "limit": "3 experiments or 2 hours",
        },
        "slot_selected": False,
    }
    if len(card["submission_note"]) > 140:
        card["submission_note"] = card["submission_note"][:137] + "..."
    out = ROOT / "docs" / "run-card.json"
    out.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    (EV / "run_card.json").write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(card['submission_note'])}-char note)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
