#!/usr/bin/env python3
"""Build or verify three controlled SNAP variants from byte-identical R0.

SNAP value = provided vertical-gradient response, with a fixed 2 px cap,
0.10 footprint-percentile gain gate and 2.8 px separation floor.  Count and
mass stay fixed.  The 1,611 R0 pixels below 3 px from the catalogue are inherited
unchanged: these files are LOCAL ONLY until the human resolves that hard-rule
conflict.  No DrivenData access or submission is performed.

  .venv/bin/python scripts/build_snap_vertical.py --build    # once per axis/value
  .venv/bin/python scripts/build_snap_vertical.py --restore  # reproduce ignored rasters
  .venv/bin/python scripts/build_snap_vertical.py --verify   # disk + byte verification
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import build_r0_variants as parent_build  # noqa: E402
from src.dti import dti_from_arrays  # noqa: E402
from src.snap import result_statistics, snap_dots, validate_snap_file  # noqa: E402

DATA = parent_build.DATA
OUT = ROOT / "releases"
RECEIPT = ROOT / "evidence" / "snap_build_receipt.json"
LEDGER = ROOT / "ledger" / "submissions.csv"
PARENT = "h33-h33-2-b2"
AXIS = "SNAP"
DATE = "20261023"
SEED = 20261023
RADIUS = 2.0
MIN_GAIN = 0.10
MIN_SEPARATION = 2.8

VARIANT_SPECS = (
    {
        "key": "tmivg",
        "slug": "SNAPtmivg2g10s2p8",
        "bands": ("tmi_vg",),
        "response": "footprint percentile of abs(tmi_vg)",
        "value": "abs(tmi_vg) percentile; cap2px; gain>=0.10; sep>=2.8px; inherited collar fixed",
        "prediction": "+0.001",
        "hypothesis": "A small subset of R0 dots is displaced from shallow magnetic-source edges; a decisive vertical-gradient gain can re-centre those dots without the wholesale movement and spacing loss of earlier SNAP recipes.",
        "confounder": "Vertical derivatives also amplify shallow dikes, volcanic or lithologic contacts, cultural ferrous sources and gridding noise; a dipping contact's gradient maximum need not coincide with its surface fault trace.",
        "falsifier": "A paired live receipt Δ<=-0.010 versus R0 falsifies the positive magnetic re-centring hypothesis; |Δ|<0.010 is no evidence.",
    },
    {
        "key": "gravvg",
        "slug": "SNAPgravvg2g10s2p8",
        "bands": ("iso_grav_anom_vg",),
        "response": "footprint percentile of abs(iso_grav_anom_vg)",
        "value": "abs(iso_grav_anom_vg) percentile; cap2px; gain>=0.10; sep>=2.8px; inherited collar fixed",
        "prediction": "-0.002",
        "hypothesis": "Shallow density contrasts could locate a minority of misregistered dots, but gravity vertical-gradient maxima are expected to be less fault-specific than the incumbent's multiband support.",
        "confounder": "Basin-fill thickness changes, intrusive or lava margins, density layering and gravity processing can produce the same vertical-gradient crest without any fault; source dip and depth can displace the crest.",
        "falsifier": "A paired live receipt Δ>=+0.010 falsifies the predicted negative direction; |Δ|<0.010 is no evidence.",
    },
    {
        "key": "vgmean",
        "slug": "SNAPvgmean2g10s2p8",
        "bands": ("tmi_vg", "iso_grav_anom_vg"),
        "response": "equal mean of the abs(tmi_vg) and abs(iso_grav_anom_vg) footprint percentiles",
        "value": "mean abs(TMI/gravity VG) percentiles; cap2px; gain>=0.10; sep>=2.8px; inherited collar fixed",
        "prediction": "+0.002",
        "hypothesis": "Requiring a decisive gain in the average of magnetic and gravity vertical-gradient ranks suppresses single-field noise and isolates the most defensible shallow-contrast relocations while preserving R0's spacing and mass.",
        "confounder": "Magnetic and gravity edges are not independent when both express the same basin or lithologic boundary; correlated survey gridding and dipping-source offsets can still move dots away from brittle surface faults.",
        "falsifier": "A paired live receipt Δ<=-0.010 falsifies the positive consensus hypothesis; |Δ|<0.010 is no evidence.",
    },
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def predicted_text(spec: dict) -> str:
    return f"{spec['prediction']} DTI (MODEL; plausible interval -0.010 to +0.010; not a score)"


def form_note(spec: dict) -> str:
    labels = {"tmivg": "|TMI VG|", "gravvg": "|gravity VG|", "vgmean": "TMI+gravity VG mean"}
    note = (f"{PARENT}; SNAP <=2px to gated {labels[spec['key']]} edge, 2.8px spacing; "
            f"predicted {spec['prediction']} DTI MODEL")
    if len(note) > 140:
        raise AssertionError("form note exceeds 140 characters")
    return note


def check_pair_reservations() -> None:
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                if row.get("parent") == PARENT and (row.get("axis") or "").upper() == AXIS:
                    for spec in VARIANT_SPECS:
                        if row.get("value") == spec["value"]:
                            raise ValueError(f"duplicate experiment reservation: {(PARENT, AXIS, spec['value'])}")
    reservation_path = ROOT / "ledger" / "experiment_reservations.json"
    if reservation_path.exists():
        reservations = json.loads(reservation_path.read_text(encoding="utf-8"))
        occupied = set(reservations.get("snap_axis", {}).get("occupied_values", []))
        for spec in VARIANT_SPECS:
            if spec["value"] in occupied:
                raise ValueError(f"cross-session SNAP value already occupied: {spec['value']}")


def percentile_response(raw: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Exact average-tie empirical CDF of |band| over valid footprint pixels."""
    response = np.full(raw.shape, np.nan, dtype=np.float64)
    values = np.abs(raw[valid].astype(np.float64))
    if not len(values):
        raise ValueError("edge band has no valid footprint values")
    ranks = rankdata(values, method="average")
    response[valid] = (ranks - 1.0) / max(len(values) - 1.0, 1.0)
    return response


