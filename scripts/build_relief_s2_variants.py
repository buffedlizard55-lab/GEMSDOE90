#!/usr/bin/env python3
"""Rebuild R0 byte-for-byte, then build and validate 3 controlled AXIS=RELIEF variants
(session 2026-10-24, branch arena/b5ea0544-gemsdoe90).

The ONLY changed axis relative to R0 (`h33-h33-2-b2`, 37,654 unit-mass dots) is the
physiographic relief-tercile mass allocation across Basin (T1), Piedmont (T2) and
Range-front (T3), using the SAME pinned recipe as the 2026-10-23 RELIEF family in
`src/relief.py` (equal-area landform terciles from Band 12 `det_elev` 0.85 weight and
Band 19 `det_elev_slope` 0.15 weight, 3 km Gaussian landform smoothing). Total count is
held strictly at 37,654 dots; all dots lie on the pinned off-catalogue H19-5 ridge
support; every newly added dot has Euclidean catalogue distance >= 3.0 px; zero
catalogue mass is emitted.

Why these three values: a read-only `gh api` audit of every reachable sibling ledger
(GEMSDOE84-89, 91, 92; GEMSDOE93-101 carry no ledger) on 2026-10-24 found 27 RELIEF rows
covering range->piedmont, range->basin, piedmont->range and basin->range, but ZERO
basin->piedmont or piedmont->basin directed pairs under any naming. The three variants
here are the two unbuilt directions, with a 12.5/15% dose pair on the primary
(piedmont->basin, concealed-basin enrichment) and a 10% direction control
(basin->piedmont). See `ledger/experiment_reservations.json` key
`relief_s2_reservations_20261024` and IR90-35.

Run build:  `.venv/bin/python scripts/build_relief_s2_variants.py --build`
Run verify: `.venv/bin/python scripts/build_relief_s2_variants.py --verify`
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
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_r0_variants as base_build  # noqa: E402
import build_relief_variants as relief1  # noqa: E402
from src.relief import block_density_cv  # noqa: E402

DATA = ROOT / ".cache" / "gems_data"
OUT = ROOT / "releases"
PARENT = "h33-h33-2-b2"
AXIS = "RELIEF"
DATE = "20261024"
SEED = 20261024
R0_DOTS = 37_654
RECEIPT_PATH = ROOT / "evidence" / "relief_s2_build_receipt.json"
CARDS_PATH = ROOT / "ledger" / "mechanism_cards_relief_s2.json"
RESERVATION_KEY = "relief_s2_reservations_20261024"

# Predictions are MODEL projections (never scores), frozen in this table BEFORE any
# proxy is computed. Sign calibration: the in-repo 2026-10-23 RELIEF family projected
# down-relief moves small-positive (r2p12.5 +0.004; r2b10 +0.003) and the up-relief
# counterpoint small-negative (p2r15 -0.004); every fixed-count move nonetheless loses
# net H19-5 support credit (IR90-25), so brackets stay wide and symmetric-ish.
VARIANT_SPECS = (
    {
        "tag": "p2b12p5pct",
        "donor": "piedmont",
        "recipient": "basin",
        "mass_frac": 0.125,
        "n_shift": 4_707,  # round(0.125 * 37,654)
        "pred_short": "+0.003",
        "predicted_change": "+0.003 DTI (MODEL; plausible interval -0.010 to +0.015; not a score)",
        "hypothesis": (
            "R0 carries only 17.25% of its dots in Basin terciles while 28.23% of known "
            "USGS/INGENIOUS catalogue fault pixels sit there, an 11-point concealed-terrain "
            "deficit. Shifting 12.5% of R0 mass (4,707 dots) from Piedmont (T2, the largest "
            "tercile, 16,871 dots) into Basin (T1) densifies R=3 px kernel coverage over "
            "concealed intrabasin graben and blind relay/step-over faults buried under "
            "Plio-Quaternary alluvium, whose H19-5 geophysical ridges have little surface "
            "expression. Funding the move from the largest tercile minimises collateral "
            "damage to well-sampled piedmont corridors."
        ),
        "mechanism": (
            "Equal-area landform terciles are the pinned src.relief partition from det_elev "
            "(0.85 percentile weight) and 3 km Gaussian-smoothed det_elev_slope (0.15). The "
            "4,707 lowest-exclusive-kernel-credit R0 dots in T2 are dropped greedily, then "
            "4,707 highest-marginal-credit off-catalogue H19-5 pixels in T1 are added "
            "greedily, every addition at Euclidean d_cat >= 3.0 px; count is held at 37,654. "
            "GeoDAWN Area 2 was flown at 400 m line spacing 150-200 m above terrain, so "
            "concealed lineament positions are uncertain by roughly the kernel radius and a "
            "denser basin coverage raises expected credit on newly mapped basin truth."
        ),
        "non_fault_confounder": (
            "Lake Lahontan pluvial shoreline berms, axial fluvial channels, buried basaltic "
            "sills/flows, playa hydrologic patterns and valley-floor cultural lineaments "
            "(roads, railways, pipelines) generate non-fault magnetic/topographic ridges in T1."
        ),
        "falsifier": (
            "A paired live receipt against R0 with Delta <= -0.010 DTI falsifies "
            "piedmont-funded basin enrichment at this dose (basin H19-5 ridges would then be "
            "predominantly non-fault). Any |Delta| < 0.010 is no evidence; private chunks may "
            "differ from the public chunks."
        ),
    },
    {
        "tag": "p2b15pct",
        "donor": "piedmont",
        "recipient": "basin",
        "mass_frac": 0.150,
        "n_shift": 5_648,  # round(0.150 * 37,654)
        "pred_short": "+0.004",
        "predicted_change": "+0.004 DTI (MODEL; plausible interval -0.012 to +0.018; not a score)",
        "hypothesis": (
            "Deeper 15.0% dose (5,648 dots) of the same piedmont->basin mechanism, giving the "
            "dose-response slope of concealed-basin enrichment: if basin truth is under-covered, "
            "the second increment should pay at least as well as the first because R0's basin "
            "share (17.25%) remains far below the catalogue basin share (28.23%) even after the "
            "12.5% move. The recipient eligible pool (about 11.4k H19-5 pixels at d_cat>=3 px) "
            "is large enough that the greedy add order does not saturate."
        ),
        "mechanism": (
            "Identical operator and terciles as p2b12p5pct with n_shift=5,648: greedy minimum "
            "R=3 px triangular-kernel exclusive-credit loss drops in T2, greedy maximum "
            "marginal-credit adds in T1 on off-catalogue H19-5 support, all additions d_cat "
            ">= 3.0 px, fixed count 37,654, deterministic (row, col) tie-breaks, no random seed "
            "in variant construction."
        ),
        "non_fault_confounder": (
            "Same basin confounders as p2b12p5pct (shorelines, channels, buried sills, "
            "cultural lineaments); at the deeper dose, lower-ranked basin ridges are reached "
            "first, so any non-fault contamination costs more than at 12.5%."
        ),
        "falsifier": (
            "A live Delta <= -0.010, or a receipt at least 0.010 below the p2b12p5pct receipt, "
            "falsifies the deeper dose and indicates the basin recipient pool saturates near "
            "the first increment. |Delta| < 0.010 is no evidence."
        ),
    },
    {
        "tag": "b2p10pct",
        "donor": "basin",
        "recipient": "piedmont",
        "mass_frac": 0.100,
        "n_shift": 3_766,  # ceil(0.100 * 37,654) -> 10.0016%, matching the in-repo r2b10 convention
        "pred_short": "-0.002",
        "predicted_change": "-0.002 DTI (MODEL; plausible interval -0.014 to +0.012; not a score)",
        "hypothesis": (
            "Direction control for the two piedmont->basin arms: if basin-floor H19-5 pixels "
            "are mostly non-fault cultural/stratigraphic ridges and new-fault truth instead "
            "concentrates in exposed piedmont range-bounding corridors (off-catalogue SGMC "
            "map faults sit 24.94% in T2 vs 9.33% in T1), moving 10.0% of R0 mass (3,766 dots) "
            "out of Basin into Piedmont should raise DTI. Under the primary concealed-basin "
            "hypothesis this arm is predicted slightly negative because it widens R0's basin "
            "deficit. The pair (b2p10 vs p2b12p5) is a matched direction test at similar dose."
        ),
        "mechanism": (
            "Same pinned terciles and greedy R=3 px kernel operator: 3,766 minimum-loss drops "
            "inside T1 (58.0% of R0's 6,495 basin dots; the region-evenness report below checks "
            "that no contiguous regional hole opens), then 3,766 maximum-gain adds on T2 "
            "off-catalogue H19-5 support at d_cat >= 3.0 px; fixed count 37,654."
        ),
        "non_fault_confounder": (
            "Coalescing alluvial-fan incised channels, terrace risers, Lake Lahontan highstand "
            "shorelines and piedmont road/pipeline magnetic anomalies can mimic piedmont fault "
            "lineaments and would be credited exactly as the intended targets."
        ),
        "falsifier": (
            "A live Delta >= +0.010 here while the p2b arms are null/negative falsifies the "
            "concealed-basin enrichment hypothesis (basin mass was dead weight; piedmont "
            "enrichment is the winning direction). Delta <= -0.010 corroborates the basin-deficit "
            "view. |Delta| < 0.010 is no evidence."
        ),
    },
)


def value_string(spec: dict) -> str:
    pct = 100.0 * spec["mass_frac"]
    return (
        f"tag={spec['tag']}; shift {pct:g}% R0 mass ({spec['n_shift']} dots) "
        f"{spec['donor']}->{spec['recipient']}; fixed count 37654; added d_cat>=3px"
    )


def check_s2_reservations() -> None:
    """Fail closed if any (RELIEF, tag) or hash already exists in reservations or ledger."""
    res_path = ROOT / "ledger" / "experiment_reservations.json"
    taken_tags: set[str] = set()
    if res_path.is_file():
        res = json.loads(res_path.read_text(encoding="utf-8"))
        for block in res.values():
            if isinstance(block, dict):
                taken_tags.update(block.get("occupied_tags", []))

    ledger_path = ROOT / "ledger" / "submissions.csv"
    ledger_relief_tags: set[str] = set()
    if ledger_path.is_file():
        with ledger_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (row.get("axis") or "").strip().upper() != AXIS:
                    continue
                val = row.get("value") or ""
                for spec in VARIANT_SPECS:
                    if spec["tag"] in val:
                        ledger_relief_tags.add(spec["tag"])
    collisions = sorted({s["tag"] for s in VARIANT_SPECS} & (taken_tags | ledger_relief_tags))
    if collisions:
        raise ValueError(f"duplicate experiment reservation/ledger hit: (RELIEF, {collisions})")


def existing_ledger_hashes(exclude_ids: set[str] | None = None) -> set[str]:
    return relief1.existing_ledger_hashes(exclude_ids)


def spatial_removal_report(
    parent_ys: np.ndarray,
    parent_xs: np.ndarray,
    removed_in_parent: np.ndarray,
    shape: tuple[int, int],
    dose: float,
    eligible_in_parent: np.ndarray | None = None,
    block_px: int = 50,
) -> dict:
    """Per-5 km-block removal share (Hard Constraint #5 anti-isolation instrument).

    With `eligible_in_parent` (bool over R0 dots, e.g. donor-tercile membership), shares
    are measured against each block's eligible dot count instead of its full R0 count,
    which is the evenness statistic that is meaningful for a tercile-restricted move.
    """
    bh = shape[0] // block_px + 2
    bw = shape[1] // block_px + 2
    tot = np.zeros((bh, bw))
    rem = np.zeros_like(tot)
    elig = eligible_in_parent if eligible_in_parent is not None else np.ones(len(parent_ys), dtype=bool)
    np.add.at(tot, (parent_ys[elig] // block_px, parent_xs[elig] // block_px), 1)
    np.add.at(rem, (parent_ys[removed_in_parent] // block_px, parent_xs[removed_in_parent] // block_px), 1)
    share_all = np.divide(rem, tot, out=np.zeros_like(rem), where=tot > 0)
    blown = (tot >= 5) & (share_all >= 0.9)
    lab, n_clusters = ndi.label(blown, structure=np.ones((3, 3), dtype=np.uint8))
    cluster_sizes = np.bincount(lab.ravel())[1:] if n_clusters else np.zeros(0, dtype=int)
    keep = tot >= 20
    share = share_all[keep]
    return {
        "block_px": block_px,
        "block_scale_km": block_px * 0.1,
        "eligible_blocks_20plus_dots": int(keep.sum()),
        "removed_share_mean": round(float(share.mean()), 4) if share.size else None,
        "removed_share_p05": round(float(np.percentile(share, 5)), 4) if share.size else None,
        "removed_share_p95": round(float(np.percentile(share, 95)), 4) if share.size else None,
        "removed_share_max": round(float(share.max()), 4) if share.size else None,
        "fraction_blocks_90pct_emptied": round(float((share >= 0.9).mean()), 4) if share.size else 0.0,
        "fraction_blocks_10pct_or_less": round(float((share <= 0.1).mean()), 4) if share.size else 0.0,
        "emptied_block_clusters": int(n_clusters),
        "largest_emptied_cluster_blocks": int(cluster_sizes.max()) if cluster_sizes.size else 0,
        "nominal_dose": round(float(dose), 6),
        "gate_pass": bool(
            share.size
            and (share >= 0.9).mean() <= 0.02
            and float(np.percentile(share, 5)) >= 0.25 * dose
            and (int(cluster_sizes.max()) if cluster_sizes.size else 0) <= 4
        ),
    }


def build_all() -> dict:
    t0 = time.time()
    check_s2_reservations()
    input_receipt = base_build.verify_manifest_inputs()
    template, foot, cat, r0, parent_stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)

    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    d15_pinned = base_build.read_binary(
        DATA / relief1.EXTRA_PINS["d15"], foot
    )
    rank = base_build.fifo_bfs_visit_rank(h19)
    d15_rebuilt = base_build.original_dot_thin(h19, rank, 1.5)
    if not np.array_equal(d15_pinned, d15_rebuilt):
        raise ValueError("H19-5 FIFO-BFS 1.5 thinning did not reproduce pinned d1.5")

    support = h19 & foot & ~cat
    if not np.all(~r0 | support):
        raise ValueError("R0 contains pixels outside off-catalogue H19-5 support")

    relief_idx, terciles, _cuts, relief_meta = relief1.load_relief_layers(foot)
    canary = relief1.compute_leakage_canary(foot, cat, relief_idx, seed=SEED)

    r0_tercile_counts = {k: int((r0 & m).sum()) for k, m in terciles.items()}
    r0_tercile_pct = {k: round(100.0 * v / R0_DOTS, 4) for k, v in r0_tercile_counts.items()}
    cat_tercile_pct = {
        k: round(100.0 * float((cat & m).sum()) / float(cat.sum()), 4) for k, m in terciles.items()
    }
    r0_cv_10km = round(block_density_cv(r0, foot, block_px=100), 6)
    H = r0.shape[0]
    r0_north_share = round(float(r0[: H // 2, :].sum()) / float(R0_DOTS), 6)
    parent_ys, parent_xs = np.nonzero(r0)
    parent_tercile_of_dot = np.array(
        [
            int(terciles["range_front"][y, x]) * 2 + int(terciles["piedmont"][y, x])
            for y, x in zip(parent_ys.tolist(), parent_xs.tolist())
        ],
        dtype=np.int8,
    )

    seen_hashes = existing_ledger_hashes()
    OUT.mkdir(parents=True, exist_ok=True)
    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]

    variants = []
    candidate_masks: dict[str, np.ndarray] = {"R0": r0}

    for spec in VARIANT_SPECS:
        cand_mask, stats = relief1.build_mask_for_spec(spec, r0, support, terciles, dist_cat)
        pct_changed = stats["pct_changed_symmetric"]
        mass_pct = stats["mass_shifted_pct_of_r0"]
        if not (10.0 <= mass_pct <= 15.0):
            raise ValueError(f"{spec['tag']} shifted {mass_pct:.4f}% mass (expected 10-15%)")
        if not (1.0 <= pct_changed <= 50.0):
            raise ValueError(f"{spec['tag']} changed {pct_changed:.4f}% of R0 (required 1-50%)")

        # --- region-evenness (Hard Constraint #5) -------------------------------------
        removed_mask = r0 & ~cand_mask
        removed_in_parent = removed_mask[parent_ys, parent_xs]
        donor_eligible = parent_tercile_of_dot == (
            2 if spec["donor"] == "range_front" else (1 if spec["donor"] == "piedmont" else 0)
        )
        evenness_donor = spatial_removal_report(
            parent_ys, parent_xs, removed_in_parent, r0.shape, spec["mass_frac"], donor_eligible
        )
        evenness_all = spatial_removal_report(
            parent_ys, parent_xs, removed_in_parent, r0.shape, spec["mass_frac"], None
        )
        if not evenness_donor["gate_pass"]:
            raise ValueError(
                f"{spec['tag']} fails donor-tercile region-evenness gate: {evenness_donor}"
            )
        if evenness_all["largest_emptied_cluster_blocks"] > 4:
            raise ValueError(
                f"{spec['tag']} opens a >4-block regional hole (all-block view): {evenness_all}"
            )

        slug = f"{PARENT}-{AXIS}{spec['tag']}-{DATE}"
        tmp_nan = OUT / f".{slug}-nan.tmp.tif"
        tmp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        base_build.emit(cand_mask, foot, template, slug, "nan", tmp_nan)
        base_build.emit(cand_mask, foot, template, slug, "zeros", tmp_zeros)
        nan_sha = base_build.sha256_file(tmp_nan)
        zeros_sha = base_build.sha256_file(tmp_zeros)
        if nan_sha in seen_hashes or zeros_sha in seen_hashes or nan_sha == zeros_sha:
            tmp_nan.unlink(missing_ok=True)
            tmp_zeros.unlink(missing_ok=True)
            raise ValueError(f"duplicate SHA-256 detected for {spec['tag']}")
        seen_hashes.update((nan_sha, zeros_sha))

        sha8 = nan_sha[:8]
        vid = f"{PARENT}-{AXIS}{spec['tag']}-{DATE}-{sha8}"
        nan_path = OUT / f"{vid}.tif"
        zeros_path = OUT / f"{vid}-zeros.tif"
        tmp_nan.replace(nan_path)
        tmp_zeros.replace(zeros_path)

        nan_audit = relief1.validate_relief_file(
            nan_path, cand_mask, r0, foot, cat, dist_cat, sample_path, cat_path, template, "nan"
        )
        zeros_audit = relief1.validate_relief_file(
            zeros_path, cand_mask, r0, foot, cat, dist_cat, sample_path, cat_path, template, "zeros"
        )

        pts = np.column_stack(np.nonzero(cand_mask))
        nn_dists, _ = cKDTree(pts).query(pts, k=2)
        terc_after = {k: int((cand_mask & m).sum()) for k, m in terciles.items()}
        terc_after_pct = {k: round(100.0 * v / R0_DOTS, 4) for k, v in terc_after.items()}

        donor_short = spec["donor"].replace("range_front", "range")
        recip_short = spec["recipient"].replace("range_front", "range")
        note = (
            f"{PARENT}; RELIEF {100*spec['mass_frac']:g}% ({spec['n_shift']}d) "
            f"{donor_short}->{recip_short}; pred {spec['pred_short']} DTI MODEL"
        )
        if len(note) > 140:
            raise AssertionError(f"form_note exceeds 140 chars ({len(note)}): {note}")

        parent_diff = {
            **stats,
            "tercile_dots_before": r0_tercile_counts,
            "tercile_dots_after": terc_after,
            "tercile_pct_before": r0_tercile_pct,
            "tercile_pct_after": terc_after_pct,
            "block_density_cv_10km_before": r0_cv_10km,
            "block_density_cv_10km_after": round(block_density_cv(cand_mask, foot, block_px=100), 6),
            "north_half_dot_share_before": r0_north_share,
            "north_half_dot_share_after": round(float(cand_mask[: H // 2, :].sum()) / float(R0_DOTS), 6),
            "nearest_neighbor_px_min": round(float(nn_dists[:, 1].min()), 6),
            "nearest_neighbor_px_median": round(float(np.median(nn_dists[:, 1])), 6),
            "region_evenness_donor_tercile_5km": evenness_donor,
            "region_evenness_all_blocks_5km": evenness_all,
        }
        mechanism_card = {
            "hypothesis": spec["hypothesis"],
            "mechanism": spec["mechanism"],
            "non_fault_confounder": spec["non_fault_confounder"],
            "predicted_live_change": spec["predicted_change"],
            "falsifier": spec["falsifier"],
            "structural_geologist_note": (
                "All 37,654 dots remain on the corroborated H19-5 geophysical/topographic ridge "
                "network with zero catalogue mass; no external lidar or non-lineage field was "
                "substituted. Review removed donor segments against buried/Quaternary cover and "
                "added recipient basin segments against shorelines, channels and cultural lineaments."
            ),
        }
        variants.append(
            {
                "id": vid,
                "tag": spec["tag"],
                "parent": PARENT,
                "axis": AXIS,
                "value": value_string(spec),
                "donor_tercile": spec["donor"],
                "recipient_tercile": spec["recipient"],
                "mass_shifted_fraction": spec["mass_frac"],
                "n_shift": spec["n_shift"],
                "n_dots": R0_DOTS,
                "pct_changed": pct_changed,
                "mass_shifted_pct": mass_pct,
                "removed_dots": stats["removed_dots"],
                "added_dots": stats["added_dots"],
                "retained_dots": stats["retained_dots"],
                "sha256": nan_audit["sha256"],
                "sha256_zeros": zeros_audit["sha256"],
                "status": "BUILT",
                "predicted_change": spec["predicted_change"],
                "prediction_frozen_before_proxies": True,
                "form_note": note,
                "files": {"nan": nan_audit, "zeros": zeros_audit},
                "parent_diff": parent_diff,
                "mechanism_card": mechanism_card,
            }
        )
        candidate_masks[vid] = cand_mask

    with rasterio.open(DATA / relief1.EXTRA_PINS["sgmc"]) as sgmc_ds:
        sgmc_off = foot & (sgmc_ds.read(1) > 0) & (dist_cat > 3.0)
    sgmc_tercile_pct = {
        k: round(100.0 * float((sgmc_off & m).sum()) / float(sgmc_off.sum()), 4) for k, m in terciles.items()
    }

    hide_recover_proxy = relief1.compute_spatial_block_proxy(
        candidate_masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000
    )
    hide_recover_proxy["caveat"] = (
        "R0 pruned d_cat<=2 px across the full catalogue and all newly added RELIEF dots enforce "
        "d_cat>=3 px, so withheld catalogue positives receive zero credit from newly added dots and "
        "only measure residual 2<d_cat<3 px flank retention. Historical correlation with live DTI "
        "is -0.87 to +0.54; PROXY ONLY, never a gate or score."
    )
    sgmc_proxy = relief1.compute_spatial_block_proxy(
        candidate_masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000
    )
    sgmc_proxy["caveat"] = (
        "Off-catalogue USGS SGMC geologic-map faults (d_cat > 3 px) over-represent exposed range "
        "bedrock (65.7% T3 vs 9.3% T1) because concealed basin faults are unmapped on surface "
        "quadrangles; standalone SGMC scored 0.0512 CLAIM live. PROXY ONLY, never a gate or score."
    )

    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": base_build.git_sha(),
        "generator_script": "scripts/build_relief_s2_variants.py",
        "generator_script_sha256": base_build.sha256_file(Path(__file__)),
        "session_branch": "arena/b5ea0544-gemsdoe90",
        "axis": AXIS,
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            "zeros_sha256": base_build.R0_ZEROS_SHA,
            "nan_sha256": base_build.R0_NAN_SHA,
            **parent_stats,
            "d15_rebuilt_from_h19_5": True,
            "d15_dots": int(d15_rebuilt.sum()),
            "d15_symmetric_difference_px": 0,
            "r0_tercile_dots": r0_tercile_counts,
            "r0_tercile_pct": r0_tercile_pct,
            "known_catalogue_tercile_pct": cat_tercile_pct,
            "sgmc_off_catalogue_tercile_pct": sgmc_tercile_pct,
            "r0_block_density_cv_10km": r0_cv_10km,
        },
        "relief_definition": {
            "bands_used": ["Band 12: det_elev (m)", "Band 19: det_elev_slope (deg, 3.0 km Gaussian landform smooth)"],
            **relief_meta,
        },
        "reallocation_operator": {
            "support": "off-catalogue H19-5 corroborated ridge mask (h19_5 & footprint & ~catalogue)",
            "drop_rule": "greedy minimum R=3 px triangular-kernel exclusive credit loss in donor tercile",
            "add_rule": "greedy maximum R=3 px triangular-kernel marginal credit gain in recipient tercile with Euclidean d_cat >= 3.0 px",
            "deterministic_tie_break": "(row, col) ascending",
            "seed_used_in_variant_construction": None,
            "shared_with": "src/relief.py greedy_relief_reallocate, identical to the 2026-10-23 RELIEF family",
        },
        "novelty_audit": {
            "checked_utc": "2026-10-24",
            "method": "read-only gh api contents fetch of ledger/submissions.csv in every reachable buffedlizard55-lab/GEMSDOE* repo (84-89, 91, 92; 93-101 have no ledger), plus this repo",
            "sibling_relief_rows_found": 27,
            "directions_occupied_siblings": [
                "range->piedmont", "range->basin", "piedmont->range", "basin->range",
                "pooled basin+piedmont->range", "pooled range->basin+piedmont",
            ],
            "directions_unbuilt_anywhere": ["basin->piedmont", "piedmont->basin"],
            "string_collision_hits_for_b2p_or_p2b": 0,
            "caveat": "best-effort public-repo audit, not proof of every submission the entity ever made (IR90-04/11)",
        },
        "manifest": {
            "manifest_path": "registry/data_manifest.json",
            "verified_count": len(input_receipt),
            "all_pins_rechecked": True,
            "files": input_receipt,
        },
        "proxy_reports": {
            "catalogue_hide_recover": hide_recover_proxy,
            "leakage_canary": canary,
            "sgmc_control": sgmc_proxy,
        },
        "variants": variants,
        "elapsed_s": round(time.time() - t0, 2),
        "no_live_submission": True,
        "not_committed_to_git": True,
    }


def update_ledgers_and_reservations(result: dict) -> None:
    ledger_path = ROOT / "ledger" / "submissions.csv"
    with ledger_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        existing_rows = list(reader)

    new_ids = {v["id"] for v in result["variants"]}
    kept_rows = [r for r in existing_rows if r.get("id") not in new_ids]
    for v in result["variants"]:
        kept_rows.append(
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
                    f"mass_shifted={v['mass_shifted_pct']:.2f}% ({v['n_shift']} dots {v['donor_tercile']}->"
                    f"{v['recipient_tercile']}); added min d_cat>=3px; session 2026-10-24; "
                    "receipt_score/date filled by human; agent never submits"
                ),
            }
        )

    with ledger_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept_rows)

    res_path = ROOT / "ledger" / "experiment_reservations.json"
    res = json.loads(res_path.read_text(encoding="utf-8"))
    res[RESERVATION_KEY] = {
        "checked_utc": "2026-10-24",
        "axis": AXIS,
        "parent": PARENT,
        "occupied_tags": [v["tag"] for v in result["variants"]],
        "occupied_values": [v["value"] for v in result["variants"]],
        "variant_ids": [v["id"] for v in result["variants"]],
        "novelty": "Two directed tercile pairs with zero sibling-ledger coverage in a 2026-10-24 read-only gh api audit (8 ledgers, 27 RELIEF rows); b2r deliberately not rebuilt (siblings hold b2r12/b2r15).",
        "note": "Repeat builds of these (RELIEF, value) pairs fail closed in scripts/build_relief_s2_variants.py.",
    }
    res_path.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    cards = {
        "schema_version": 1,
        "parent": PARENT,
        "session": "2026-10-24 arena/b5ea0544-gemsdoe90",
        "axis": AXIS,
        "variants": [
            {"id": v["id"], "axis": AXIS, "value": v["value"], "mechanism_card": v["mechanism_card"]}
            for v in result["variants"]
        ],
    }
    CARDS_PATH.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


def verify_all() -> int:
    base_build.verify_manifest_inputs()
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    template, foot, cat, r0, _stats = base_build.exact_parent_rebuild()
    dist_cat = ndi.distance_transform_edt(~cat)
    h19 = base_build.read_binary(DATA / base_build.PIN_PATHS["h19_5"], foot)
    support = h19 & foot & ~cat
    _relief_idx, terciles, _cuts, _meta = relief1.load_relief_layers(foot)

    sample_path = DATA / base_build.PIN_PATHS["sample_submission"]
    cat_path = DATA / base_build.PIN_PATHS["catalogue"]
    spec_by_tag = {s["tag"]: s for s in VARIANT_SPECS}
    our_ids = {v["id"] for v in receipt["variants"]}
    other_hashes = existing_ledger_hashes(exclude_ids=our_ids)

    tmp_dir = ROOT / ".cache" / "verify_relief_s2_bytes"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for v in receipt["variants"]:
        spec = spec_by_tag[v["tag"]]
        expected_mask, stats = relief1.build_mask_for_spec(spec, r0, support, terciles, dist_cat)
        if int(expected_mask.sum()) != R0_DOTS:
            raise ValueError(f"recomputed {v['id']} dot count != {R0_DOTS}")
        if abs(stats["pct_changed_symmetric"] - float(v["pct_changed"])) > 1e-6:
            raise ValueError(f"recomputed {v['id']} pct_changed mismatch")
        for mode_name in ("nan", "zeros"):
            fpath = ROOT / v["files"][mode_name]["path"]
            audit = relief1.validate_relief_file(
                fpath, expected_mask, r0, foot, cat, dist_cat, sample_path, cat_path, template, mode_name
            )
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"disk SHA-256 mismatch for {v['id']} [{mode_name}]")
            if audit["sha256"] in other_hashes:
                raise ValueError(f"hash collision with another ledger row: {v['id']} [{mode_name}]")
            tmp_path = tmp_dir / f"{v['id']}-{mode_name}.tif"
            try:
                base_build.emit(expected_mask, foot, template, v["id"], mode_name, tmp_path)
                if base_build.sha256_file(tmp_path) != audit["sha256"]:
                    raise ValueError(f"byte-for-byte deterministic re-emit failed for {v['id']} [{mode_name}]")
            finally:
                tmp_path.unlink(missing_ok=True)
        print(f"[verified] {v['id']}  {v['n_dots']} dots  {v['pct_changed']:.4f}% changed  sha256={v['sha256'][:16]}...")
    print(f"Verified {len(receipt['variants'])} RELIEF-s2 pairs against {RECEIPT_PATH.name}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--build", action="store_true")
    grp.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.build:
        result = build_all()
        RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        update_ledgers_and_reservations(result)
        print(f"Built {len(result['variants'])} RELIEF-s2 variants -> {RECEIPT_PATH.relative_to(ROOT)}")
        for v in result["variants"]:
            print(
                f"  {v['id']}: {v['n_dots']} dots | mass_shifted={v['mass_shifted_pct']:.2f}% "
                f"| sym_changed={v['pct_changed']:.3f}% | sha256={v['sha256'][:16]}..."
            )
        return 0
    return verify_all()


if __name__ == "__main__":
    raise SystemExit(main())
