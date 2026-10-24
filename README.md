# GEMSDOE90 — DOE GEMS Prize (DrivenData #306)

**Start every session by reading this file top to bottom, then
[`docs/KNOWLEDGE_BASE_GEOTHERMAL.md`](docs/KNOWLEDGE_BASE_GEOTHERMAL.md) and the newest run card
in [`docs/run-card.json`](docs/run-card.json).**

Site (download + how to submit): **[docs/index.html](docs/index.html)** ·
[how to submit](docs/how-to-submit.html) · [method & evidence](docs/method.html)

---

## 1. Project brief — standing requirements

> This is the operational statement of the user's brief. It is a faithful restatement of every
> requirement, not a byte-for-byte transcript; where a requirement was given in several messages it
> is consolidated here. Treat every line as binding.

**Goal.** Compete in the DOE GEMS competition
(<https://www.drivendata.org/competitions/306/competition-doe-gems/>) and produce a unique,
downloadable, submission-ready single-band GeoTIFF that can win.

**Hard requirements**

1. **Never relabel an old submission.** Every candidate must be a genuinely new raster. Copies of
   prior GEMSDOE submissions may be restored for study only, never shipped.
2. **Beat the incumbents.** The reference point is GEMSDOE32 `h33-h33-2-b2-…-zeros` = **0.2778**
   (owner-claimed, no receipt). Quoted current leaderboard highs: **0.4413** and **0.3195**.
   Explain *why* 0.2778 scored highest and whether it can be beaten.
3. **Format.** Single-band GeoTIFF, EPSG:32611, the sample submission's shape and geotransform,
   all values in **[0, 1]**. A previous upload was rejected with *"Predicted values must be in
   range [0, 1]"* — NaN fill is the suspected cause, so ship **zeros outside** the footprint.
4. **Name + note.** Supply a unique submission name and a note of **≤ 140 characters**.
5. **Hypotheses first.** Before implementing, generate 3–5 untried geological hypotheses; each must
   name the layer(s), the physical signature/transform, why it finds faults the USGS/INGENIOUS
   catalogue lacks, and how it differs from existing repository work. Rank by expected DTI gain and
   cost, and validate the top one on the spatially blocked holdout before spending a slot. If new
   external data is needed, name the specific free official source and verify it is obtainable.
6. **Parallel-run protocol.** Stay in one method lane. A candidate is a duplicate if Spearman
   ρ > 0.90 against any registry raster, or if > 70 % of its dots fall within 3 px of a registry
   raster's dots — check the surface *before* placement and the final dots *after*. Reuse the
   shared template tools; if a shared tool is wrong, fix it once in the template and report it —
   never keep a private fork.
7. **Label every number.** Each figure is either **HOLDOUT-DTI** (with evaluator version, number of
   withheld positives and a 95 % CI) or **ORGANIZER-CONFIRMED** (from a submission-page receipt).
   Never write a projection as a score.
8. **Leakage canary.** Score every feature alone; AUC > 0.90 is leakage until proven otherwise.
9. **One JSON run card** per session: hypothesis, mechanism, named non-fault mimic, holdout DTI +
   CI, correlation/overlap against the registry, raster sha256, validator output, submission name +
   note, and a promote/negative verdict.
10. **Budget:** stop after 3 experiments or 2 hours.
11. **Do not pick the weekly slot.** Promotion is a separate human selector step.
12. **Site.** A GitHub Pages site with a clean UI; the downloadable TIF and an executive-summary
    subpage explaining exactly how to submit must be at the very top of the site, and it must be
    obvious whether the file is OK to download and submit.
13. **This prompt lives in the README** and is re-read at the start of every session.
14. **Research.** Do deep, cited research into geothermal-vent discovery and store the gathered
    knowledge in-repo as a reusable base for future projects.
15. **Finish with a pull request, merged to main**, stating explicit remaining work and
    limitations for the next session.

**Standing working constraints**

- **No hallucinations.** Verify line by line from official, verified, trusted sources and provide
  links for manual review.
- **Fully autonomous.** No manual input required; flag irregularities for review rather than
  asking.
- **Data must be free, public and official.** State limitations and what access would be needed.
- **Never commit competition rasters or data** — this repository is PUBLIC (`.gitignore` covers
  `data/`, `.cache/`, `releases/*.tif`).
- **Negative results are deliverables.** Report them; never invent a win.
- **Three passes:** (1) implement and verify, (2) review for bugs, missing requirements, bad
  assumptions and edge cases, and fix, (3) re-check everything against the original request and
  improve accuracy, reliability, completeness and code quality. Do not stop after pass 1.
- **Arena's core values stay central: Maximize P(Win) and Own the Outcome.**

---

## 2. What the metric actually rewards (verified)

From the official problem description
([page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)), with
`k(d) = max(1 − d/R, 0)` and `R = 300 m = 3 px`:

```
DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + ε)
```

Because `FN_w = |G| − TP_w` exactly and `α + β = 1`, this collapses to

```
DTI = T / (0.2·T + 0.2·(S − M) + 0.8·|G|)
```

with `T` the coverage credit on hidden faults, `S = Σp` the total predicted mass and `M` the part
of that mass lying near truth. Three consequences, all unit-tested in `tests/test_metric_exact.py`:

1. `0.8·|G|` is a constant — the floor nobody can move.
2. **Mass is bang-bang:** emit 1.0 or nothing; fractional confidence maps are strictly dominated.
3. **The dot budget is endogenous:** a dot far from truth pays only if its coverage credit beats
   `0.2θ/(1 − 0.2θ)` ≈ **0.059 at θ = 0.2778**.

---

## 3. Why the incumbent 0.2778 is the best file so far

Inverting the identity against 14 locally held scored rasters (`evidence/blind_probe_inversion.json`):

- A uniform 5 px lattice is spatially blind, so its credit is its mean coverage × |G| whatever the
  truth looks like. Its 0.0904 pins **|G| ≈ 12,545 hidden-fault pixels** (0.246 % of the scored
  domain). The independent blind "placeholder" raster lands at lift 0.71 — the consistency check.
- Every *targeted* raster saturates at `T` ≈ 5,000–6,900, i.e. 40–55 % of all available credit,
  with blind-lift 3.4–6.8×. They differ mainly in **dot count**.
- `h33-h33-2-b2` is **not** the most accurate file — `hedge_v2` and `h19_5` capture more credit.
  It wins because it captures nearly the same credit with the smallest budget: **0.134 credit per
  dot against a 0.059 break-even**, while the 120k–200k-dot files were buying credit at ~0.02–0.04
  per dot, i.e. below cost.

**So the lever is credit efficiency, not map accuracy** — that is this session's lane.

---

## 4. Current state (2026-10-24)

- **Candidate:** see `evidence/candidate_receipt.json` and the top of
  [the site](docs/index.html). Unique (duplicate screen passed), format-gate PASS, zeros outside
  the footprint, all-finite, values in [0, 1].
- **HOLDOUT-DTI** (evaluator `gems90-holdout-1.0.0`, 4 buffered whole-segment folds, visible-only
  catalogue features, pooled with a fold×block bootstrap CI): reported in
  `evidence/holdout_report.json` and `evidence/holdout_budget_curve.json`. Controls at the same
  budget: uniform-lattice chance, a fold-honest rebuild of the collar recipe, and the incumbent
  raster as submitted.
- **Two calibration attempts against the 14 owner-reported scores FAILED** (negative result, see
  `evidence/calibration_fit.json`, `evidence/band_profile.json`). Under a physically valid
  occupancy field both under-predict every targeted raster by ≈ 2×. **No leaderboard projection is
  claimed for the candidate.**
- **Measured bias of the local holdout:** it withholds *catalogue* segments, so its truth lies on
  catalogue traces and any collar-style file that avoids the 3 px neighbourhood of the catalogue
  scores ≈ 0 by construction (the incumbent measures 0.0048, below the 0.052 chance lattice).
  A holdout win over the collar control is therefore **not** evidence of a leaderboard win.
- **Best receipt on file: none.** Every historical score in this repository is OWNER-REPORTED.
- **No weekly slot was selected.**

## 5. Reproduce

```bash
python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/restore_data.py          # 26 pinned inputs, SHA-256 verified
./.venv/bin/python scripts/run_discovery.py all     # features -> folds -> deploy  (~12 min)
./.venv/bin/python scripts/invert_blind_probes.py   # |G| from the blind lattice probe
./.venv/bin/python scripts/calibrate.py             # occupancy-capped score calibration
./.venv/bin/python scripts/band_profile.py          # model-free radial inversion
./.venv/bin/python scripts/evaluate_holdout.py      # HOLDOUT-DTI + block-bootstrap CIs
./.venv/bin/python scripts/make_submission.py       # emit -> screen -> validate -> GeoTIFF
./.venv/bin/python scripts/make_run_card.py && ./.venv/bin/python scripts/build_site.py
./.venv/bin/python -m pytest -q
```

Competition rasters are never committed; `releases/` and `.cache/` are gitignored.

## 6. Layout

| path | contents |
|---|---|
| `src/metric.py` | exact DTI (triangular kernel, algebraic identity, break-even) |
| `src/holdout.py` | buffered whole-segment folds, pooled DTI, block bootstrap, leakage canary |
| `src/featstack.py` | 54 static features + 9 fold-honest catalogue features |
| `src/emit.py` | greedy DTI-optimal emission, DTI curve, raster writer |
| `src/submission_writer.py` | fail-closed writer + validator (CRS/shape/transform/range/NaN) |
| `scripts/` | pipeline stages, calibration, holdout CLI, submission builder, site builder |
| `evidence/` | every JSON receipt referenced above |
| `docs/` | site, knowledge base, run card, submit checklist |
| `ledger/` | submission ledger (ORGANIZER-CONFIRMED scores only once a receipt exists) |
| `registry/data_manifest.json` | 26 pinned inputs with SHA-256 and provenance |

## 7. Known irregularities

1. DrivenData and Dropbox are unreachable from the build sandbox; competition files come from
   GitHub-pinned mirrors listed in `registry/data_manifest.json` — byte-consistent, but **not
   organizer-authenticated**.
2. `labels.tif` and `existing_faults.tif` in that mirror are byte-identical: the training labels
   *are* the catalogue.
3. All 14 calibration scores are OWNER-REPORTED; no submission-page receipt exists in this repo.
4. Two registry rasters are pixel-identical off-catalogue, differ by 54,533 on-catalogue pixels and
   both scored 0.1563 — direct evidence that catalogue pixels are masked from scoring.
5. The kernel's distance metric is assumed Euclidean in pixels; the published text does not say.
6. The three "current leaderboard" values quoted in the brief cannot be verified from this sandbox;
   a human must read the live leaderboard.
