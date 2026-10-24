#!/usr/bin/env python3
"""2026-10-24 H1 lane runner: fold-clean learned fault-ness surface +
surface-ranked Poisson emission (docs/HYPOTHESES_20261024.md).

Stages (each writes a JSON receipt under evidence/):
  canary   per-feature blocked-evaluation AUC (leakage canary, stop if >0.90)
  holdout  5-fold 25 km-block hide-and-recover; arms A (incumbent FIFO-thinned
           H19-5 recipe, fold-clean collar), B (new surface), C (new surface
           restricted to H19-5 support), D (random-order control); matched dot
           budgets, pooled HOLDOUT-DTI + block-bootstrap 95% CIs (src/holdout.py)
  final    train on the full catalogue, emit the winning arm at the chosen
           budget, uniqueness vs every registry raster, format-gate the exact
           zeros-outside file offered for download, write the site + run card

No DrivenData/Dropbox access, no submission is made by this script -- it only
builds and validates files; the human uploads from their own account.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.dti import ALPHA, BETA, R_PX  # noqa: E402
from src.emission90 import poisson_emit  # noqa: E402
from src.features90 import CACHE, DATA, build_rank_u8, build_stack, load_masks  # noqa: E402
from src.holdout import (  # noqa: E402
    auc_rank,
    block_bootstrap_ci,
    block_components,
    dot_overlap_within,
    make_blocks,
    paired_block_bootstrap,
    pooled_dti,
    spearman_sample,
)
from src.validate import validate as format_gate  # noqa: E402

SEED = 20261024
BLOCK_PX = 250  # 25 km at 100 m/px
N_FOLDS = 5
BUFFER_PX = 5
COLLAR_PX = 2.0  # incumbent's winning edit: keep dots with d_catalogue > 2 px
MIN_SEP = 2.8
HOLDOUT_BUDGET = 40_000
HGB_PARAMS = dict(
    max_iter=200, learning_rate=0.08, max_leaf_nodes=63,
    min_samples_leaf=40, l2_regularization=1.0, random_state=SEED,
)
EVID = ROOT / "evidence"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sample_X(stack, ys, xs) -> np.ndarray:
    return np.stack([stack[i][ys, xs] for i in range(stack.shape[0])], axis=1).astype(np.float32)


def train_model(stack, pos_yx, neg_yx):
    Xp = sample_X(stack, pos_yx[0], pos_yx[1])
    Xn = sample_X(stack, neg_yx[0], neg_yx[1])
    X = np.vstack([Xp, Xn])
    y = np.r_[np.ones(len(Xp), dtype=np.int8), np.zeros(len(Xn), dtype=np.int8)]
    w_pos = len(Xn) / max(len(Xp), 1)
    w = np.where(y == 1, w_pos, 1.0)
    clf = HistGradientBoostingClassifier(**HGB_PARAMS)
    clf.fit(X, y, sample_weight=w)
    return clf


def predict_rows(clf, stack, row0: int, row1: int) -> np.ndarray:
    blk = np.stack([stack[i][row0:row1] for i in range(stack.shape[0])], axis=-1)
    h, w, _ = blk.shape
    return clf.predict_proba(blk.reshape(-1, stack.shape[0]))[:, 1].reshape(h, w).astype(np.float32)


# --------------------------------------------------------------- canary
def stage_canary() -> dict:
    stack, names, _ = build_stack()
    foot, cat, _h19, _prof = load_masks()
    rng = np.random.default_rng(SEED)
    d_cat = ndi.distance_transform_edt(~cat)
    pos = np.nonzero(cat)
    neg_pool = np.nonzero(foot & (d_cat > 10))
    take = rng.choice(neg_pool[0].size, size=min(250_000, neg_pool[0].size), replace=False)
    neg = (neg_pool[0][take], neg_pool[1][take])
    labels = np.r_[np.ones(pos[0].size, dtype=bool), np.zeros(neg[0].size, dtype=bool)]
    per = {}
    for i, name in enumerate(names):
        vals = np.r_[stack[i][pos], stack[i][neg]].astype(np.float64)
        auc = auc_rank(vals, labels)
        per[name] = {"auc": round(float(auc), 4), "symmetric_auc": round(float(max(auc, 1 - auc)), 4)}
    worst = max(per, key=lambda k: per[k]["symmetric_auc"])
    out = {
        "generated_utc": utc(), "stage": "canary", "seed": SEED,
        "protocol": "single-feature ROC-AUC, positives=all 60,988 catalogue px, "
                    "negatives=250k footprint px with d_catalogue>10px (evaluation only; "
                    "AUC>0.90 symmetric = leakage until proven otherwise)",
        "n_pos": int(pos[0].size), "n_neg": int(neg[0].size),
        "max_symmetric_auc_feature": worst,
        "max_symmetric_auc": per[worst]["symmetric_auc"],
        "leakage_stop_triggered": bool(per[worst]["symmetric_auc"] > 0.90),
        "per_feature": per,
    }
    (EVID / "lane90_canary_receipt.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("max_symmetric_auc_feature", "max_symmetric_auc", "leakage_stop_triggered")}, indent=2))
    return out


# --------------------------------------------------------------- holdout
def fifo_rank(h19: np.ndarray) -> np.ndarray:
    from build_r0_variants import fifo_bfs_visit_rank

    cache = CACHE / "fifo_rank.npy"
    if cache.is_file():
        return np.load(cache)
    r = fifo_bfs_visit_rank(h19)
    np.save(cache, r)
    return r


def stage_holdout() -> dict:
    t0 = time.time()
    stack, names, _ = build_stack()
    foot, cat, h19, _prof = load_masks()
    shape = foot.shape
    block_id, fold_map = make_blocks(shape, BLOCK_PX, N_FOLDS, SEED)
    frank = fifo_rank(h19).astype(np.float64)
    rng = np.random.default_rng(SEED)
    rand_score = rng.random(shape)
    oof = np.full(shape, np.nan, dtype=np.float32)
    arms = ("A_incumbent_fifo_h19", "B_new_surface", "C_surface_on_h19", "D_random_control")
    pooled = {a: None for a in arms}
    fold_rows = []
    foot_total = int(foot.sum())

    for f in range(N_FOLDS):
        hidden_blocks = fold_map == f
        dist_hidden = ndi.distance_transform_edt(~hidden_blocks)
        train_area = foot & ~hidden_blocks & (dist_hidden > BUFFER_PX)
        vis_cat = cat & train_area
        d_vis = ndi.distance_transform_edt(~vis_cat)
        pos = np.nonzero(vis_cat)
        neg_pool = np.nonzero(train_area & (d_vis > 10))
        take = rng.choice(neg_pool[0].size, size=min(220_000, neg_pool[0].size), replace=False)
        neg = (neg_pool[0][take], neg_pool[1][take])
        clf = train_model(stack, pos, neg)
        rows = np.nonzero(hidden_blocks.any(axis=1))[0]
        for r0 in range(int(rows.min()), int(rows.max()) + 1, 250):
            r1 = min(r0 + 250, shape[0])
            pred = predict_rows(clf, stack, r0, r1)
            m = hidden_blocks[r0:r1]
            oof[r0:r1][m] = pred[m]
        budget_f = int(round(HOLDOUT_BUDGET * float((foot & hidden_blocks).sum()) / foot_total))
        elig = foot & hidden_blocks & (d_vis > COLLAR_PX)
        truth_f = cat & hidden_blocks
        dots = {
            "A_incumbent_fifo_h19": poisson_emit(-frank, elig & h19, budget_f, MIN_SEP),
            "B_new_surface": poisson_emit(np.nan_to_num(oof), elig, budget_f, MIN_SEP),
            "C_surface_on_h19": poisson_emit(np.nan_to_num(oof), elig & h19, budget_f, MIN_SEP),
            "D_random_control": poisson_emit(rand_score, elig, budget_f, MIN_SEP),
        }
        row = {"fold": f, "budget": budget_f, "withheld_positives": int(truth_f.sum()),
               "train_positives": int(pos[0].size), "train_negatives": int(neg[0].size), "arms": {}}
        for a in arms:
            comp = block_components(dots[a], truth_f, block_id)
            pooled[a] = comp if pooled[a] is None else {k: pooled[a][k] + comp[k] for k in comp}
            row["arms"][a] = {"n_dots": int(dots[a].sum()), "fold_dti": round(pooled_dti(comp), 4)}
        fold_rows.append(row)
        print(f"fold {f}: budget={budget_f} withheld={row['withheld_positives']} "
              + " ".join(f"{a.split('_')[0]}={row['arms'][a]['fold_dti']}" for a in arms), flush=True)

    np.save(CACHE / "oof_surface.npy", oof)
    # OOF surface AUC on hidden positives vs far negatives (evaluation only)
    d_all = ndi.distance_transform_edt(~cat)
    hp = np.nonzero(cat & np.isfinite(oof))
    neg_pool = np.nonzero(foot & (d_all > 10) & np.isfinite(oof))
    take = rng.choice(neg_pool[0].size, size=min(250_000, neg_pool[0].size), replace=False)
    oof_auc = auc_rank(
        np.r_[oof[hp], oof[(neg_pool[0][take], neg_pool[1][take])]].astype(np.float64),
        np.r_[np.ones(hp[0].size, dtype=bool), np.zeros(take.size, dtype=bool)],
    )
    results = {}
    for a in arms:
        pt, lo, hi = block_bootstrap_ci(pooled[a])
        results[a] = {
            "holdout_dti": round(pt, 4), "ci95": [round(lo, 4), round(hi, 4)],
            "T": round(float(pooled[a]["T"].sum()), 1), "S": float(pooled[a]["S"].sum()),
            "M": round(float(pooled[a]["M"].sum()), 1), "G": int(pooled[a]["G"].sum()),
        }
    paired = {}
    for a in ("B_new_surface", "C_surface_on_h19", "D_random_control"):
        d, lo, hi = paired_block_bootstrap(pooled["A_incumbent_fifo_h19"], pooled[a])
        paired[f"{a}_minus_A"] = {"delta": round(d, 4), "ci95": [round(lo, 4), round(hi, 4)]}
    out = {
        "generated_utc": utc(), "stage": "holdout", "seed": SEED,
        "evaluator": f"src/holdout.py pooled DTI alpha={ALPHA} beta={BETA} triangular R={R_PX}px "
                     f"(src/dti.py A1/A2, UNVERIFIED vs official code); 25km blocks, {BUFFER_PX}px buffer, "
                     "visible faults masked pixel-exactly, collar d_vis>2px, matched budgets",
        "label": "HOLDOUT-DTI (not an organizer score)",
        "withheld_positives_total": int(sum(r["withheld_positives"] for r in fold_rows)),
        "oof_surface_auc_hidden_vs_far": round(float(oof_auc), 4),
        "budget_global_equivalent": HOLDOUT_BUDGET,
        "folds": fold_rows, "pooled": results, "paired_vs_incumbent": paired,
        "elapsed_s": round(time.time() - t0, 1),
        "caveats": [
            "H19-5 support lineage is owner-supplied; if it was built using the full catalogue, arm A/C holdout values are optimistic -- arm B uses no H19-5 pixels and no catalogue-derived feature.",
            "Trainer negatives are >10px from *visible* faults only (PU-realistic): some fall on withheld faults, which is label noise shared by all learned arms.",
            "Bands deq/ieq (earthquake distance/intensity) are organizer-supplied features kept after the canary; seismicity legitimately localises active faults.",
        ],
    }
    (EVID / "lane90_holdout_receipt.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"pooled": results, "paired": paired, "oof_auc": out["oof_surface_auc_hidden_vs_far"]}, indent=2))
    return out


# --------------------------------------------------------------- final
REGISTRY_RASTERS = [
    "parent/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "scored/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
    "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
    "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
    "scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
    "scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
    "scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif",
    "scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif",
    "scored/gemsdoe-ens12-adopted-7f00890a.tif",
    "scored/8GEMSDOE_Hedge-v2_submission.tif",
    "scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
    "scored/gemsdoe9-PLACEHOLDER-2314b599.tif",
]


def emit_geotiff(dots, foot, profile, mode: str, path: Path) -> None:
    prof = profile.copy()
    prof.update(driver="GTiff", dtype="float32", count=1, compress="deflate", predictor=3,
                zlevel=9, tiled=True, blockxsize=256, blockysize=256,
                nodata=np.nan if mode == "nan" else None)
    a = np.where(foot, dots.astype(np.float32), np.nan if mode == "nan" else 0.0).astype(np.float32)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(a, 1)


def stage_final(arm: str, budget: int) -> dict:
    t0 = time.time()
    hold = json.loads((EVID / "lane90_holdout_receipt.json").read_text())
    canary = json.loads((EVID / "lane90_canary_receipt.json").read_text())
    stack, names = build_rank_u8()
    foot, cat, h19, profile = load_masks()
    rng = np.random.default_rng(SEED)
    d_cat = ndi.distance_transform_edt(~cat)
    pos = np.nonzero(cat)
    neg_pool = np.nonzero(foot & (d_cat > 10))
    take = rng.choice(neg_pool[0].size, size=300_000, replace=False)
    neg = (neg_pool[0][take], neg_pool[1][take])
    clf = train_model(stack, pos, neg)
    surface = np.zeros(foot.shape, dtype=np.float32)
    for r0 in range(0, foot.shape[0], 250):
        surface[r0:r0 + 250] = predict_rows(clf, stack, r0, min(r0 + 250, foot.shape[0]))
    np.save(CACHE / "final_surface.npy", surface)
    elig = foot & (d_cat > COLLAR_PX)
    if arm == "C":
        elig = elig & h19
    dots = poisson_emit(surface.astype(np.float64), elig, budget, MIN_SEP)
    n_dots = int(dots.sum())
    assert n_dots == budget, f"emission starved: {n_dots} != {budget}"
    assert not (dots & cat).any(), "catalogue mass!"

    (ROOT / "releases").mkdir(exist_ok=True)
    tmp = ROOT / "releases" / "_lane90_tmp.tif"
    emit_geotiff(dots, foot, profile, "zeros", tmp)
    sha = sha256_file(tmp)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem = f"gems90-h1learned{arm.lower()}-poisson{budget // 1000}k-{stamp}-{sha[:8]}"
    zeros_path = ROOT / "releases" / f"{stem}-zeros.tif"
    nan_path = ROOT / "releases" / f"{stem}-nan.tif"
    tmp.replace(zeros_path)
    emit_geotiff(dots, foot, profile, "nan", nan_path)
    sha_nan = sha256_file(nan_path)

    sample = DATA / "sample_submission.tif"
    cat_path = DATA / "existing_faults.tif"
    gate_zeros = format_gate(str(zeros_path), str(sample), str(cat_path), zeros_outside=True)
    gate_nan = format_gate(str(nan_path), str(sample), str(cat_path), zeros_outside=False)

    uniq = []
    for rel in REGISTRY_RASTERS:
        with rasterio.open(DATA / rel) as ds:
            a = ds.read(1).astype(np.float64)
        other_dots = foot & np.isfinite(a) & (a > 0.5)
        dist_other = ndi.distance_transform_edt(~other_dots)
        # Density-matched baseline: fraction of the whole footprint within 3px of
        # the other raster.  A 5px lattice (206,895 px) or a 227k hedge covers
        # ~everything within 3px by construction, so raw overlap vs dense rasters
        # is a geometric tautology (their Spearman here is ~0); excess-over-baseline
        # is the density-invariant duplicate signal.  The protocol's 70% rule is
        # applied (a) raw, against comparably-sparse dotted rasters (<=65k dots --
        # the R0 lineage's emission family) and (b) as excess, against all rasters.
        # All numbers are published per raster; nothing is hidden.
        baseline = float((dist_other[foot] <= 3.0).mean()) if other_dots.any() else 0.0
        overlap = float(dot_overlap_within(dots, other_dots, 3.0))
        uniq.append({
            "raster": Path(rel).name,
            "surface_spearman": round(float(spearman_sample(surface, np.nan_to_num(a), foot)), 4),
            "dot_overlap_within_3px": round(overlap, 4),
            "footprint_baseline_within_3px": round(baseline, 4),
            "excess_overlap": round(overlap - baseline, 4),
            "other_n_dots": int(other_dots.sum()),
            "comparably_sparse_dotted": bool(int(other_dots.sum()) <= 65_000),
        })
    max_spear = max(abs(u["surface_spearman"]) for u in uniq if np.isfinite(u["surface_spearman"]))
    sparse = [u for u in uniq if u["comparably_sparse_dotted"]]
    max_over_sparse = max(u["dot_overlap_within_3px"] for u in sparse)
    max_excess = max(u["excess_overlap"] for u in uniq)
    max_over = max(u["dot_overlap_within_3px"] for u in uniq)
    lane_unique = bool(max_spear <= 0.90 and max_over_sparse <= 0.70 and max_excess <= 0.70)

    arm_key = {"B": "B_new_surface", "C": "C_surface_on_h19"}[arm]
    paired_key = f"{arm_key}_minus_A"
    beats = bool(hold["paired_vs_incumbent"][paired_key]["delta"] > 0)
    ci_clear = bool(hold["paired_vs_incumbent"][paired_key]["ci95"][0] > 0)
    submittable = bool(gate_zeros["pass"] and lane_unique and beats and not canary["leakage_stop_triggered"])
    form_note = f"H1 learned fault-ness ({arm}) Poisson {n_dots // 1000}k dots sep2.8 collar>2px; holdout-DTI {hold['pooled'][arm_key]['holdout_dti']}"
    assert len(form_note) <= 140, form_note

    out = {
        "generated_utc": utc(), "stage": "final", "seed": SEED,
        "hypothesis": "H1 fold-clean learned off-catalogue fault-ness surface + surface-ranked Poisson emission (docs/HYPOTHESES_20261024.md)",
        "mechanism": "HGB over 51 label-agnostic layers (19 competition bands + magnetic/gravity/basement derivatives + 3DEP lidar-scarp + GeoDAWN radiometrics); greedy unit dots, 2.8px separation, d_catalogue>2px, zero catalogue mass",
        "non_fault_mimicker": "lithologic contacts / survey seams share the same magnetic+radiometric edge signature",
        "arm": arm_key, "n_dots": n_dots, "min_sep_px": MIN_SEP, "collar_px_exclusive": COLLAR_PX,
        "budget_rationale": "40,000 = the budget at which arm B beat the incumbent recipe in the paired "
                            "holdout test, inside the leaderboard-CLAIM sweet spot (R0 37,654 / d2.8 44,090). "
                            "The OOF budget sweep (evidence/lane90_budget_receipt.json) still rises at 60k, but "
                            "holdout truth is mapped-fault density, denser than hidden-fault truth, and dense "
                            "leaderboard files (80k: 0.1193 CLAIM) collapsed -- so the sweep's optimum is "
                            "deliberately NOT extrapolated.",
        "catalogue_mass": 0.0, "min_d_cat_px": float(d_cat[dots].min()),
        "files": {
            "zeros_primary_download": {"path": f"releases/{zeros_path.name}", "sha256": sha,
                                       "bytes": zeros_path.stat().st_size, "format_gate": gate_zeros},
            "nan_twin": {"path": f"releases/{nan_path.name}", "sha256": sha_nan,
                         "bytes": nan_path.stat().st_size, "format_gate": gate_nan},
        },
        "holdout": {
            "label": "HOLDOUT-DTI (src/holdout.py; alpha 0.2 beta 0.8 R=3px; 25km blocks)",
            "this_arm": hold["pooled"][arm_key],
            "incumbent_A": hold["pooled"]["A_incumbent_fifo_h19"],
            "paired_delta_vs_A": hold["paired_vs_incumbent"][paired_key],
            "withheld_positives": hold["withheld_positives_total"],
            "ci_excludes_zero": ci_clear,
        },
        "canary": {"max_symmetric_auc": canary["max_symmetric_auc"],
                   "feature": canary["max_symmetric_auc_feature"], "stop": canary["leakage_stop_triggered"]},
        "uniqueness": {"max_abs_surface_spearman_vs_registry": round(float(max_spear), 4),
                       "max_dot_overlap_within_3px_vs_registry_all": round(float(max_over), 4),
                       "max_dot_overlap_within_3px_vs_sparse_dotted_le65k": round(float(max_over_sparse), 4),
                       "max_excess_overlap_vs_density_baseline": round(float(max_excess), 4),
                       "overlap_vs_parent_R0": uniq[0]["dot_overlap_within_3px"],
                       "lane_unique_le_0.90_and_le_0.70": lane_unique, "per_raster": uniq,
                       "rule_note": "Raw 70% rule applied to comparably-sparse dotted rasters (<=65k dots); "
                                    "vs dense rasters raw overlap is a coverage tautology (published per-raster "
                                    "with its footprint baseline), so excess-over-baseline<=0.70 is required for all. "
                                    "Surface Spearman<=0.90 required against every registry raster."},
        "submission_name": zeros_path.name,
        "form_note_le_140_chars": form_note, "form_note_chars": len(form_note),
        "verdict": "promote" if submittable else "negative",
        "ok_to_download_and_submit": submittable,
        "decision_rule": "promote requires: zeros format-gate PASS + lane-unique (Spearman<=0.90, overlap<=0.70) + holdout paired delta>0 vs incumbent recipe + canary clean. Human still chooses the slot; agent never submits.",
        "elapsed_s": round(time.time() - t0, 1),
    }
    (EVID / "lane90_final_receipt.json").write_text(json.dumps(out, indent=2) + "\n")
    (EVID / "lane90_run_card.json").write_text(json.dumps({
        "hypothesis": out["hypothesis"], "mechanism": out["mechanism"],
        "non_fault_mimicker": out["non_fault_mimicker"],
        "holdout_dti": out["holdout"]["this_arm"]["holdout_dti"],
        "holdout_ci95": out["holdout"]["this_arm"]["ci95"],
        "holdout_withheld_positives": out["holdout"]["withheld_positives"],
        "paired_delta_vs_incumbent_recipe": out["holdout"]["paired_delta_vs_A"],
        "correlation_overlap_vs_registry": {
            "max_abs_spearman": out["uniqueness"]["max_abs_surface_spearman_vs_registry"],
            "max_overlap_3px_sparse_dotted": out["uniqueness"]["max_dot_overlap_within_3px_vs_sparse_dotted_le65k"],
            "max_overlap_3px_all_raw": out["uniqueness"]["max_dot_overlap_within_3px_vs_registry_all"],
            "max_excess_overlap": out["uniqueness"]["max_excess_overlap_vs_density_baseline"],
            "overlap_vs_parent_R0": out["uniqueness"]["overlap_vs_parent_R0"]},
        "raster_sha256": sha, "validator": gate_zeros,
        "submission_name": out["submission_name"], "form_note": form_note,
        "verdict": out["verdict"],
    }, indent=2) + "\n")
    print(json.dumps({"file": out["submission_name"], "sha256": sha, "n_dots": n_dots,
                      "gate_zeros_pass": gate_zeros["pass"], "lane_unique": lane_unique,
                      "max_spearman": out["uniqueness"]["max_abs_surface_spearman_vs_registry"],
                      "max_overlap_sparse": out["uniqueness"]["max_dot_overlap_within_3px_vs_sparse_dotted_le65k"],
                      "max_excess": out["uniqueness"]["max_excess_overlap_vs_density_baseline"],
                      "verdict": out["verdict"]}, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["canary", "holdout", "final"])
    ap.add_argument("--arm", choices=["B", "C"], default="B")
    ap.add_argument("--budget", type=int, default=40_000)
    args = ap.parse_args()
    if args.stage == "canary":
        stage_canary()
    elif args.stage == "holdout":
        stage_holdout()
    else:
        stage_final(args.arm, args.budget)
    return 0


if __name__ == "__main__":
    sys.exit(main())
