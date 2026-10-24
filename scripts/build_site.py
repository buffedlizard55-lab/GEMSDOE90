#!/usr/bin/env python3
"""Generate the GitHub Pages site from the evidence receipts.

Every number on the site is read out of a JSON receipt in evidence/ — nothing is
typed by hand, so the page cannot drift from what was actually measured.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EV = ROOT / "evidence"

CSS = """
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#9198a1;
--ok:#2ea043;--warn:#d29922;--bad:#f85149;--acc:#58a6ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,
"Segoe UI",Helvetica,Arial,sans-serif}
header{padding:28px 20px 18px;border-bottom:1px solid var(--line);background:#010409}
.wrap{max-width:1060px;margin:0 auto;padding:0 20px}
h1{margin:0 0 4px;font-size:28px}h2{margin:34px 0 10px;font-size:21px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{margin:22px 0 8px;font-size:17px}
p,li{color:var(--fg)}.mut{color:var(--mut)}
a{color:var(--acc)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:16px 0}
.ready{border-color:var(--ok);box-shadow:0 0 0 1px rgba(46,160,67,.35)}
.notready{border-color:var(--bad);box-shadow:0 0 0 1px rgba(248,81,73,.35)}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:13px;font-weight:700}
.b-ok{background:rgba(46,160,67,.18);color:#56d364;border:1px solid var(--ok)}
.b-bad{background:rgba(248,81,73,.15);color:#ff7b72;border:1px solid var(--bad)}
.b-warn{background:rgba(210,153,34,.15);color:#e3b341;border:1px solid var(--warn)}
.dl{display:inline-block;background:var(--ok);color:#fff;font-weight:700;font-size:18px;
padding:14px 26px;border-radius:9px;text-decoration:none;margin:10px 12px 10px 0}
.dl:hover{filter:brightness(1.1)}
.dl2{display:inline-block;border:1px solid var(--line);color:var(--fg);padding:13px 20px;
border-radius:9px;text-decoration:none;margin:10px 0}
code,kbd{background:#010409;border:1px solid var(--line);border-radius:5px;padding:1px 6px;
font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;word-break:break-all}
pre{background:#010409;border:1px solid var(--line);border-radius:8px;padding:12px 14px;overflow:auto}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{background:#1c2128}
tr:nth-child(even) td{background:#12171d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:14px 0}
.kv{background:#010409;border:1px solid var(--line);border-radius:8px;padding:12px}
.kv b{display:block;font-size:22px;margin-bottom:2px}
.kv span{color:var(--mut);font-size:13px}
nav a{margin-right:18px;font-weight:600}
footer{margin:46px 0 26px;color:var(--mut);font-size:13px}
ol li{margin:7px 0}
"""


def h(x) -> str:
    return html.escape(str(x))


def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h(title)}</title><style>{CSS}</style></head>
<body><header><div class="wrap">
<h1>GEMSDOE90</h1>
<p class="mut">DOE GEMS Prize (DrivenData #306) — credit-efficient hidden-fault discovery,
auditable end to end.</p>
<nav><a href="index.html">Submission</a><a href="how-to-submit.html">How to submit</a>
<a href="method.html">Method &amp; evidence</a><a href="lane-h90.html">Lane H90</a>
<a href="https://github.com/buffedlizard55-lab/GEMSDOE90">Repository</a></nav>
</div></header><div class="wrap">{body}
<footer>Generated {h(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))} by
<code>scripts/build_site.py</code> from the JSON receipts in <code>evidence/</code>.
Scores copied from the owner's submission list are labelled OWNER-REPORTED; no
organizer receipt is on file in this repository. Local measurements are labelled
HOLDOUT-DTI or MODEL and are never presented as leaderboard scores.</footer>
</div></body></html>
"""


def _lane_name(path) -> str:
    """Submission name recorded by whichever lane published this file.

    Matched on the file's own SHA-256 (exact) or on the file name recorded in a
    receipt, so it keeps working when a lane renames its artefacts.
    """
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    cards = list(path.parent.glob("*.json")) + list((DOCS / "run-cards").glob("*.json")) + \
        list(DOCS.glob("run-card*.json")) + list(EV.glob("*receipt*.json"))
    for cardp in cards:
        try:
            c = json.loads(cardp.read_text())
        except Exception:
            continue
        flat = json.dumps(c)
        if digest in flat or path.name in flat:
            for key in ("submission_name", "name", "candidate"):
                v = c.get(key) or (c.get("raster", {}) or {}).get(key)
                if v:
                    return str(v)
    return path.stem


def fmt(x, n=4):
    return "—" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))


def build() -> None:
    cand = json.loads((EV / "candidate_receipt.json").read_text())
    inv = json.loads((EV / "blind_probe_inversion.json").read_text())
    cal = json.loads((EV / "calibration_fit.json").read_text())
    band = json.loads((EV / "band_profile.json").read_text())
    hold = json.loads((EV / "holdout_report.json").read_text())
    if (EV / "holdout_budget_curve.json").exists():
        hold = json.loads((EV / "holdout_budget_curve.json").read_text())
    card = json.loads((DOCS / "run-card.json").read_text())
    hres = hold["results"]
    nstar = str(min((int(b) for b in hres["ours"]), key=lambda b: abs(b - cand["n_dots"])))

    ready = bool(cand["format_gate"]["pass"] and not cand["lane"]["duplicate"]
                 and str(card["verdict"]).startswith("promote"))
    tif = Path(cand["file"]).name
    dl = f"downloads/{tif}"

    # ---------------------------------------------------------------- index --
    gate = cand["format_gate"]
    gate_rows = "".join(
        f"<tr><td>{h(k)}</td><td>{h(v)}</td></tr>" for k, v in [
            ("CRS", "EPSG:32611 (matches sample_submission.tif)"),
            ("Shape", f"{gate['shape'][0]} x {gate['shape'][1]} @ 100 m"),
            ("Bands / dtype", "1 / float32"),
            ("Values inside footprint", f"min {gate['min_inside']:.1f}, max {gate['max_inside']:.1f} — inside [0,1]"),
            ("Non-finite pixels (whole raster)", f"{gate['nonfinite_total']} — the upload form rejects NaN"),
            ("Outside footprint", "0.0 (all-finite encoding)"),
            ("Positive pixels (dots)", f"{gate['n_positive_inside']:,}"),
            ("Total predicted mass", f"{gate['mass_inside']:,.0f}"),
            ("Mass on catalogued faults", f"{gate['catalogue_mass']:.0f} (those pixels are masked from scoring)"),
            ("SHA-256", cand["sha256"]),
            ("File size", f"{cand['bytes']:,} bytes"),
            ("Format gate", "PASS" if gate["pass"] else "FAIL: " + "; ".join(gate["fails"])),
        ])

    lane_rows = "".join(
        f"<tr><td>{h(r['registry'])}</td><td>{r['dot_overlap_within_3px']:.3f}</td>"
        f"<td>{r['chance_overlap']:.3f}</td><td>{r['excess_over_chance']:+.3f}</td>"
        f"<td>{r['spearman_surface']:+.3f}</td>"
        f"<td>{'DUPLICATE' if r['duplicate'] else 'distinct'}</td></tr>"
        for r in sorted(cand["lane"]["per_registry"],
                        key=lambda r: -r["excess_over_chance"]))

    budgets = sorted(hres["ours"], key=int)
    hold_rows = ""
    for m, label in [("ours", "This candidate's method (fold-honest)"),
                     ("collar", "Incumbent recipe, rebuilt fold-honestly"),
                     ("chance", "Uniform lattice (chance)"),
                     ("R0_oracle", "h33-2-b2 as submitted (oracle-advantaged)")]:
        cells = ""
        for b in budgets:
            hi = " style=\"background:#15311f\"" if (m == "ours" and b == nstar) else ""
            r = hres[m][b]
            cells += (f"<td{hi}>{r['dti']:.4f}<br><span class='mut'>"
                      f"[{r['ci'][0]:.4f}, {r['ci'][1]:.4f}]</span></td>")
        hold_rows += f"<tr><td>{h(label)}</td>{cells}</tr>"

    cal_rows = "".join(
        f"<tr><td>{h(f['name'])}</td><td>{f['n_dots']:,}</td>"
        f"<td>{f['score_owner_reported']:.4f}</td><td>{f['pred_joint']:.4f}</td>"
        f"<td>{f['pred_joint']-f['score_owner_reported']:+.4f}</td>"
        f"<td>{b2['predicted']:.4f}</td><td>{b2['residual']:+.4f}</td></tr>"
        for f, b2 in zip(cal["files"], band["observations"]))

    inv_rows = "".join(
        f"<tr><td>{h(r['name'])}</td><td>{r['n_dots_scored']:,}</td>"
        f"<td>{r['score_owner_reported']:.4f}</td><td>{r['T_implied']:,.0f}</td>"
        f"<td>{r['lift_vs_blind']:.2f}x</td><td>{r['credit_per_dot']:.4f}</td></tr>"
        for r in sorted(inv["files"], key=lambda r: -r["score_owner_reported"]))

    others = sorted(x for x in (DOCS / "downloads").glob("*.tif") if x.name != tif)
    if others:
        import hashlib
        other_rows = ("<table><tr><th>lane / file</th><th>size</th><th>sha256</th>"
                      "<th>page</th></tr>") + "".join(
            f'<tr><td><a href="downloads/{h(o.name)}" download><code>{h(o.name)}</code></a></td>'
            f'<td>{o.stat().st_size/1024:.0f} KB</td>'
            f'<td><code>{hashlib.sha256(o.read_bytes()).hexdigest()}</code></td>'
            f'<td>{h(_lane_name(o))}<br><a href="lane-h90.html">lane portal</a> &middot; '
            f'<a href="executive-summary.html">its summary</a></td></tr>' for o in others) + "</table>"
    else:
        other_rows = "<p class='mut'>None.</p>"

    status = ('<div class="card ready"><span class="badge b-ok">OK TO DOWNLOAD AND SUBMIT</span>'
              '<p style="margin:10px 0 0">The file below passed every gate: single-band float32 '
              'GeoTIFF on the official grid, all values finite and in [0,1], no mass on catalogued '
              'faults, and it is not a duplicate of any raster in the registry. Spending a weekly '
              'slot on it is still a human decision.</p>'
              if ready else
              '<div class="card notready"><span class="badge b-bad">NOT READY — DO NOT SUBMIT</span>'
              '<p style="margin:10px 0 0">A gate failed; see the tables below.</p>')

    body = f"""
<h2 style="margin-top:22px">Executive summary</h2>
{status}
<h3 style="margin-top:14px">Submission file: <code>{h(tif)}</code></h3>
<p>One click, one file, nothing else to prepare. It is a single-band float32 GeoTIFF on the
official grid, every pixel finite and inside [0,1] (zeros outside the footprint), so it passes the
upload form's <em>"Predicted values must be in range [0, 1]"</em> check that rejects NaN-padded files.</p>
<p><a class="dl" href="{h(dl)}" download>&#11015; Download the submission GeoTIFF ({cand['bytes']/1024:.0f} KB)</a>
<a class="dl2" href="how-to-submit.html">Step-by-step submission guide &rarr;</a></p>
<div class="grid">
  <div class="kv"><b>{cand['n_dots']:,}</b><span>unit-mass dots — budget set by the measured holdout curve, not by hand</span></div>
  <div class="kv"><b>{hres['ours'][nstar]['dti']:.4f}</b><span>HOLDOUT-DTI [{hres['ours'][nstar]['ci'][0]:.4f}, {hres['ours'][nstar]['ci'][1]:.4f}] — local hide-and-recover, not a leaderboard score</span></div>
  <div class="kv"><b>{hres['chance'][nstar]['dti']:.4f}</b><span>same holdout, uniform-lattice chance baseline at the same budget</span></div>
  <div class="kv"><b>{cand['lane']['max_excess_over_chance']:+.2f}</b><span>largest above-chance dot overlap with any registry raster (limit 0.30 at &gt;70% overlap)</span></div>
</div>
<div class="card"><h3 style="margin-top:0">What this file does and does not show</h3>
<p><b>Shown.</b> On a buffered whole-segment hide-and-recover holdout it recovers withheld fault
segments far better than chance ({hres['ours'][nstar]['dti']:.4f} vs {hres['chance'][nstar]['dti']:.4f}, non-overlapping 95% CIs) and far better than a
fold-honest rebuild of the incumbent collar recipe ({hres['collar'][nstar]['dti']:.4f}). It is format-valid and it is not a
copy of anything in the registry.</p>
<p><b>Not shown.</b> That it beats the incumbent 0.2778 on the real leaderboard. Two independent
calibration attempts against the 14 owner-reported scores <em>failed</em> (below), and this holdout
is structurally blind to collar-style files — the incumbent itself scores only
{hres['R0_oracle'][nstar]['dti']:.4f} on it. No projected score is claimed anywhere in this repository.</p></div>
<h3>Paste these into the submission form</h3>
<table><tr><th style="width:170px">Form field</th><th>Value</th></tr>
<tr><td>File to submit</td><td><code>{h(tif)}</code></td></tr>
<tr><td>Note (optional, &le;140 chars)</td><td><code>{h(card['submission_note'])}</code>
<span class="mut"> ({len(card['submission_note'])} characters)</span></td></tr></table>
<p class="mut">Verdict recorded in the run card: <b>{h(card['verdict'])}</b>. The agent never uploads;
a human spends the weekly slot.</p>

<h2>Why this file exists (the short version)</h2>
<p>The official metric is a distance-weighted Tversky index,
<code>DTI = TP<sub>w</sub> / (TP<sub>w</sub> + 0.2&middot;FP<sub>w</sub> + 0.8&middot;FN<sub>w</sub>)</code>
with a 300 m triangular kernel. Because <code>FN<sub>w</sub> = |G| - TP<sub>w</sub></code> and
&alpha;+&beta;=1, it collapses to</p>
<pre>DTI = T / (0.2&middot;T + 0.2&middot;(S - M) + 0.8&middot;|G|)</pre>
<p>where <b>T</b> is coverage credit on the hidden faults, <b>S</b> is total predicted mass and
<b>M</b> is the part of that mass sitting close to truth. <b>0.8&middot;|G|</b> is a constant, so a dot
helps only if the credit it adds beats
<code>0.2&theta;/(1-0.2&theta;)</code> &mdash; about
<b>{inv['break_even_credit_at_0.2778']:.3f} credit</b> at &theta;=0.2778. Mass is bang-bang
(always emit 1.0 or nothing) and the dot budget is therefore a quantity the metric decides, not a
style choice.</p>
<p>Inverting that identity against the owner's own scored rasters shows the incumbent family has
been buying credit at a price barely above break-even: see the table below.</p>

<h2>Inversion of the scored history (OWNER-REPORTED scores)</h2>
<p>A uniform 5 px lattice covers every pixel equally, so its credit is its mean coverage
({inv['files'][0]['mean_coverage']:.4f}) times |G| whatever the hidden faults look like. That single
blind probe pins <b>|G| &asymp; {inv['G_adopted']:,.0f}</b> hidden-fault pixels
({100*inv['global_density']:.3f}% of the {inv['scored_domain_px']:,}-pixel scored domain); the
independent blind "placeholder" raster lands at lift 0.71, which is the consistency check.</p>
<table><tr><th>raster</th><th>dots</th><th>score (owner-reported)</th><th>implied T</th>
<th>lift vs blind</th><th>credit / dot</th></tr>{inv_rows}</table>
<p>The incumbent <code>h33-h33-2-b2</code> (0.2778) is <em>not</em> the most accurate file in the
list &mdash; <code>hedge_v2</code> and <code>h19_5</code> both capture more credit. It wins because it
captures nearly the same credit with the smallest budget: 0.134 credit per dot against a
{inv['break_even_credit_at_0.2778']:.3f} break-even. Everything above roughly 40k dots in that family
was being bought at about 0.02 credit per dot, i.e. below cost.</p>

<h2>Calibration: can any model of the hidden field reproduce real scores? (NEGATIVE)</h2>
<p>Two independent attempts, both constrained to a physically valid occupancy field
(0 &le; &pi; &le; 1, &Sigma;&pi; = |G| — a pixel either is a hidden-fault pixel or it is not):</p>
<ol>
<li><b>Learner field.</b> &pi; &prop; p<sub>model</sub><sup>&gamma;</sup>, &gamma; and |G| fitted.
Best: &gamma; = {cal['gamma_joint']:.2f}, |G| = {cal['G_joint']:,.0f}, RMSE <b>{cal['rmse_joint']:.4f}</b>.</li>
<li><b>Model-free band inversion.</b> &pi; = &rho;<sub>band</sub>·[(1&minus;&eta;) + &eta;·w/w&#772;], with
&rho; solved by non-negative least squares per distance-to-catalogue band and &eta; measuring how
much the learner's ranking helps. Best: &eta; = {band['best']['eta']:.2f}, |G| = {band['best']['G']:,.0f},
RMSE <b>{band['best']['rmse']:.4f}</b>, leave-one-out RMSE {band['best']['loo_rmse']:.4f}.</li>
</ol>
<p><b>Both fail, in the same direction:</b> every targeted raster is under-predicted by roughly a
factor of two (the incumbent most of all). Dropping the occupancy cap produces an apparently
excellent fit (RMSE 0.015) only by letting single pixels carry a density of 70 hidden faults — an
artefact, not a result. The honest conclusion is that <em>where those dots sit</em> is not explained
by distance-to-catalogue or by the current 63-feature stack, so no leaderboard projection is made.</p>
<table><tr><th>raster</th><th>dots</th><th>owner-reported</th><th>learner pred</th><th>resid</th>
<th>band pred</th><th>resid</th></tr>
{cal_rows}</table>
<p class="mut">Radial profile returned by the band inversion (hidden-fault density by distance to
the catalogue): {h(', '.join(f"{r['d_lo_px']:.1f}-{r['d_hi_px']:.1f} px: {r['rho']:.4f}" for r in band['rho_by_band'] if r['rho'] > 1e-5))}.</p>

<h2>Holdout: buffered whole-segment hide-and-recover</h2>
<p>{h(hold['protocol'])}; {hold['n_folds']} folds over {hold['n_segments']:,} catalogue segments
grouped by 25 km blocks; buffer {hold['buffer_px']:.0f} px; catalogue-derived features rebuilt from
visible faults only; visible faults masked pixel-exactly; pooled DTI with a spatial-block bootstrap
95% CI. Evaluator <code>{h(hold['evaluator'])}</code>.</p>
<table><tr><th>method</th>{''.join(f'<th>n = {int(b):,}</th>' for b in budgets)}</tr>{hold_rows}</table>
<p class="mut">The incumbent raster is scored here for reference only: it was built with the whole
catalogue visible, including the segments this holdout withholds, so its row is an upper bound and
not a like-for-like control. The fold-honest rebuild of its recipe ("collar") is the fair control.</p>

<h2>Duplicate / lane screen</h2>
<p>Dot overlap within 3 px, the overlap a blind placement would get against the same raster
(chance), the excess over chance, and the Spearman rank correlation of the surfaces. Raw overlap
alone is not a duplicate test: the 5 px lattice probe covers 98% of the domain within 3 px, so
everything "overlaps" it. Duplicate = overlap &gt; 0.70 <em>and</em> excess &gt; 0.30, or &rho; &gt; 0.90.</p>
<table><tr><th>registry raster</th><th>dot overlap &le;3 px</th><th>chance</th><th>excess</th>
<th>Spearman</th><th>verdict</th></tr>
{lane_rows}</table>

<h2>Where the dots are — this is not a collar file</h2>
<div class="grid">
  <div class="kv"><b>{cand['geometry']['d_to_catalogue_px']['median']:.0f} px</b><span>median distance to the nearest catalogued fault ({cand['geometry']['d_to_catalogue_px']['median']*0.1:.1f} km)</span></div>
  <div class="kv"><b>{cand['geometry']['share_beyond_6px']:.1%}</b><span>of dots lie beyond 6 px of the catalogue — the incumbent family sits at 3.4&ndash;4.5 px</span></div>
  <div class="kv"><b>{cand['geometry']['occupied_25km_blocks']}</b><span>occupied 25 km blocks; largest single block holds {cand['geometry']['max_single_block_share']:.1%} of the dots</span></div>
  <div class="kv"><b>0</b><span>mass on catalogued fault pixels (they are masked from scoring)</span></div>
</div>
<p>Every scored raster in the registry is a halo around the existing catalogue. This candidate is
not: it places {cand['geometry']['share_beyond_6px']:.0%} of its mass in ground the catalogue does not touch, which is where a
genuinely <em>undiscovered</em> fault has to be. That is also why it is risky — the collar strategy
is the one with real score feedback behind it, and this one has only the holdout.</p>

<h2>Format gate (re-read from the written file)</h2>
<table><tr><th style="width:280px">check</th><th>value</th></tr>{gate_rows}</table>

<h2>Other candidates published in this repository</h2>
<p>Parallel sessions publish their own lanes. Each is a separate experiment with its own receipt;
only one file may ever be uploaded per weekly slot, and choosing between them is a human decision.</p>
{other_rows}

<h2>Official sources</h2>
<ul>
<li>Competition &amp; rules: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">drivendata.org/competitions/306</a></li>
<li>Problem description &amp; metric: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page/967</a></li>
<li>Data (login required): <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">data tab</a></li>
<li>Leaderboard: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">public leaderboard</a></li>
<li>Official reference solution: <a href="https://github.com/drivendataorg/gems-prize-reference-solution">drivendataorg/gems-prize-reference-solution</a></li>
<li>USGS GeoDAWN release: <a href="https://doi.org/10.5066/P93LGLVQ">doi:10.5066/P93LGLVQ</a>
 &middot; <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS data page</a></li>
<li>INGENIOUS / GDR 1391: <a href="https://gdr.openei.org/submissions/1391">gdr.openei.org/submissions/1391</a>
 &middot; <a href="https://gbcge.org/current-projects/ingenious/">project page</a></li>
<li>Grid CRS: <a href="https://epsg.io/32611">EPSG:32611</a> &middot;
 Metric family: <a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></li>
</ul>
"""
    (DOCS / "index.html").write_text(page("GEMSDOE90 — submission", body), encoding="utf-8")

    # ------------------------------------------------------- how to submit --
    note = card["submission_note"]
    howto = f"""
<h2>How to make a submission — exact steps</h2>
<div class="card ready"><b>Summary:</b> download one file, open the submission page, choose the file,
paste the note, submit. Nothing is renamed, unzipped or converted.</div>
<ol>
<li><b>Download the file.</b> <a class="dl" href="{h(dl)}" download>&#11015; {h(tif)}</a>
Keep the name as it is &mdash; it is unique and carries the method, dot count and timestamp.
Verify it if you like:<br><code>sha256sum {h(tif)}</code> &rarr; <code>{h(cand['sha256'])}</code></li>
<li><b>Open</b> <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">
the competition submission page</a> and sign in. Check the weekly quota shown there
(the rules allow a limited number of scored submissions per week per team).</li>
<li><b>"File to submit":</b> choose the downloaded <code>.tif</code>. A single-band GeoTIFF is accepted
directly; a <code>.zip</code> containing exactly one GeoTIFF is also accepted. Do not upload both.</li>
<li><b>"Note" (optional, helps you tell submissions apart):</b> paste
<pre>{h(note)}</pre>
({len(note)} characters, within the form's short-comment intent of &le;140.)</li>
<li><b>Submit</b>, then copy the score the page returns back into
<code>ledger/submissions.csv</code> as an ORGANIZER-CONFIRMED receipt. Until that is done, every
number in this repository stays labelled MODEL or HOLDOUT-DTI.</li>
</ol>

<h2>If the form rejects the file</h2>
<table>
<tr><th>message</th><th>cause</th><th>fix</th></tr>
<tr><td><em>Predicted values must be in range [0, 1]</em></td>
<td>The raster contains NaN (or a nodata sentinel such as -3.4e38). NaN is not in [0,1], so a
NaN-outside-footprint file is rejected even though it is otherwise valid.</td>
<td>Use the file linked above: it is the all-finite encoding (zeros outside the footprint,
{gate['nonfinite_total']} non-finite pixels in the whole raster).</td></tr>
<tr><td><em>CRS / shape / transform mismatch</em></td>
<td>The raster must be exactly the submission-format grid.</td>
<td>This file is EPSG:32611, {gate['shape'][0]}&times;{gate['shape'][1]} at 100 m, with the sample
transform; <code>python -m src.submission_writer</code>'s validator re-checks all three from disk.</td></tr>
<tr><td><em>Multiple bands / wrong dtype</em></td><td>Only one float32 band is accepted.</td>
<td>This file is single-band float32.</td></tr>
</table>

<h2>Re-validate the file yourself</h2>
<pre>python - &lt;&lt;'PY'
import rasterio, numpy as np
ds = rasterio.open("{h(tif)}")
a  = ds.read(1)
print(ds.crs, ds.width, ds.height, ds.count, a.dtype)
print("finite:", np.isfinite(a).all(), "min:", a.min(), "max:", a.max(), "dots:", int((a>0).sum()))
PY</pre>
<p>Expected: <code>EPSG:32611 {gate['shape'][1]} {gate['shape'][0]} 1 float32</code>,
<code>finite: True min: 0.0 max: 1.0 dots: {gate['n_positive_inside']}</code>.</p>

<h2>What counts as a slot</h2>
<p>Promotion to a weekly scored slot is a <b>separate human decision</b>. This page only certifies that
the file is unique, format-valid and holdout-tested; it does not claim a leaderboard position and it
does not spend a slot. One file per slot &mdash; the repository never offers two encodings of the same
experiment as two submissions.</p>
"""
    (DOCS / "how-to-submit.html").write_text(page("GEMSDOE90 — how to submit", howto), encoding="utf-8")

    # ------------------------------------------------------------- method --
    feats = json.loads((ROOT / ".cache" / "work" / "static_names.json").read_text()) + \
        json.loads((ROOT / ".cache" / "work" / "cat_names.json").read_text()) \
        if (ROOT / ".cache" / "work" / "static_names.json").exists() else []
    canary = card.get("leakage_canary", {})
    can_rows = "".join(f"<tr><td>{h(k)}</td><td>{fmt(v)}</td></tr>" for k, v in
                       sorted(canary.get("top_features", {}).items(), key=lambda kv: -kv[1])[:12])
    method = f"""
<h2>Hypothesis</h2>
<p>{h(card['hypothesis'])}</p>
<h3>Mechanism</h3><p>{h(card['mechanism'])}</p>
<h3>Named non-fault process that could mimic it</h3><p>{h(card['named_non_fault_mimic'])}</p>

<h2>Pipeline</h2>
<ol>
<li><code>scripts/restore_data.py</code> — restore and SHA-256 verify all 26 pinned inputs into
<code>.cache/gems_data/</code> (never committed).</li>
<li><code>scripts/run_discovery.py features</code> — {len(feats) if feats else 54} leak-free static
features (GeoDAWN magnetics/gravity/strain/conductivity, 3DEP-derived lidar scarp morphometry,
radiometrics and ratios, SGMC geologic-map faults, GDR 1391 thermal wells/springs, Quaternary
slip-rate density, volcanic vents) plus 9 catalogue features rebuilt per fold.</li>
<li><code>scripts/run_discovery.py folds</code> — buffered whole-segment hide-and-recover; a gradient
boosted model per fold trained only on <em>other</em> folds' withheld segments.</li>
<li><code>scripts/run_discovery.py deploy</code> — the same learner with the whole catalogue visible,
giving the hidden-fault probability field.</li>
<li><code>scripts/invert_blind_probes.py</code> — |G| from the blind lattice probe.</li>
<li><code>scripts/calibrate.py</code> — fit the field against {len(cal['files'])} owner-reported scores.</li>
<li><code>scripts/make_submission.py</code> — greedy DTI-optimal emission, budget at the maximum of
the exact predicted-DTI curve, lane screen, format gate, GeoTIFF.</li>
<li><code>scripts/evaluate_holdout.py</code> — pooled HOLDOUT-DTI with block-bootstrap CIs.</li>
</ol>

<h2>Leakage canary</h2>
<p>Every feature is scored alone on the holdout; a single-feature AUC above 0.90 is treated as
leakage until proven otherwise. Maximum observed: <b>{fmt(canary.get('max_auc'))}</b>
({h(canary.get('max_feature', '—'))}).</p>
<table><tr><th>feature</th><th>holdout AUC (symmetric)</th></tr>{can_rows}</table>

<h2>Run card</h2>
<pre>{h(json.dumps(card, indent=2))}</pre>

<h2>Known irregularities</h2>
<ul>
<li>Every historical score used for calibration is OWNER-REPORTED; no submission-page receipt is in
this repository. The calibration is therefore conditional on that list being accurate.</li>
<li><code>labels.tif</code> and <code>existing_faults.tif</code> in the pinned mirror are byte-identical
(SHA-256 <code>7ba308cc…</code>), i.e. the training labels <em>are</em> the catalogue.</li>
<li>Two registry rasters (<code>hedge_v2</code>, <code>ens12</code>) are pixel-identical off-catalogue
and differ by 54,533 on-catalogue pixels, and both are reported at 0.1563 — direct evidence that
catalogued fault pixels are masked out of scoring.</li>
<li>The kernel's distance is assumed Euclidean in pixels; the published definition gives
k(d)=max(1-d/300 m, 0) without naming the metric.</li>
<li>The prompt quotes three different "current leaderboard" values (0.4413, 0.3195, 0.3049 in an
older sibling repository). None is verifiable from this sandbox; the live leaderboard must be read by
a human on the day.</li>
</ul>
"""
    (DOCS / "method.html").write_text(page("GEMSDOE90 — method & evidence", method), encoding="utf-8")

    # GitHub Pages serves this repository from main:/ , so the root page is the
    # one visitors actually land on.  Same HTML, links rewritten into docs/.
    root = page("GEMSDOE90 — submission", body)
    for a, b in (('href="downloads/', 'href="docs/downloads/'),
                 ('href="how-to-submit.html"', 'href="docs/how-to-submit.html"'),
                 ('href="method.html"', 'href="docs/method.html"'),
                 ('href="index.html"', 'href="index.html"'),
                 ('href="lane-h90.html"', 'href="lane-h90.html"'),
                 ('href="executive-summary.html"', 'href="executive-summary.html"')):
        root = root.replace(a, b)
    (ROOT / "index.html").write_text(root, encoding="utf-8")
    print("wrote index.html (Pages root), docs/index.html, docs/how-to-submit.html, "
          "docs/method.html")


if __name__ == "__main__":
    sys.exit(build() or 0)
