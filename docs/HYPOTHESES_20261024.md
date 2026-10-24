# Candidate hypotheses — session 2026-10-24 (branch `arena/96081fbe-gemsdoe90`)

Written **before** implementation, per the brief. All layers named below are already
restored and SHA-256-verified locally (`registry/data_manifest.json`, 26/26 pins,
`.cache/gems_data/`), so every candidate is buildable with **no new external data**.
Grid: 100 m px, 3730×3292, EPSG:32611, footprint 5,167,373 px, catalogue
(`existing_faults.tif` ≡ `labels.tif`) 60,988 px.

## Why `h33-h33-2-b2` = 0.2778 (CLAIM, owner-reported, no receipt) is the incumbent

Verified from the pinned rasters, not from filenames:

- `H19-5` support: 121,131 binary px, **zero catalogue mass** (multi-line corroborated support).
- dotted `d2.8`: 44,090 unit dots (greedy 2.8 px min-separation thinning of that support).
- `h27-4 solo`: 40,199 dots. **R0 `h33-h33-2-b2` = h27-4 ∩ (d_catalogue > 2 px) = 37,654 unit dots**
  (byte-identical rebuild verified by `scripts/build_r0_variants.py`).
- CLAIM ladder in `ledger/submissions.csv`: continuous H19-5 0.1922 → dotted d1.5 0.2477 →
  dotted d2.8 0.2600 → solo d2.8 0.2708 → **+ (d>2 px collar) 0.2778**.

Mechanistic reading (DTI α=0.2, β=0.8, 300 m triangular kernel, `src/dti.py`):

1. **Unit-dot (Poisson) emission beats continuous mass.** Every unit of predicted mass
   pays α·(1−k) false-positive rent unless it earns kernel credit; overlapping dots
   duplicate the *same* max-credit. Sparse 2.8 px-separated dots maximise *unique*
   kernel coverage per unit mass — hence +0.055…+0.068 for dotting alone.
2. **Zero catalogue mass.** The scored truth is faults *missing* from the catalogue;
   mass on/near mapped faults earns nothing. Counter-example on file: `ens12-7f00890a`
   (172,974 px, 6,455 px of catalogue mass) CLAIMs only 0.1563.
3. **~38–44 k dots is the empirical budget sweet spot** (80 k-dot physics file: 0.1193;
   100 k-dot tilt ring: 0.0005 — mass, not geology, killed both).
4. **The support, not the dotting, is now the ceiling.** Every 2026-10-23/24 repo edit
   (PRUNE/MASS/RELIEF/CONCENTRATION/SPACING) only re-arranges R0's dots on the *same*
   H19-5 support; all MODEL deltas are ≤ +0.022 and measured arrangement headroom is
   < 0.010 (IR90-37). Beating 0.2778 materially — let alone the owner-reported
   leaderboard top 0.4413 — requires a **better support surface**, then the same
   dotted emission. That is this session's lane.

Why prior supervised ML in the CLAIM ledger failed (HGB 0.0286, sup01 0.0424, …):
plausibly (i) trained to reproduce the *catalogue* (scored truth is off-catalogue),
(ii) leakage / random-split validation, (iii) continuous or on-catalogue emission.
Each failure mode is directly testable and avoidable — see H1.

## Candidates (ranked by expected DTI gain ÷ implementation cost)

### H1 — Fold-clean learned off-catalogue fault-ness surface + surface-ranked Poisson emission ★ TOP
- **Layers:** all 19 `training_features` bands + derivatives (gradient magnitude /
  |Laplacian| of `tmi` b14, `iso_grav_anom` b13, `depth_to_base_surf` b15,
  `det_elev` b12; multi-scale σ=3 px `tmi_hg`, `det_elev_slope`; high-pass magnetic
  residual), 12-band USGS-3DEP lidar-scarp stack, GeoDAWN radiometrics (K/Th/U/TC +
  Th/K, U/K, U/Th) + `TMI_up150`.
- **Signature:** classifier score = P(pixel lies on a fault trace) from *physical*
  layers only; **no catalogue-derived feature** (no distance-to-catalogue etc.).
