# Audit and research plan — 2026-10-24

## Pass 1: repository and provenance
Read README, manifest, submission guide, metric and validator. The requested shared `evaluate_holdout.py` and `submission_writer.py` do not exist here. `src/dti.py` explicitly describes an unverified metric proxy: it cannot establish an official holdout win. No assigned single-method paragraph was supplied. No experiments or weekly submissions were run; no TIFF was copied or renamed as a new result.

Official reference README retrieved through GitHub API into `evidence/official-reference-readme.md`. Source: https://github.com/drivendataorg/gems-prize-reference-solution . It supports CPU-only execution: the prompt's blanket GPU requirement is not a requirement of the reference project. Competition/USGS/NLR/Dropbox hosts are outside this sandbox's outbound allowlist; their contents and current leaderboard have not been independently fetched. GitHub mirrors are pinned for reproducibility, not organizer authentication.

## Why the historical parent may have worked
The manifest identifies the historical parent as a sparse dotted raster; README records catalogue-collar filtering and fixed-count refill. Under the repo's assumed triangular-kernel metric, sparse spatial coverage can trade off redundant predicted mass against truth coverage. This is a mechanism, **not a proven causal explanation** of a leaderboard result. The requested historical score lacks an organizer receipt. Conflicting current-leaderboard claims cannot be reconciled from accessible evidence. No defensible promise of exceeding them can be made.

## Candidate hypotheses (unexecuted; qualitative ranking only)
These are transform-level research proposals, not demonstrated geological discoveries or globally unique lanes. Existing repo scripts implement mass, relief, concentration, collars and spacing; related sibling work makes registry checks mandatory. All use already-manifested layers, avoiding claims that inaccessible new data are obtainable.

|Priority / cost|Layers and physical signature|Why potentially off-catalogue; difference from local implementation|Non-fault mimic|
|---|---|---|---|
|First / medium|GeoDAWN radiometric channels + DEM: locally detrended K-versus-Th ratio discontinuity, conditioned on low relief and cross-edge symmetry|Could expose altered buried contacts rather than catalogue extensions; adds conditional radiometric ratio transform, not a parent-dot reallocation|Lithologic contact or transported alluvium|
|Second / high|Magnetic grid + DEM: phase-congruent edges persisting across upward-continuation scales, retaining only edges discordant with topographic aspect|Potential concealed basement breaks; explicitly tests phase persistence and aspect disagreement instead of spacing existing dots|Dike or survey seam|
|Third / high|DEM + radiometrics: aligned residual curvature discontinuities across several adjacent fan surfaces, with radiometric continuity across the break|Potential young cross-fan scarps not mapped as existing traces; requires repeated-surface geometry, not relief-tercile quotas|Terrace riser, canal or road|

Expected benefit ranking is speculative. Confirm band identities/units and cached coverage before implementing. Do not call these viable validated improvements yet. Training targets must remain faults, not geothermal vent locations: vents are contextual evidence, not interchangeable labels.

## Pass 2: defects corrected
The shared validator previously accepted positive/negative infinity inside the footprint because its range test discarded nonfinite values. It now rejects all nonfinite predictions, matches sample CRS explicitly, respects the reference GDAL validity mask and checks catalogue CRS/transform. New exact full-footprint uniqueness utility checks directional proximity and Spearman correlation; constant surfaces, empty predictions and malformed shapes fail closed. This utility does not certify registry completeness or replace holdout evaluation.

## Pass 3: original-request reconciliation
Added Pages dashboard, executive submission guide and negative run card. No approval/download link is shown without supporting evidence. Existing README/slot plan is historical and does not override the new readiness warning. The user's request for an immediately submit-ready unique TIFF remains **unfulfilled**, because inventing an evaluator, baseline or lane would violate the same request's safeguards. Next session: restore the shared template and complete registry, establish segment-based baseline and writer, assign a lane, run at most three experiments, and publish only a proven candidate through an approved private distribution channel. No automated live feed is claimed.

Official reference source commit observed: `aebe92f7c8a990f0e3443451b7a825d9afd6336b`. Retrieved via GitHub API on 2026-10-24; external competition pages not fetched.