def symmetric_auc(positive: np.ndarray, negative: np.ndarray) -> float:
    """Rank-based ROC AUC with average ties; no sklearn dependency."""
    positive = np.asarray(positive, dtype=np.float64)
    negative = np.asarray(negative, dtype=np.float64)
    combined = np.concatenate([positive, negative])
    ranks = rankdata(combined, method="average")
    n_pos, n_neg = len(positive), len(negative)
    auc = (ranks[:n_pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(max(auc, 1.0 - auc))


def load_edges(footprint: np.ndarray, catalogue: np.ndarray) -> tuple[dict, dict, dict]:
    required = {band for spec in VARIANT_SPECS for band in spec["bands"]}
    responses: dict[str, np.ndarray] = {}
    band_receipt: dict[str, dict] = {}
    canary: dict[str, dict] = {}
    rng = np.random.default_rng(SEED)
    off_catalogue = footprint & ~catalogue
    off_indices = np.flatnonzero(off_catalogue)
    negative_indices = rng.choice(off_indices, size=min(250_000, len(off_indices)), replace=False)
    positive_indices = np.flatnonzero(catalogue & footprint)

    with rasterio.open(DATA / "training_features.tif") as src:
        names = [src.tags(i).get("band_name") for i in range(1, src.count + 1)]
        for band in sorted(required):
            if band not in names:
                raise ValueError(f"pinned feature stack lacks required band {band}")
            index = names.index(band) + 1
            raw = src.read(index)
            valid = footprint & np.isfinite(raw) & (raw > -3.0e38)
            responses[band] = percentile_response(raw, valid)
            # Missing/sentinel inputs are never filled or allowed as destinations.  The
            # canary uses the same seeded negative draw, filtered to valid values only.
            valid_flat = valid.ravel()
            valid_positive = positive_indices[valid_flat[positive_indices]]
            valid_negative = negative_indices[valid_flat[negative_indices]]
            if not len(valid_positive) or not len(valid_negative):
                raise ValueError(f"{band}: insufficient valid values for leakage canary")
            auc = symmetric_auc(np.abs(raw.ravel()[valid_positive]), np.abs(raw.ravel()[valid_negative]))
            canary[band] = {
                "symmetric_auc": auc,
                "n_catalogue_positive": len(valid_positive),
                "n_seeded_off_catalogue_negative": len(valid_negative),
                "threshold": 0.90,
                "triggered": auc > 0.90,
                "evidence_class": "REPORT ONLY; catalogue canary, not live performance",
            }
            band_receipt[band] = {
                "rasterio_band": index,
                "description": src.descriptions[index - 1],
                "valid_footprint_pixels": int(valid.sum()),
                "missing_or_sentinel_footprint_pixels": int((footprint & ~valid).sum()),
                "missing_value_policy": "no fill; missing origins stay fixed and missing destinations are inadmissible",
                "response_transform": "absolute value, then exact average-tie footprint percentile over valid pixels",
            }
            del raw
    if any(row["triggered"] for row in canary.values()):
        raise RuntimeError("leakage canary AUC > 0.90: stop and investigate before building")
    return responses, band_receipt, canary


def sgmc_proxy(candidate: np.ndarray, truth: np.ndarray) -> float:
    """Off-catalogue SGMC DTI under the repository's explicit metric assumptions."""
    return dti_from_arrays(candidate.astype(np.float64), truth.astype(np.float64))


def construct_candidates() -> tuple[dict, list[dict]]:
    input_receipt = parent_build.verify_manifest_inputs()
    template, footprint, catalogue, r0, parent_stats = parent_build.exact_parent_rebuild()
    distance = ndi.distance_transform_edt(~catalogue)
    responses, band_receipt, canary = load_edges(footprint, catalogue)
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m_u8.tif") as src:
        sgmc = (src.read(1) > 0) & footprint & ~catalogue & (distance > 3.0)
    if not sgmc.any():
        raise ValueError("SGMC control is empty")

    candidates = []
    parent_sgmc = sgmc_proxy(r0, sgmc)
    for spec in VARIANT_SPECS:
        response = np.mean(np.stack([responses[band] for band in spec["bands"]]), axis=0)
        allowed = footprint & ~catalogue & np.isfinite(response)
        result = snap_dots(
            r0,
            response,
            allowed,
            distance,
            radius=RADIUS,
            min_gain=MIN_GAIN,
            min_separation=MIN_SEPARATION,
            fixed_collar=3.0,
        )
        stats = result_statistics(result, r0, response)
        if stats["n_moved"] == 0:
            raise ValueError(f"{spec['key']} is not an experiment: zero dots moved")
        if stats["max_displacement_px"] > RADIUS + 1e-9:
            raise AssertionError("SNAP radius cap failed")
        candidate_sgmc = sgmc_proxy(result.candidate, sgmc)
        candidates.append({
            "spec": spec,
            "candidate": result.candidate,
            "stats": stats,
            "sgmc_proxy": candidate_sgmc,
            "sgmc_delta_proxy": candidate_sgmc - parent_sgmc,
        })

    context = {
        "template": template,
        "footprint": footprint,
        "catalogue": catalogue,
        "catalogue_distance": distance,
        "r0": r0,
        "parent_stats": parent_stats,
        "manifest_verified_count": len(input_receipt),
        "band_receipt": band_receipt,
        "canary": canary,
        "sgmc_truth_pixels": int(sgmc.sum()),
        "parent_sgmc_proxy": parent_sgmc,
    }
    return context, candidates


def mechanism_card(spec: dict) -> dict:
    return {
        "hypothesis": spec["hypothesis"],
        "mechanism": (
            f"Response = {spec['response']}. Only a dot whose Euclidean <=2 px window contains a "
            f"currently admissible destination at least {MIN_GAIN:.2f} response percentile higher can move. "
            "Proposals are gain-ordered; every destination must be in-footprint, off-catalogue, at least "
            "3 px from the catalogue, finite, and no closer than 2.8 px to another final dot. R0's inherited "
            "sub-3 px pixels remain fixed. Unit mass and 37,654-dot count are unchanged, so this is a position "
            "experiment rather than MASS, PRUNE or CONCENTRATION."
        ),
        "non_fault_process_that_could_mimic": spec["confounder"],
        "predicted_live_change": predicted_text(spec),
        "falsifier": spec["falsifier"],
        "structural_geologist_note": (
            "A vertical-derivative maximum is a potential-field source-edge locator, not direct evidence "
            "of brittle faulting. Review relocated dots against mapped geology, dipping contacts and "
            "non-fault shallow sources before interpreting any receipt."
        ),
    }


def ledger_hash_conflicts(nan_sha: str, zeros_sha: str, own_id: str | None = None) -> list[str]:
    conflicts = []
    if not LEDGER.exists():
        return conflicts
    with LEDGER.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if own_id and row.get("id") == own_id:
                continue
            recorded = {row.get("sha256", ""), row.get("sha256_zeros", "")}
            recorded = {value for value in recorded if value}
            if nan_sha in recorded or zeros_sha in recorded:
                conflicts.append(row.get("id", "(unnamed)"))
            if any(value.startswith(nan_sha[:8]) or value.startswith(zeros_sha[:8]) for value in recorded):
                conflicts.append(row.get("id", "(unnamed)") + " (sha8 prefix)")
    return conflicts


def base_result(context: dict) -> dict:
    return {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha_at_build": parent_build.git_sha(),
        "generator_script_sha256": sha256_file(Path(__file__)),
        "snap_module_sha256": sha256_file(ROOT / "src" / "snap.py"),
        "axis": AXIS,
        "recipe": {
            "radius_px": RADIUS,
            "minimum_response_gain_percentile": MIN_GAIN,
            "minimum_nearest_neighbour_separation_px": MIN_SEPARATION,
            "seed_for_canary_only": SEED,
            "count": parent_build.R0_DOTS,
            "assignment": "gain-descending deterministic greedy; unprocessed origins reserved; response/displacement/raster tie-breaks",
            "collar_policy": "R0 d_cat<3 px pixels fixed; all moved origins and destinations d_cat>=3 px; every final dot retains R0's d_cat>2 px exclusion",
        },
        "parent": {
            "id": PARENT,
            "claimed_live_score": 0.2778,
            "evidence_class": "CLAIM",
            **context["parent_stats"],
        },
        "manifest": {
            "path": "registry/data_manifest.json",
            "verified_count": context["manifest_verified_count"],
            "all_sha256_matched": True,
        },
        "edge_bands": context["band_receipt"],
        "hard_constraint_status": {
            "format_and_zero_catalogue_mass": "PASS",
            "general_minimum_3px_from_catalogue": "FAIL_INHERITED_FROM_R0",
            "near_catalogue_dot_count": int((context["r0"] & (context["catalogue_distance"] < 3)).sum()),
            "new_near_catalogue_mass": 0,
            "upload_eligible": False,
            "reason": "Literal SNAP cap 2 px cannot move every inherited sub-3 px dot to a legal destination; no PRUNE/refill edit was silently added.",
        },
        "proxy_reports": {
            "catalogue_hide_recover": {
                "status": "NOT RUN",
                "reason": "R0 was pruned using the full catalogue; no fold-clean recovery instrument is validated for this positional comparison. Never a gate or score.",
            },
            "leakage_canary": {"status": "REPORT ONLY", "seed": SEED, "bands": context["canary"]},
            "sgmc_control": {
                "status": "REPORT ONLY PROXY under src/dti.py assumptions; not a live score",
                "truth": "pinned USGS SGMC proxy pixels outside catalogue and >3 px from it",
                "n_truth_pixels": context["sgmc_truth_pixels"],
                "parent_proxy": context["parent_sgmc_proxy"],
            },
        },
        "no_live_submission": True,
        "competition_rasters_committed_to_git": False,
    }


def build() -> dict:
    check_pair_reservations()
    context, candidates = construct_candidates()
    OUT.mkdir(parents=True, exist_ok=True)
    result = base_result(context)
    records = []
    for item in candidates:
        spec, mask, stats = item["spec"], item["candidate"], item["stats"]
        slug = f"{PARENT}-{spec['slug']}-{DATE}"
        temp_nan = OUT / f".{slug}-nan.tmp.tif"
        temp_zeros = OUT / f".{slug}-zeros.tmp.tif"
        parent_build.emit(mask, context["footprint"], context["template"], slug, "nan", temp_nan)
        parent_build.emit(mask, context["footprint"], context["template"], slug, "zeros", temp_zeros)
        nan_sha, zeros_sha = sha256_file(temp_nan), sha256_file(temp_zeros)
        conflicts = ledger_hash_conflicts(nan_sha, zeros_sha)
        if conflicts:
            raise ValueError(f"candidate hash already appears in ledger: {conflicts}")
        base = OUT / f"{slug}-{nan_sha[:8]}"
        nan_path = base.with_suffix(".tif")
        zeros_path = OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        audits = {}
        for mode, path in (("nan", nan_path), ("zeros", zeros_path)):
            audit = validate_snap_file(
                path,
                expected=mask,
                parent=context["r0"],
                footprint=context["footprint"],
                catalogue=context["catalogue"],
                catalogue_distance=context["catalogue_distance"],
                sample_profile=context["template"],
                mode=mode,
            )
            audit["path"] = str(path.relative_to(ROOT))
            audit["sha256"] = sha256_file(path)
            audit["bytes"] = path.stat().st_size
            audits[mode] = audit
        if audits["nan"]["sha256"] != nan_sha or audits["zeros"]["sha256"] != zeros_sha:
            raise AssertionError("disk re-read changed a candidate hash")
        records.append({
            "id": base.name,
            "parent": PARENT,
            "axis": AXIS,
            "value": spec["value"],
            "response": spec["response"],
            "bands": list(spec["bands"]),
            "n_dots": stats["n_dots"],
            "pct_changed": stats["pct_changed"],
            "parent_diff": stats,
            "sha256": nan_sha,
            "sha256_zeros": zeros_sha,
            "status": "BUILT",
            "upload_eligible": False,
            "predicted_change": predicted_text(spec),
            "form_note": form_note(spec),
            "files": audits,
            "mechanism_card": mechanism_card(spec),
            "sgmc_control_proxy": item["sgmc_proxy"],
            "sgmc_control_delta_proxy": item["sgmc_delta_proxy"],
        })
    result["variants"] = records
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    append_ledger(records)
    (ROOT / "ledger" / "mechanism_cards_snap.json").write_text(json.dumps({
        "schema_version": 1,
        "parent": PARENT,
        "axis": AXIS,
        "variants": [{"id": row["id"], "value": row["value"], "mechanism_card": row["mechanism_card"]} for row in records],
    }, indent=2) + "\n", encoding="utf-8")
    return result


def append_ledger(records: list[dict]) -> None:
    with LEDGER.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise ValueError("ledger has no header")
    for record in records:
        rows.append({
            "id": record["id"],
            "site": "GEMSDOE90",
            "name": record["id"],
            "score": "",
            "evidence_class": "MODEL (predicted change only)",
            "encoding": "nan primary; zeros fallback; LOCAL ONLY pending collar-rule resolution",
            "n_dots": record["n_dots"],
            "pct_changed": f"{record['pct_changed']:.6f}",
            "sha256": record["sha256"],
            "sha256_zeros": record["sha256_zeros"],
            "parent": PARENT,
            "axis": AXIS,
            "value": record["value"],
            "status": "BUILT",
            "receipt": "N",
            "receipt_score": "",
            "predicted_change": record["predicted_change"],
            "date": "",
            "form_note": record["form_note"],
            "notes": "SNAP moved-dot percent; inherited R0 sub-3px collar unchanged; human must resolve before upload; agent never submits",
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify_or_restore(restore: bool) -> dict:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    context, candidates = construct_candidates()
    by_key = {item["spec"]["key"]: item for item in candidates}
    spec_by_key = {spec["key"]: spec for spec in VARIANT_SPECS}
    if len(receipt["variants"]) != len(VARIANT_SPECS):
        raise ValueError("receipt variant count mismatch")
    for record in receipt["variants"]:
        key = next((key for key, spec in spec_by_key.items() if spec["value"] == record["value"]), None)
        if key is None:
            raise ValueError(f"receipt value is not a declared recipe: {record['value']}")
        item = by_key[key]
        mask, stats = item["candidate"], item["stats"]
        if abs(stats["pct_changed"] - float(record["pct_changed"])) > 1e-9:
            raise ValueError(f"parent diff drifted for {record['id']}")
        if stats["n_dots"] != record["n_dots"]:
            raise ValueError(f"count drifted for {record['id']}")
        if ledger_hash_conflicts(record["sha256"], record["sha256_zeros"], own_id=record["id"]):
            raise ValueError(f"hash collision with another ledger row for {record['id']}")
        for mode in ("nan", "zeros"):
            relative = Path(record["files"][mode]["path"])
            target = ROOT / relative
            expected_sha = record["files"][mode]["sha256"]
            if expected_sha != record["sha256" if mode == "nan" else "sha256_zeros"]:
                raise ValueError(f"receipt hash fields disagree for {record['id']} {mode}")
            temp = ROOT / ".cache" / "snap_verify" / f"{record['id']}-{mode}.tif"
            temp.parent.mkdir(parents=True, exist_ok=True)
            parent_build.emit(mask, context["footprint"], context["template"], record["id"], mode, temp)
            if sha256_file(temp) != expected_sha:
                raise ValueError(f"deterministic re-emit hash mismatch for {record['id']} {mode}")
            if restore:
                target.parent.mkdir(parents=True, exist_ok=True)
                temp.replace(target)
            else:
                temp.unlink()
                if not target.is_file():
                    raise FileNotFoundError(f"candidate missing; run --restore: {target}")
            audit = validate_snap_file(
                target,
                expected=mask,
                parent=context["r0"],
                footprint=context["footprint"],
                catalogue=context["catalogue"],
                catalogue_distance=context["catalogue_distance"],
                sample_profile=context["template"],
                mode=mode,
            )
            if sha256_file(target) != expected_sha:
                raise ValueError(f"on-disk hash mismatch for {target}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--restore", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.build:
        result = build()
        print(f"Built {len(result['variants'])} LOCAL-ONLY SNAP variants; no submission")
    elif args.restore:
        result = verify_or_restore(restore=True)
        print(f"Restored and verified {len(result['variants'])} SNAP variant pairs from pinned inputs")
    else:
        result = verify_or_restore(restore=False)
        print(f"Verified {len(result['variants'])} SNAP variant pairs from disk and deterministic re-emission")
    for row in result["variants"]:
        stats = row.get("parent_diff", {})
        moved = stats.get("n_moved", "?")
        mean = stats.get("mean_displacement_px_all_dots", float("nan"))
        print(f"  {row['id']}: moved={moved}, mean_disp={mean:.4f}px, sha256={row['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
