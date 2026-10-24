#!/usr/bin/env python3
"""Continuity-aware MASS arms from the byte-identical R0: the shadow ladder's
missing corner.

Session axis: MASS (agent-selected under the brief's delegation -- the human
said "pick your own session; do not prompt me over choosing an Axis"). Why not
an axis with no in-repo rows: a fresh read-only audit on 2026-10-23 of every
sibling ledger (GEMSDOE84-92, `gh api`, no DrivenData contact) found all seven
brief axes already built (PRUNE 68 rows, SNAP 58, MASS 44, CONCENTRATION 33,
RELIEF 27, SPACING 16, TRACKB 9) with **zero receipts anywhere**, and the
brief-literal CONCENTRATION direction (lowest-prior -> highest-prior blocks)
already built at 0.8/1/5 km and 10/50 px blocks, 10/15/20 % -- with the
GEMSDOE86 reconciliation reading every upward arm at <= 0 on its SGMC MODEL
(-0.0005..-0.0150) and GEMSDOE84 holding its CONCENTRATION files for collar
breaches. No repository, this one included, has a continuity-protected MASS
removal. That pair is built here; the audit is recorded in the receipt and in
`ledger/experiment_reservations.json`.

New (AXIS, value) pairs only, all deletion-only strict subsets of R0
(h33-h33-2-b2, 37,654 unit dots), at the exact removal counts of the recorded
shadow ladder so every comparison is matched-count:

  shadowcont-drop 20%  delete 7,531 dots  -> 30,123 dots
  shadowcont-drop 30%  delete 11,296 dots -> 26,358 dots
  shadowcont-drop 40%  delete 15,062 dots -> 22,592 dots

Ranking: ascending exclusive 300 m kernel credit, recomputed after each
deletion (`src/mass.py`) -- identical to the shadow ladder -- plus one
eligibility rule (`src/continuity.py`): a dot in an R0 strand of >= 10 dots
linked at <= 6 px (the kernel diameter) may not be removed while it is an
articulation point of that strand's alive subgraph, nor once the strand is
down to 10 alive dots. Every R0 strand therefore survives whole, where the
recorded shadow 40 % arm keeps 0 of 838 strands on the 5 px instrument and
the random 40 % control keeps 136. The measured credit price of the
constraint is small (+2.7/+5.8/+7.4 % exclusive credit vs shadow at
20/30/40 %; the 40 % arm still destroys less credit than random-40), so this
session separates "credit saved" from "continuity kept" at near-constant
credit -- the comparison SLOT_PLAN proposed as CONTINUITY_AWARE_DOSE and no
session had built.

No truth, no label, no catalogue distance, no feature band and no score
enters the ranking, so this is not label probing. Nothing is added or moved;
the catalogue collar is inherited unchanged (changing it would be a second
axis). Rasters go to ignored `releases/` and must not be committed (public
repo). The agent never submits.

Run:    .venv/bin/python scripts/build_mass_continuity.py --build
Verify: .venv/bin/python scripts/build_mass_continuity.py --verify
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_mass_high_dose as hd     # noqa: E402  region gate + strand instrument
import build_mass_shadow as shadow    # noqa: E402  audited format gate + bracket model
import build_r0_variants as b         # noqa: E402  audited exact-R0 rebuild path
import build_relief_variants as relief_build  # noqa: E402  report-only PROXY instrument
from src import continuity, mass      # noqa: E402
from src.validate import validate as format_validate  # noqa: E402

PARENT = "h33-h33-2-b2"
AXIS = "MASS"
DATE = "20261023"
R0_DOTS = 37_654
SEED = 20261023  # PROXY bootstrap / holdout only; variant construction is deterministic
OUT = ROOT / "releases"
RECEIPT = ROOT / "evidence" / "mass_continuity_receipt.json"
LEDGER = ROOT / "ledger" / "submissions.csv"
RESERVATIONS = ROOT / "ledger" / "experiment_reservations.json"
R0_NAN_SHA = "baeae3219bba6a19bc8cfe79224e28555c50184b7c1ca65c2a822f54807c77dd"
R0_ZEROS_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"

DOSES = (20, 30, 40)
LINK_PX = continuity.LINK_PX_DEFAULT            # 6.0 px = kernel diameter
MIN_STRAND = continuity.MIN_STRAND_DOTS_DEFAULT  # 10 dots ~ >= 1 km instrument

# Recorded unconstrained ladder at matched counts (re-derived in build() and
# asserted against these receipts; never fitted to a score -- no MASS dose
# anywhere has a receipt).
SHADOW_RECEIPTS = ("evidence/mass_build_receipt.json", "evidence/mass_high_dose_receipt.json")

FIELDS = ["id", "site", "name", "score", "evidence_class", "encoding", "n_dots", "pct_changed",
          "sha256", "sha256_zeros", "parent", "axis", "value", "status", "receipt",
          "receipt_score", "predicted_change", "date", "form_note", "notes"]

# Distinct MASS values found in the 2026-10-23 read-only sibling audit
# (GEMSDOE84-92 ledgers via gh api; this repo's rows included). None carries a
# continuity / strand / articulation rule; "shadowcont" appears nowhere.
SIBLING_MASS_VALUES = [
    "+10pct", "-10pct", "-20pct", "MASS_A10", "MASS_D10", "MASS_SWAP10",
    "add20pct-next", "add5pct-next", "cons1drop", "cons2drop", "cons3add",
    "drop5pct-tail", "m10e", "m10minus", "m10plus", "m10rand", "m10u",
    "m10uniq", "m20minus", "m20uniq", "minus10pct", "minus10pct-marginal",
    "p10", "plus10pct", "plus10pct-extend", "plus10pct-extend-rand",
    "r10minus", "r10plus", "r10swap",
    "random-drop 40% (seeded 20261023, credit-blind, no additions)",
    "shadow-drop 10% (exclusive-credit greedy, no additions)",
    "shadow-drop 20% (exclusive-credit greedy, no additions)",
    "shadow-drop 30% (exclusive-credit greedy, no additions)",
    "shadow-drop 40% (exclusive-credit greedy, no additions)",
    "shadow-drop 48% (exclusive-credit greedy, no additions)",
]


def removal_count(pct: int) -> int:
    return int(round(pct / 100.0 * R0_DOTS))


def value_of(pct: int) -> str:
    return f"shadowcont-drop {pct}% (exclusive-credit greedy + 6px strand protection, no additions)"


def recorded_shadow() -> dict[int, dict]:
    """Matched-dose unconstrained reference, read from the recorded receipts."""
    out: dict[int, dict] = {}
    for rel in SHADOW_RECEIPTS:
        receipt = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        for v in receipt["variants"]:
            if v.get("selection_rule", "shadow") != "shadow" and "shadow-drop" not in v.get("value", ""):
                continue
            if "shadow-drop" not in v.get("value", ""):
                continue
            pct = int(round(100.0 * v["removed_dots"] / R0_DOTS))
            if pct in DOSES and v["removed_dots"] == removal_count(pct):
                out[pct] = {
                    "id": v["id"],
                    "exclusive_credit_sum": float(v["removal_statistics"]["exclusive_credit_sum"]),
                    "point_prediction_dti": float(v.get("point_prediction_dti", float("nan"))),
                    "predicted_change": v["predicted_change"],
                    "receipt": rel,
                }
    missing = [p for p in DOSES if p not in out]
    if missing:
        raise ValueError(f"recorded shadow ladder is missing doses {missing}; cannot anchor predictions")
    # mass_build_receipt stores the point inside the prediction string only.
    points = {20: 0.009, 30: 0.012, 40: 0.014}
    for pct, ref in out.items():
        if not math.isfinite(ref["point_prediction_dti"]):
            ref["point_prediction_dti"] = points[pct]
    return out


def check_reservations() -> None:
    """Fail closed if a shadowcont (MASS, value) pair was already built anywhere indexed."""
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if (row.get("axis") or "").upper() != AXIS:
                    continue
                if "shadowcont" in ((row.get("value") or "") + (row.get("id") or "")).lower():
                    raise ValueError(
                        f"duplicate experiment reservation: shadowcont already in ledger as {row.get('id')}")
    if RESERVATIONS.exists():
        data = json.loads(RESERVATIONS.read_text(encoding="utf-8"))
        data.pop("mass_continuity_20261023", None)  # this session's own block, written with the docs
        if "shadowcont" in json.dumps(data).lower():
            raise ValueError("duplicate experiment reservation: shadowcont already recorded in reservations")
    for taken in SIBLING_MASS_VALUES:
        if "shadowcont" in taken.lower():
            raise ValueError("sibling audit already contains a shadowcont value; refusing to rebuild")


def build() -> dict:
    t0 = time.time()
    input_receipt = b.verify_manifest_inputs()                          # all 26 pins rechecked
    template, foot, cat, r0, parent_stats = b.exact_parent_rebuild()    # byte-identical R0
    if parent_stats["r0_rebuilt_zeros_sha256"] != R0_ZEROS_SHA or \
            parent_stats["r0_rebuilt_nan_sha256"] != R0_NAN_SHA:
        raise ValueError("R0 rebuild is not the recorded parent; stopping (never approximate the parent)")
    footprint_px = int(foot.sum())
    distance_cat = ndi.distance_transform_edt(~cat)
    ys, xs = np.nonzero(r0)
    if len(ys) != R0_DOTS:
        raise ValueError(f"R0 dot count {len(ys)} != {R0_DOTS}")
    pts = np.column_stack([ys, xs]).astype(float)
    credit_neighbours = mass.neighbour_lists(pts)
    credit0 = mass.all_exclusive_credit(pts, credit_neighbours, np.ones(len(pts), dtype=bool))
    link_adjacency, comp, comp_sizes = continuity.link_graph(pts, link_px=LINK_PX)

    counts = {p: removal_count(p) for p in DOSES}
    snapshots = tuple(counts[p] for p in DOSES)

    # Continuity-aware greedy (the session's ranking) and, for REPORT-ONLY
    # matched-count comparison, the unconstrained greedy re-derived on the
    # same parent. The unconstrained credit sums must reproduce the recorded
    # ladder receipts, which pins both rankings to the same code path.
    cont = continuity.greedy_continuity_removal(
        pts, credit_neighbours, link_adjacency, comp, comp_sizes,
        n_remove=counts[40], snapshots=snapshots,
    )
    uncon = mass.greedy_shadow_removal(pts, credit_neighbours, n_remove=counts[40], snapshots=snapshots)
    shadow_ref = recorded_shadow()
    for pct in DOSES:
        got = float(uncon["credit_at_removal"][:counts[pct]].sum())
        want = shadow_ref[pct]["exclusive_credit_sum"]
        if not math.isclose(got, want, rel_tol=1e-9):
            raise ValueError(f"unconstrained re-derivation drifted at {pct}%: {got} != recorded {want}")

    rand_mask_40 = np.zeros(R0_DOTS, dtype=bool)
    rand_mask_40[hd.random_removal(R0_DOTS, counts[40])] = True
    rand_credit_40 = float(credit0[rand_mask_40].sum())

    parent_strand5 = hd.strand_report(r0)
    sample_path = str(b.DATA / b.PIN_PATHS["sample_submission"])
    catalogue_path = str(b.DATA / b.PIN_PATHS["catalogue"])

    OUT.mkdir(parents=True, exist_ok=True)
    variants = []
    candidate_masks: dict[str, np.ndarray] = {"R0": r0}
    for pct in DOSES:
        n_rem = counts[pct]
        removed = cont["removed_masks"][n_rem]
        candidate = r0.copy()
        candidate[ys[removed], xs[removed]] = False
        n_dots = int(candidate.sum())
        if n_dots != R0_DOTS - n_rem:
            raise AssertionError(f"shadowcont {pct}%: {n_dots} dots != {R0_DOTS - n_rem}")
        changed = int(np.count_nonzero(candidate ^ r0))
        pct_changed = 100.0 * changed / R0_DOTS
        if not 1.0 <= pct_changed <= 50.0:
            raise ValueError(f"shadowcont {pct}% changes {pct_changed:.4f}% of R0 (required 1-50%)")
        if np.any(candidate & ~r0) or np.any(candidate & cat) or np.any(candidate & ~foot):
            raise AssertionError(f"shadowcont {pct}% is not a catalogue-clean subset of R0")
        spatial = hd.spatial_removal_report(removed, ys, xs, r0.shape, pct / 100.0)
        spatial["passes_region_evenness_gate"] = hd.region_evenness_gate(spatial)
        if not spatial["passes_region_evenness_gate"]:
            raise ValueError(f"shadowcont {pct}% fails the region-evenness gate: {spatial}")

        credit_sum = float(cont["credit_at_removal"][:n_rem].sum())
        shadow_credit = float(uncon["credit_at_removal"][:n_rem].sum())
        credit_ratio = credit_sum / shadow_credit
        # MODEL prediction, repo convention: the recorded ladder point scaled
        # by the matched-count credit ratio (the same scaling the high-dose
        # session applied to its random control), bracketed by the
        # first-order formula over the unobservable c and |G| ranges.
        point = shadow_ref[pct]["point_prediction_dti"] / credit_ratio
        bracket = shadow.bracket_delta(credit_sum, n_rem, footprint_px)
        low, high = min(bracket["low"], point), max(bracket["high"], point)
        pred_text = f"{point:+.3f} DTI (MODEL; bracket {low:+.3f} to {high:+.3f}; not a score)"

        slug = f"{PARENT}-MASSshadowcont{pct}pct-{DATE}"
        temp_nan, temp_zeros = OUT / f".{slug}-nan.tmp.tif", OUT / f".{slug}-zeros.tmp.tif"
        b.emit(candidate, foot, template, slug, "nan", temp_nan)
        b.emit(candidate, foot, template, slug, "zeros", temp_zeros)
        sha8 = b.sha256_file(temp_nan)[:8]
        base = OUT / f"{slug}-{sha8}"
        nan_path, zeros_path = base.with_suffix(".tif"), OUT / f"{base.name}-zeros.tif"
        temp_nan.replace(nan_path)
        temp_zeros.replace(zeros_path)
        nan_audit = shadow.validate_candidate(nan_path, candidate, foot, cat, template, "nan", r0, distance_cat)
        zeros_audit = shadow.validate_candidate(zeros_path, candidate, foot, cat, template, "zeros", r0, distance_cat)
        for path, zeros_mode in ((nan_path, False), (zeros_path, True)):
            report = format_validate(str(path), sample_path, catalogue_path, zeros_outside=zeros_mode)
            if not report["pass"]:
                raise ValueError(f"src.validate format gate failed for {path.name}: {report['fails']}")

        survival6 = continuity.strand_survival(link_adjacency, comp, comp_sizes, ~removed)
        if survival6["strands_surviving_whole"] != survival6["protected_strands"]:
            raise AssertionError(f"shadowcont {pct}% broke its own strand guarantee: {survival6}")
        uncon_removed = uncon["removed_masks"][n_rem]
        structure = {
            "parent_strand_report_5px": parent_strand5,
            "candidate_strand_report_5px": hd.strand_report(candidate),
            "strand_survival_6px": survival6,
            "unconstrained_shadow_strand_survival_6px": continuity.strand_survival(
                link_adjacency, comp, comp_sizes, ~uncon_removed),
        }
        if pct == 40:
            structure["random40_strand_survival_6px"] = continuity.strand_survival(
                link_adjacency, comp, comp_sizes, ~rand_mask_40)
            structure["random40_strand_report_5px_note"] = (
                "recorded in evidence/mass_high_dose_receipt.json: 136 strands >= 10 dots at 5 px")

        cand5 = structure["candidate_strand_report_5px"]
        cards = {
            "hypothesis": (
                f"Deleting the {pct}% lowest-exclusive-credit dots of R0 under a rule that forbids "
                "splitting any >= 1 km kernel-continuous strand keeps the shadow ladder's mass saving "
                "while preserving the along-strike coverage line-like truth is paid for, so live DTI "
                "should match or beat the unconstrained shadow arm at the same count."
            ),
            "mechanism": (
                "DTI = T / (0.2T + 0.2(S-M) + 0.8|G|) charges 0.2 per dot but credits T once per truth "
                "pixel (max over dots inside the 300 m triangular kernel). The shadow ranking removes "
                "dots whose disks neighbours already cover -- but those are disproportionately the "
                "interior dots of densely sampled strands, so at 40% it keeps 0 of R0's 838 strands of "
                ">= 10 dots at 5 px linking and pushes mean spacing to 6.19 px, beyond the kernel. "
                "For line-like truth the brief's own algebra lowers the per-dot bar (a dot pays iff its "
                "credit exceeds ~0.2*DTI, less for lines), so a strand sampled every ~5-6 px still "
                "covers every truth pixel while paying roughly half the mass of R0's ~2.8-3 px "
                "sampling. This arm keeps the identical credit ranking and dose, but a dot inside an "
                "R0 strand of >= 10 dots linked at <= 6 px (kernel diameter: linked disks touch) is "
                "ineligible while it is an articulation point of the strand or the strand is at its "
                f"10-dot floor. All {survival6['protected_strands']} strands survive whole at 6 px; "
                f"the measured price is {credit_ratio - 1:+.1%} exclusive credit vs the unconstrained "
                f"arm at matched count (E={credit_sum:.0f} vs {shadow_credit:.0f})."
            ),
            "non_fault_confounder": (
                "Continuity is geometric, not geological: unfaulted dikes, resistant stratigraphic "
                "hogbacks, drainage divides and Lake Lahontan shoreline berms also form >= 1 km "
                "corridors in the H19-5 support, and protection preserves their mass with the same "
                "force as a real fault's. Conversely the dots protection forces out instead -- short "
                "fragments and isolated dots -- may be the sole coverage of short genuine strands "
                "(relay tips, step-over splays shorter than 1 km). A negative receipt cannot by itself "
                "separate 'strands were non-fault lineaments' from 'short fragments were real'."
            ),
            "competing_prediction": (
                "The credit model alone ranks this arm strictly below its unconstrained twin: it "
                f"destroys {credit_ratio - 1:+.1%} more exclusive credit at the same count, hence the "
                f"point prediction is scaled down to {point:+.3f} from the shadow arm's "
                f"{shadow_ref[pct]['point_prediction_dti']:+.3f} (both MODEL). The structural reading "
                f"points the other way: on the legacy 5 px instrument this arm keeps "
                f"{cand5['strands_ge_10dots']} strands of >= 10 dots (unconstrained shadow keeps 0 at "
                f"40%, random keeps 136) and on the 6 px kernel-continuity instrument it keeps all "
                f"{survival6['protected_strands']} strands connected. If new-fault truth is line-like, "
                "the continuity term can outweigh a single-digit credit penalty; if truth is "
                "effectively point-like at 100 m sampling, it cannot. Both readings are recorded "
                "before any receipt; |delta| < 0.010 on public chunks is no evidence either way."
            ),
            "predicted_live_change": pred_text,
            "model_bracket": (
                f"first-order bracket {bracket['low']:+.4f} to {bracket['high']:+.4f} DTI over removed-dot "
                f"credit c in {list(shadow.C_BRACKET)} and truth pixels in {list(shadow.G_BRACKET)} "
                "(src/mass.predicted_removal_delta); point = recorded shadow point scaled by the "
                "matched-count credit ratio. Assumptions, not measurements."
            ),
            "falsifier": (
                "Paired same-week live receipts decide, with |delta| < 0.010 = no evidence throughout: "
                "(i) delta vs R0 <= -0.010 falsifies the dose direction for the protected ranking; "
                "(ii) at matched count, shadowcont minus shadow >= +0.010 shows continuity pays beyond "
                "credit and the protected ranking replaces the ladder; shadowcont minus shadow "
                "<= -0.010 shows the credit term is all there is and protection is abandoned; "
                "(iii) if the credit-blind random-40 control beats both ranked arms by >= 0.010, every "
                "exclusive-credit ranking in this repo is wrong, not just this one."
            ),
            "structural_geologist_note": (
                "Map the survivors, not just the deletions. By construction every >= 1 km R0 strand "
                "remains a single kernel-continuous trace (gaps <= 600 m); what left is strand-interior "
                "redundancy, short < 1 km fragments and isolated dots. Where a surviving strand follows "
                "a mappable range-front or a step-over between catalogue traces, the protection did "
                "geological work; where it follows a shoreline, a contact or a drainage divide for "
                "kilometres, it preserved false mass and a negative receipt should be believed. "
                "Check also the deleted short fragments at fault tips: if they systematically sit in "
                "0.3-2.5 km along-strike cones ahead of mapped terminations, the 10-dot floor is "
                "mis-set for relay geometry, which is a different (unbuilt) axis."
            ),
        }
        note = (f"{PARENT}; MASS shadowcont-drop {pct}% -> {n_dots} dots, all >=1km strands kept; "
                f"predicted {point:+.3f} MODEL")
        if len(note) > 140:
            raise AssertionError(f"form note is {len(note)} chars: {note}")
        variants.append({
            "id": base.name,
            "parent": PARENT,
            "axis": AXIS,
            "value": value_of(pct),
            "selection_rule": "shadowcont",
            "dose_pct": pct,
            "ranking": ("ascending exclusive 300 m kernel credit, recomputed after each deletion "
                        "(src/mass.py), with 6 px articulation + 10-dot strand-floor eligibility "
                        "(src/continuity.py)"),
            "seed": None,
            "n_dots": n_dots,
            "pct_changed": pct_changed,
            "removed_dots": n_rem,
            "added_dots": 0,
            "moved_dots": 0,
            "retained_dots": n_dots,
            "sha256": nan_audit["sha256"],
            "sha256_zeros": zeros_audit["sha256"],
            "status": "BUILT",
            "evidence_class": "MODEL (predicted change only)",
            "predicted_change": pred_text,
            "point_prediction_dti": round(point, 4),
            "model_bracket": {"low": round(float(low), 4), "high": round(float(high), 4),
                              "formula_bracket": bracket,
                              "basis": ("recorded shadow point scaled by matched-count credit ratio; "
                                        "bracket from the first-order credit term over unobservable "
                                        "c and |G|. Assumptions, not measurements.")},
            "form_note": note,
            "files": {"nan": nan_audit, "zeros": zeros_audit},
            "parent_diff": {
                "removed_from_parent": n_rem, "added": 0, "moved": 0, "retained_parent": n_dots,
                "symmetric_difference_px": changed, "pct_changed_of_R0": pct_changed,
            },
            "removal_statistics": {
                "exclusive_credit_sum": credit_sum,
                "exclusive_credit_mean": credit_sum / n_rem,
                "exclusive_credit_max": float(cont["credit_at_removal"][:n_rem].max()),
                "unconstrained_shadow_credit_sum_same_count": shadow_credit,
                "credit_ratio_vs_shadow": credit_ratio,
                "r0_total_exclusive_credit": float(credit0.sum()),
                "share_of_r0_credit_removed": credit_sum / float(credit0.sum()),
                "min_catalogue_distance_px_inherited": nan_audit["min_catalogue_distance_px"],
                "sub3px_dots_removed": int((distance_cat[ys[removed], xs[removed]] < 3.0).sum()),
                "sub3px_dots_in_parent": int((distance_cat[ys, xs] < 3.0).sum()),
            },
            "spatial_removal": spatial,
            "structure_report_only": structure,
            "mechanism_card": cards,
        })
        candidate_masks[base.name] = candidate

    # REPORT-ONLY instruments (brief s6): never gates, never used to rank.
    with rasterio.open(b.DATA / "external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc_off = foot & (ds.read(1) > 0) & (distance_cat > 3.0)
    hide_recover = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, cat, holdout_quarter=True, seed=SEED, block_px=200, n_boot=1000)
    hide_recover["caveat"] = (
        "R0 was pruned at d_cat > 2 px against the FULL catalogue, so withheld catalogue positives "
        "can only earn credit from the 1,611 inherited 2-3 px flank dots; the instrument mostly "
        "rewards retaining near-catalogue mass, which a deletion ladder removes only incidentally. "
        "Ledger history: this holdout correlated -0.87 to +0.54 with live scores (n = 12-14). "
        "PROXY ONLY -- reported because the brief requires it, never a gate, never a ranking, "
        "never called a score."
    )
    sgmc_proxy = relief_build.compute_spatial_block_proxy(
        candidate_masks, foot, sgmc_off, holdout_quarter=False, seed=SEED, block_px=200, n_boot=1000)
    sgmc_proxy["caveat"] = (
        "Off-catalogue USGS SGMC geologic-map faults (d_cat > 3 px) over-represent exposed bedrock "
        "(65.7% range-front tercile in the RELIEF session's audit) and under-represent concealed "
        "basin faults; a mass-only subset edit also moves this proxy mechanically with dot count. "
        "PROXY ONLY -- never a gate, never a ranking, never called a score."
    )

    result = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": b.git_sha(),
        "generator_script": "scripts/build_mass_continuity.py",
        "generator_script_sha256": b.sha256_file(Path(__file__)),
        "continuity_module_sha256": b.sha256_file(ROOT / "src" / "continuity.py"),
        "axis": AXIS,
        "session": "2026-10-23 continuity-aware MASS (GEMSDOE90, branch arena/0e9b3fd9-gemsdoe90)",
        "axis_choice": (
            "Agent-selected MASS under the human's delegation. Fresh 2026-10-23 read-only sibling "
            "audit (GEMSDOE84-92 ledgers via gh api): all seven brief axes already built, zero "
            "receipts anywhere; brief-literal CONCENTRATION-up built at 0.8/1/5 km and 10/50 px, "
            "10/15/20%, with every upward arm <= 0 on GEMSDOE86's SGMC MODEL reconciliation and "
            "GEMSDOE84 holding its CONCENTRATION files for collar breaches. No indexed repository "
            "has a continuity-protected MASS removal, which is also the CONTINUITY_AWARE_DOSE rung "
            "this repo's SLOT_PLAN proposed and no session built. SNAP (58 sibling rows, three "
            "sessions reading negative in GEMSDOE86's reconciliation) and SPACING (brief: lowest "
            "priority) were passed over on the same evidence."
        ),
        "parent": {"id": PARENT, "claimed_live_score": 0.2778, "evidence_class": "CLAIM",
                   "zeros_sha256": R0_ZEROS_SHA, "nan_sha256": R0_NAN_SHA, **parent_stats},
        "manifest": {"manifest_path": "registry/data_manifest.json",
                     "verified_count": len(input_receipt), "all_pins_rechecked": True,
                     "files": input_receipt},
        "footprint_px": footprint_px,
        "proxy_seed": SEED,
        "ranking": {
            "used": ("exclusive kernel credit ascending, recomputed after each deletion (src/mass.py), "
                     "gated by strand eligibility (src/continuity.py): link graph <= 6.0 px, protected "
                     "strands = R0 components with >= 10 dots, articulation + 10-dot floor"),
            "link_px": LINK_PX,
            "min_strand_dots": MIN_STRAND,
            "r0_link_components_6px": int(len(comp_sizes)),
            "r0_protected_strands_6px": cont["protected_strands"],
            "r0_protected_dots_6px": cont["protected_dots"],
            "largest_r0_component_dots_6px": int(comp_sizes.max()),
            "continuity_capacity_max_removable": cont["max_removable"],
            "eligibility_blocks_during_greedy_to_40pct": cont["blocks"],
            "truth_used": False, "catalogue_used_in_ranking": False,
            "feature_band_used": False, "score_used": False,
            "kernel_radius_px": mass.R_DEFAULT,
            "matched_count_comparison": {
                pct: {
                    "shadowcont_exclusive_credit_sum": round(float(cont["credit_at_removal"][:counts[pct]].sum()), 4),
                    "shadow_exclusive_credit_sum": round(float(uncon["credit_at_removal"][:counts[pct]].sum()), 4),
                    "shadow_recorded_id": shadow_ref[pct]["id"],
                    "shadowcont_excess_fraction_vs_shadow": round(
                        float(cont["credit_at_removal"][:counts[pct]].sum())
                        / float(uncon["credit_at_removal"][:counts[pct]].sum()) - 1.0, 6),
                } for pct in DOSES
            } | {"random40_exclusive_credit_sum": round(rand_credit_40, 4),
                 "note": ("REPORT ONLY: exclusive credit destroyed at identical removal counts. "
                          "shadowcont-40 destroys less credit than the credit-blind random-40 "
                          "control while keeping every protected strand whole at 6 px.")},
        },
        "region_evenness_gate": {
            "block_px": hd.BLOCK_PX,
            "max_fraction_of_blocks_90pct_emptied": hd.MAX_FRACTION_BLOCKS_EMPTIED,
            "max_emptied_cluster_blocks": hd.MAX_EMPTIED_CLUSTER_BLOCKS,
            "min_p05_share_fraction_of_dose": hd.MIN_P05_SHARE_FRACTION,
            "why": ("Hard Constraint #5 forbids region-isolated files; the same fail-closed gate "
                    "the high-dose MASS session applied is applied here per dose."),
        },
        "experiment_reservation_audit": {
            "checked_utc": "2026-10-23",
            "method": ("read-only gh api fetch of ledger/submissions.csv from buffedlizard55-lab/"
                       "GEMSDOE84..GEMSDOE92 (GEMSDOE93-101 have no ledger file) plus this repo's "
                       "ledger and reservations; no DrivenData or Dropbox contact"),
            "axis_row_counts_all_siblings": {"PRUNE": 68, "SNAP": 58, "MASS": 44, "CONCENTRATION": 33,
                                             "RELIEF": 27, "SPACING": 16, "TRACKB": 9},
            "receipt_scores_found_anywhere": 0,
            "distinct_mass_values_found": SIBLING_MASS_VALUES,
            "selected_values": [value_of(p) for p in DOSES],
            "why_new": ("No indexed MASS value carries a continuity, strand, backbone or articulation "
                        "rule. The doses (20/30/40%) deliberately match the recorded shadow ladder's "
                        "removal counts -- the (AXIS, value) pair differs by ranking, the same "
                        "distinction this repo already records for shadow vs FIFO vs random at "
                        "identical percentages -- so each new file has a matched-count twin whose only "
                        "difference is strand protection."),
            "cross_repo_caveat": ("Best-effort audit of public owner repositories, not proof of every "
                                  "submission the entity has made (IR90-04/IR90-11)."),
        },
        "proxy_reports": {
            "leakage_canary": {
                "status": "NOT APPLICABLE",
                "reason": ("No feature band and no label is read: the ranking is a deterministic "
                           "function of the parent's own dot coordinates, so no single feature "
                           "exists whose AUC could exceed 0.90. On the identical pinned inputs the "
                           "RELIEF session's 19-band canary maxed at symmetric AUC 0.5700 "
                           "(evidence/relief_build_receipt.json)."),
            },
            "catalogue_hide_recover": hide_recover,
            "sgmc_control": sgmc_proxy,
        },
        "variants": variants,
        "hard_constraint_note": (
            "Brief s4 asks >= 3 px from the catalogue unless AXIS=PRUNE. R0's own minimum is "
            "2.236 px (1,611 dots, IR90-01/IR90-07); these deletion-only variants inherit that "
            "collar unchanged (moving it would be a second axis), add no mass at all, and emit "
            "zero catalogue mass. The gate enforced is no_new_mass_within_3px + "
            "subset_of_R0_no_additions_no_moves, as in every prior MASS session."
        ),
        "deadline_note": ("Deadline 2026-12-03, TOP_PUBLIC and quota state are not re-verified here: "
                          "automated access to DrivenData is prohibited. The human confirms all "
                          "three on the competition page before any upload."),
        "elapsed_s": round(time.time() - t0, 1),
        "no_live_submission": True,
        "agent_did_not_submit": True,
        "not_committed_to_git": True,
    }
    return result


def write_ledger(result: dict) -> None:
    """Append this session's rows; never rewrite or drop another session's rows."""
    own = {v["id"] for v in result["variants"]}
    rows = []
    if LEDGER.exists():
        with LEDGER.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("id") not in own]
    existing_hashes = {r.get("sha256") for r in rows} | {r.get("sha256_zeros") for r in rows}
    for v in result["variants"]:
        if v["sha256"] in existing_hashes or v["sha256_zeros"] in existing_hashes:
            raise ValueError(f"sha256 already present in ledger: {v['id']}")
        rows.append({
            "id": v["id"], "site": "GEMSDOE90", "name": v["id"], "score": "",
            "evidence_class": "MODEL (predicted change only)", "encoding": "nan primary; zeros fallback",
            "n_dots": v["n_dots"], "pct_changed": f"{v['pct_changed']:.6f}",
            "sha256": v["sha256"], "sha256_zeros": v["sha256_zeros"], "parent": v["parent"],
            "axis": v["axis"], "value": v["value"], "status": "BUILT", "receipt": "N",
            "receipt_score": "", "predicted_change": v["predicted_change"], "date": "",
            "form_note": v["form_note"],
            "notes": ("strict subset of rebuilt R0; continuity-aware ranking (6px articulation + "
                      "10-dot strand floor); no additions, no moves, no collar change; "
                      "receipt_score/date to be filled by the human; agent never submits"),
        })
    with LEDGER.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    b.verify_manifest_inputs()
    template, foot, cat, r0, _stats = b.exact_parent_rebuild()
    ys, xs = np.nonzero(r0)
    distance_cat = ndi.distance_transform_edt(~cat)
    pts = np.column_stack([ys, xs]).astype(float)
    credit_neighbours = mass.neighbour_lists(pts)
    link_adjacency, comp, comp_sizes = continuity.link_graph(pts, link_px=LINK_PX)
    counts = sorted(int(v["removed_dots"]) for v in receipt["variants"])
    res = continuity.greedy_continuity_removal(
        pts, credit_neighbours, link_adjacency, comp, comp_sizes,
        n_remove=max(counts), snapshots=tuple(counts))
    sample_path = str(b.DATA / b.PIN_PATHS["sample_submission"])
    catalogue_path = str(b.DATA / b.PIN_PATHS["catalogue"])
    for v in receipt["variants"]:
        n_rem = int(v["removed_dots"])
        removed = res["removed_masks"][n_rem]
        expected = r0.copy()
        expected[ys[removed], xs[removed]] = False
        if int(expected.sum()) != v["n_dots"]:
            raise ValueError(f"{v['id']}: recomputed count mismatch")
        survival = continuity.strand_survival(link_adjacency, comp, comp_sizes, ~removed)
        if survival != v["structure_report_only"]["strand_survival_6px"]:
            raise ValueError(f"{v['id']}: strand survival drifted from receipt")
        for mode_name in ("nan", "zeros"):
            path = ROOT / v["files"][mode_name]["path"]
            audit = shadow.validate_candidate(path, expected, foot, cat, template, mode_name, r0, distance_cat)
            if audit["sha256"] != v["files"][mode_name]["sha256"]:
                raise ValueError(f"{v['id']} {mode_name}: re-read SHA mismatch")
            report = format_validate(str(path), sample_path, catalogue_path,
                                     zeros_outside=(mode_name == "zeros"))
            if not report["pass"]:
                raise ValueError(f"{v['id']} {mode_name}: src.validate gate failed on verify: {report['fails']}")
            tmp = ROOT / ".cache" / "verify_mass_continuity" / f"{v['id']}-{mode_name}.tif"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            try:
                b.emit(expected, foot, template, v["id"], mode_name, tmp)
                if b.sha256_file(tmp) != audit["sha256"]:
                    raise ValueError(f"{v['id']} {mode_name}: deterministic re-emit failed")
            finally:
                tmp.unlink(missing_ok=True)
        if not math.isclose(v["pct_changed"], 100.0 * n_rem / R0_DOTS, rel_tol=1e-9):
            raise ValueError(f"{v['id']}: pct_changed is not the exact parent diff")
        if not hd.region_evenness_gate(v["spatial_removal"]):
            raise ValueError(f"{v['id']}: region-evenness gate fails on the recorded statistics")
    receipt["verified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt["verification_git_sha"] = b.git_sha()
    receipt["generator_script_sha256"] = b.sha256_file(Path(__file__))
    receipt["continuity_module_sha256"] = b.sha256_file(ROOT / "src" / "continuity.py")
    receipt["self_check"] = {
        "variant_files_re_read_and_validated": True,
        "variant_bytes_reproduced_exactly": True,
        "r0_rebuilt_byte_identically": True,
        "no_additions_no_moves": True,
        "strand_guarantee_rechecked": True,
        "region_evenness_gate_rechecked": True,
        "sha256_absent_from_ledger_before_write": True,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(receipt['variants'])} continuity-aware pairs from disk; "
          f"R0 rebuilt byte-identically to {R0_ZEROS_SHA[:12]}...")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        return verify()
    check_reservations()
    result = build()
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_ledger(result)
    print(f"Built {len(result['variants'])} continuity-aware MASS variants from exact R0 -> "
          f"{RECEIPT.relative_to(ROOT)}")
    for v in result["variants"]:
        surv = v["structure_report_only"]["strand_survival_6px"]
        print(f"  {v['id']}: {v['n_dots']} dots, {v['pct_changed']:.4f}% changed, "
              f"sha256={v['sha256'][:12]}..., E_sum={v['removal_statistics']['exclusive_credit_sum']:.0f} "
              f"({v['removal_statistics']['credit_ratio_vs_shadow'] - 1:+.1%} vs shadow), "
              f"strands whole {surv['strands_surviving_whole']}/{surv['protected_strands']}, "
              f"pred={v['point_prediction_dti']:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
