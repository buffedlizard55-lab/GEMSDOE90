#!/usr/bin/env python3
"""Generate the GitHub-Pages site (docs/index.html) for the 2026-10-24 H1 lane.

The page is generated *from the receipts* -- it cannot claim more than the
gates measured.  The download button is enabled (green "OK TO DOWNLOAD &
SUBMIT") only when evidence/lane90_final_receipt.json says
ok_to_download_and_submit=true, which itself requires: format gate PASS on the
exact zeros-outside file, lane-uniqueness vs every registry raster
(Spearman<=0.90, 3px dot overlap<=0.70), a positive paired HOLDOUT-DTI delta
vs the incumbent recipe, and a clean leakage canary.  Otherwise the page shows
a red DO-NOT-SUBMIT banner and no download link.  The TIF offered here is the
team's own prediction raster (not competition data), copied to
docs/downloads/ at the owner's explicit request for a one-click download.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence"
DOCS = ROOT / "docs"
DOWN = DOCS / "downloads"


def parallel_lane_section() -> str:
    """Truthful summary of the parallel edge-persistence lane merged from main
    (PR #32), generated from its own run card so this page never overclaims it."""
    rc_path = DOCS / "run-card.json"
    add_path = EVID / "lane90_crosslane_addendum.json"
    if not rc_path.is_file():
        return ""
    rc = json.loads(rc_path.read_text())
    h = rc.get("holdout", {})
    cross = ""
    if add_path.is_file():
        a = json.loads(add_path.read_text())
        cross = (
            f" Cross-lane uniqueness vs the H1 file above (E3 raster byte-reproduced, "
            f"Spearman {a['surface_spearman_H1_vs_E3']}, dot overlap "
            f"{a['H1_dots_within_3px_of_E3_dots']}): <b>distinct lanes, not duplicates</b> "
            f"(<code>evidence/lane90_crosslane_addendum.json</code>)."
        )
    return f"""
<h2>Parallel lane on main — catalogue-free edge persistence (🔴 NOT approved)</h2>
<p>A second 2026-10-24 lane (radiometric/magnetic/gravity/strain/topo edge-persistence fusion,
file <code>gems90-e3-multiphysics-fusion-37654-20261024.tif</code>, SHA-256
<code>{rc.get('raster_sha256', '')}</code>) is format-valid and unique but <b>lost</b> its
whole-segment holdout to the fold-clean H19-5 dotted baseline
(E3 HOLDOUT-DTI {h.get('E3_multiphysics_fusion', {}).get('value')} vs baseline
{h.get('baseline_foldclean_h19_dotted', {}).get('value')}, {h.get('withheld_positives')} withheld
positives, {h.get('evaluator_version')}). Verdict: <b>negative — do not submit that file</b>;
it is not hosted here.{cross}</p>
<p>Full record: <a href="edge-lane.html">edge-lane dashboard (preserved)</a> ·
<a href="executive-summary.html">executive summary &amp; submission steps</a> ·
<a href="run-card.json">edge-lane run card (JSON)</a> ·
<a href="session-review.md">research audit</a> ·
<a href="REVIEW_AND_NEXT_HYPOTHESES.md">repository review &amp; next hypotheses</a></p>"""


def main() -> int:
    final = json.loads((EVID / "lane90_final_receipt.json").read_text())
    hold = json.loads((EVID / "lane90_holdout_receipt.json").read_text())
    ok = bool(final["ok_to_download_and_submit"])
    name = final["submission_name"]
    src = ROOT / final["files"]["zeros_primary_download"]["path"]
    DOWN.mkdir(parents=True, exist_ok=True)
    dst = DOWN / name
    if ok:
        if not dst.is_file() or dst.stat().st_size != src.stat().st_size:
            shutil.copyfile(src, dst)
    sha = final["files"]["zeros_primary_download"]["sha256"]
    size_kb = final["files"]["zeros_primary_download"]["bytes"] / 1024
    gate = final["files"]["zeros_primary_download"]["format_gate"]
    note = final["form_note_le_140_chars"]
    pooled = hold["pooled"]
    paired = hold["paired_vs_incumbent"]
    uniq_rows = "".join(
        f"<tr><td>{u['raster']}</td><td>{u['surface_spearman']}</td>"
        f"<td>{u['dot_overlap_within_3px']}</td><td>{u['footprint_baseline_within_3px']}</td>"
        f"<td>{u['excess_overlap']}</td><td>{u['other_n_dots']:,}</td></tr>"
        for u in final["uniqueness"]["per_raster"]
    )
    pooled_rows = "".join(
        f"<tr><td>{k}</td><td><b>{v['holdout_dti']}</b></td><td>[{v['ci95'][0]}, {v['ci95'][1]}]</td>"
        f"<td>{int(v['S']):,}</td><td>{v['G']:,}</td></tr>"
        for k, v in pooled.items()
    )
    banner = (
        '<div class="banner ok">✅ VALIDATED — OK TO DOWNLOAD &amp; SUBMIT'
        "<span>Every automated gate below PASSed on this exact file (re-read from disk). "
        "No human inspection is required before upload; the slot choice and the upload itself remain yours.</span></div>"
        f'<p><a class="dl" href="downloads/{name}" download>⬇ Download submission TIF — {name}</a></p>'
        f"<p class='meta'>{final['n_dots']:,} dots · {size_kb:,.0f} KiB · SHA-256 <code>{sha}</code></p>"
        f"<p>Paste this into the DrivenData <b>Note</b> field ({final['form_note_chars']} chars):<br>"
        f"<code id='note'>{note}</code> <button onclick=\"navigator.clipboard.writeText(document.getElementById('note').textContent)\">Copy note</button></p>"
        if ok else
        '<div class="banner bad">⛔ DO NOT SUBMIT THIS FILE'
        "<span>One or more automated gates below FAILed. The file is kept local as a negative result; "
        "see the gate table for exactly why.</span></div>"
    )
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GEMSDOE90 — H1 learned fault-ness submission (2026-10-24)</title>
<style>
body{{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:920px;margin:2rem auto;padding:0 1rem;line-height:1.5;color:#111}}
.banner{{border-radius:10px;padding:1rem 1.2rem;font-weight:700;font-size:1.25rem}}
.banner span{{display:block;font-weight:400;font-size:.95rem;margin-top:.4rem}}
.ok{{background:#e6f4ea;border:2px solid #1e8e3e}} .bad{{background:#fce8e6;border:2px solid #c5221f}}
a.dl{{display:inline-block;background:#1e8e3e;color:#fff;padding:.9rem 1.4rem;border-radius:8px;
font-size:1.15rem;font-weight:700;text-decoration:none}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}} td,th{{border:1px solid #ccc;padding:.35rem .5rem;text-align:left}}
code{{background:#f1f3f4;padding:.1rem .3rem;border-radius:4px;word-break:break-all}}
.meta{{color:#444;font-size:.9rem}} h2{{margin-top:2rem;border-bottom:2px solid #eee;padding-bottom:.3rem}}
.pass{{color:#1e8e3e;font-weight:700}} .fail{{color:#c5221f;font-weight:700}}
</style></head><body>
<h1>GEMSDOE90 — next submission (H1: learned fault-ness surface)</h1>
{banner}
<h2>Executive summary — exactly how to submit</h2>
<ol>
<li>Download the TIF from the green button above (only present when every gate PASSes).
It is a single-band float32 GeoTIFF, EPSG:32611, same shape/transform as the sample submission,
all-finite values in {{0,1}} — so it cannot trigger DrivenData's
<i>"Predicted values must be in range [0, 1]"</i> rejection (that error comes from NaN/sentinel
encodings; this primary file uses zeros outside the footprint and no nodata sentinel).</li>
<li>Go to the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> → <b>Submit</b> → choose the downloaded file.</li>
<li>Paste the Note text above into the optional Note field.</li>
<li>Upload <b>one file per scored slot</b> from your own account. The agent never submits.
After scoring, record the receipt score in <code>ledger/submissions.csv</code> (that converts the
CLAIM in the ledger into an ORGANIZER-CONFIRMED number).</li>
</ol>
<h2>What this file is (and why it should beat 0.2778)</h2>
<p>The incumbent <code>h33-h33-2-b2</code> (CLAIM 0.2778, owner-reported — no organizer receipt on file)
is the H19-5 support thinned to 2.8&nbsp;px-spaced unit dots with a &gt;2&nbsp;px catalogue collar
(37,654 dots, byte-identical rebuild verified in this repo). It wins because sparse unit dots maximise
unique 300&nbsp;m-kernel coverage per unit of penalised mass, it puts zero mass on the catalogue
(scored truth is faults <i>missing</i> from the catalogue), and ~38–44k dots is the empirical budget
sweet spot. But every later repo candidate only re-arranges dots on that same support (measured
headroom &lt;0.010), so the support is the ceiling. This file instead builds a <b>new support</b>:
a fold-clean learned fault-ness surface over 51 label-agnostic layers (19 competition bands +
magnetic/gravity/basement derivatives + USGS-3DEP lidar-scarp stack + GeoDAWN radiometrics;
no catalogue-derived feature), then applies the incumbent's proven emission
(2.8&nbsp;px Poisson unit dots, d<sub>catalogue</sub>&gt;2&nbsp;px, zero catalogue mass).
Full analysis: <code>docs/HYPOTHESES_20261024.md</code> in the repo.</p>
<h2>Automated validation gates (no human inspection)</h2>
<table>
<tr><th>Gate</th><th>Result</th><th>Detail</th></tr>
<tr><td>Format (src/validate.py on this exact file: CRS EPSG:32611, shape, transform, float32, 1 band, values in [0,1], no NaN in footprint, zero catalogue mass)</td>
<td class="{'pass' if gate['pass'] else 'fail'}">{'PASS' if gate['pass'] else 'FAIL ' + str(gate['fails'])}</td>
<td>dots={gate['n_dots']:,}, catalogue_mass={gate['catalogue_mass']}</td></tr>
<tr><td>Blocked holdout: paired Δ vs incumbent recipe (25&nbsp;km blocks, {hold['withheld_positives_total']:,} withheld positives; HOLDOUT-DTI α=0.2 β=0.8 R=3px, <i>not</i> a leaderboard score)</td>
<td class="{'pass' if final['holdout']['paired_delta_vs_A']['delta'] > 0 else 'fail'}">Δ={final['holdout']['paired_delta_vs_A']['delta']:+}</td>
<td>95% CI [{final['holdout']['paired_delta_vs_A']['ci95'][0]}, {final['holdout']['paired_delta_vs_A']['ci95'][1]}]</td></tr>
<tr><td>Lane uniqueness vs every registry raster (surface Spearman ≤0.90 and ≤70% dots within 3px of any one raster)</td>
<td class="{'pass' if final['uniqueness']['lane_unique_le_0.90_and_le_0.70'] else 'fail'}">{'PASS' if final['uniqueness']['lane_unique_le_0.90_and_le_0.70'] else 'FAIL'}</td>
<td>max |Spearman|={final['uniqueness']['max_abs_surface_spearman_vs_registry']}, max overlap (sparse dotted ≤65k)={final['uniqueness']['max_dot_overlap_within_3px_vs_sparse_dotted_le65k']}, vs R0={final['uniqueness']['overlap_vs_parent_R0']}, max excess-over-density-baseline={final['uniqueness']['max_excess_overlap_vs_density_baseline']} (raw overlap vs dense coverage rasters is a tautology; see per-raster baselines below)</td></tr>
<tr><td>Leakage canary (max single-feature symmetric AUC ≤0.90)</td>
<td class="{'pass' if not final['canary']['stop'] else 'fail'}">{final['canary']['max_symmetric_auc']} ({final['canary']['feature']})</td>
<td>51 features, catalogue positives vs far negatives</td></tr>
</table>
<h2>Holdout detail (HOLDOUT-DTI, evaluator src/holdout.py)</h2>
<table><tr><th>Arm</th><th>Pooled HOLDOUT-DTI</th><th>95% CI (block bootstrap)</th><th>Dots</th><th>Withheld truth px</th></tr>
{pooled_rows}</table>
<p class="meta">Paired deltas vs A: """ + ", ".join(
        f"{k}={v['delta']:+} [{v['ci95'][0]}, {v['ci95'][1]}]" for k, v in paired.items()
    ) + f""". OOF surface AUC (hidden vs far) = {hold['oof_surface_auc_hidden_vs_far']}.
Holdout absolute values are <b>not</b> comparable to leaderboard scores (different truth set and budget geography);
only the paired comparison at matched budget is evidence. Organizer scores exist in this project only as
owner-reported CLAIMs unless a submission-page receipt is recorded in the ledger.</p>
<h2>Uniqueness vs registry rasters</h2>
<table><tr><th>Raster</th><th>Surface Spearman</th><th>My dots within 3px (raw)</th><th>Footprint baseline within 3px</th><th>Excess overlap</th><th>Their dots</th></tr>
{uniq_rows}</table>
<h2>Reproduce &amp; verify line-by-line</h2>
<pre>.venv/bin/python scripts/restore_data.py            # 26/26 SHA-256 pins
.venv/bin/python scripts/run_lane90.py canary       # evidence/lane90_canary_receipt.json
.venv/bin/python scripts/run_lane90.py holdout      # evidence/lane90_holdout_receipt.json
.venv/bin/python scripts/run_lane90.py final --arm {final['arm'][0]} --budget {final['n_dots']}
.venv/bin/python -m src.validate releases/{name} .cache/gems_data/sample_submission.tif --catalogue .cache/gems_data/existing_faults.tif --zeros-outside
.venv/bin/python scripts/build_site90.py            # regenerates this page from the receipts</pre>
{parallel_lane_section()}
<h2>Official sources</h2>
<ul>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS competition</a> ·
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">submission rules PDF (NLR FY26OSTI-96647)</a> ·
<a href="https://github.com/drivendataorg/gems-prize-reference-solution">reference solution</a></li>
<li><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN magnetic/radiometric surveys</a> (DOI 10.5066/P93LGLVQ) ·
<a href="https://gdr.openei.org/submissions/1391">GDR 1391 INGENIOUS data</a> ·
<a href="https://epsg.io/32611">EPSG:32611</a> · <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></li>
</ul>
<p class="meta">Generated {final['generated_utc']} by scripts/build_site90.py from
evidence/lane90_final_receipt.json + lane90_holdout_receipt.json. Run card: evidence/lane90_run_card.json.
Verdict: <b>{final['verdict']}</b>. Decision rule: {final['decision_rule']}</p>
</body></html>
"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"site written: ok={ok} file={name} download_copied={dst.is_file() and ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