- **Why it catches uncatalogued faults:** faults offset magnetic basement, juxtapose
  conductivity/lithology, and scarp the surface whether or not a mapper drew them;
  trained on visible blocks only and applied everywhere, it generalises the
  *expression* of faulting to unmapped ground. Emission then forbids d_cat ≤ 2 px,
  so all mass is off-catalogue by construction.
- **Differs from repo history:** every BUILT candidate in this repo edits R0's dots;
  none builds a new surface. Differs from failed sibling ML: blocked (25 km)
  hide-and-recover validation with pixel-exact visible-fault masking, per-feature
  leakage canary (AUC > 0.90 = stop), off-catalogue dotted emission at the proven
  2.8 px / collar recipe.
- **Non-fault mimicker:** lithologic contacts / survey seams produce identical
  magnetic+radiometric edges; the classifier may simply learn "contact", not "fault".
- **Cost:** medium (feature stack + HGB + emission, all CPU). **Rank 1.**

### H2 — Buried basement-step faults under basin cover
- **Layers:** `depth_to_base_surf` (b15) gradient ridge ∩ `iso_grav_anom_hg` (b18) ridge.
- **Signature:** co-located steep basement-deepening step + gravity edge = blind
  basin-bounding normal fault with no surface scarp (invisible to lidar & photo-mapping,
  hence missing from the catalogue). Standalone basement-step CLAIMed 0.0009 (h61a), so
  this is viable only as a *corroborated* component — it enters H1 as derivative bands.
- **Mimicker:** depositional pinch-outs / buried paleo-valleys step the basement too. **Rank 2 (folded into H1).**

### H3 — Shallow-source magnetic residual edges
- **Layers:** `rtp` (b2) minus upward-continued field (`TMI_up150`), gradient magnitude.
- **Signature:** edges that exist only at shallow depth = young faults offsetting
  near-surface volcanics/alluvium (deep basement contacts survive upward continuation).
- **Mimicker:** shallow volcanic flow margins / buried channels. **Rank 3 (feature inside H1).**

### H4 — Dilational-jog / intersection nodes
- **Layers:** `tmi_hg` ridge × `iso_grav_anom_hg` ridge acute intersections + high
  `geod_dilaterate` (b8). Geothermal permeability localises at stepovers/intersections.
- **Why:** scored truth is fault *pixels* (line density), node-only files CLAIMed ≤ 0.1193;
  nodes cannot carry enough line-km. **Rank 4 — not built standalone.**

### H5 — Along-strike tip continuation of catalogue segments
- **Layers:** catalogue skeleton endpoints + strike extrapolation, corroborated by
  `tmi_hg` / lidar `step_max`. Already probed entity-wide (tip/stepover 0.2632 as a
  re-cut of dotted support; tip-relay 0.0159; relay-ramp 0.0053) and it is catalogue-derived,
  needing visible-only derivation per fold. **Rank 5 — not built this session.**

## Validation gate (binding)

Top candidate H1 must beat the incumbent-recipe arm on **spatially-blocked
hide-and-recover HOLDOUT-DTI** (25 km blocks, buffer, visible faults masked
pixel-exactly, catalogue-derived features from visible faults only — here: none;
pooled DTI α=0.2 β=0.8 R=3 px, block-bootstrap 95 % CI) before it is marked
download-and-submit. Uniqueness vs every registry raster: surface rank-correlation
≤ 0.90 **and** ≤ 70 % of final dots within 3 px of any single registry raster's dots;
otherwise log as duplicate and stop. Format gate `src/validate.py` must PASS on the
zeros-outside file actually offered for download (the owner's
"Predicted values must be in range [0, 1]" rejection cannot occur on an all-finite
{0,1} float32 raster with no nodata sentinel).

Official sources (manual review): competition
https://www.drivendata.org/competitions/306/competition-doe-gems/ · rules PDF
https://docs.nlr.gov/docs/fy26osti/96647.pdf · reference solution
https://github.com/drivendataorg/gems-prize-reference-solution · GeoDAWN
https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
(DOI 10.5066/P93LGLVQ) · INGENIOUS/GDR 1391 https://gdr.openei.org/submissions/1391 ·
EPSG:32611 https://epsg.io/32611 · Tversky index https://en.wikipedia.org/wiki/Tversky_index
