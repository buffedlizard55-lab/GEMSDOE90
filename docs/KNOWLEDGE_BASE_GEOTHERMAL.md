# Knowledge base — finding hidden faults and blind geothermal systems in the Great Basin

A reusable, cited reference for this project and future ones. Every claim has a link to a
primary or official source. Nothing in this file is a competition score.

Last updated 2026-10-24. Sources were read through the links below; where a PDF could not be
retrieved from this sandbox the search-result extract is quoted and marked **(extract)**.

---

## 1. The target: faults the catalogue does not have

### 1.1 Why unmapped faults matter for geothermal
Blind (hidden) systems have no surface hot springs, fumaroles or sinter. Coolbaugh et al. (2006),
as quoted by Faulds et al., estimate **~75 % of Great Basin geothermal resources are hidden**, and
**~39–40 % of *known* Nevada systems are already blind**
([Faulds & Hinz 2015, WGC](https://pangea.stanford.edu/ERE/db/WGC/papers/WGC/2015/11100.pdf);
[Faulds et al. 2026, SGW](https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2026/Faulds.pdf)).
Most of the blind systems that have been found were found **accidentally**, while drilling for
agriculture or minerals ([DE-EE0006731 final report, OSTI](https://www.osti.gov/servlets/purl/1724080)),
which is exactly the gap a fault-prediction model is meant to close.

### 1.2 Structural settings that host systems — the prior that matters
From an inventory of **426 systems ≥ 37 °C** across the Great Basin
([Faulds & Hinz 2015](https://pangea.stanford.edu/ERE/db/WGC/papers/WGC/2015/11100.pdf);
[GDR submission 355](https://gdr.openei.org/submissions/355);
[OSTI dataset 1148722](https://www.osti.gov/dataexplorer/biblio/dataset/1148722)):

| setting | share of systems | geometry to look for |
|---|---|---|
| Step-overs / relay ramps in normal faults | ~32 % (and ~40 % of favourable settings in the 2026 update) | two overlapping, same-dip strands with minor linking faults between them |
| Normal-fault terminations / horsetails | ~16–25 % | a trace that splays into several short strands at its tip |
| Fault intersections | ~22–26 % | transverse oblique-slip faults cutting normal faults |
| Accommodation zones | ~6–9 % | intermeshing, *oppositely* dipping normal-fault arrays |
| Displacement transfer zones | ~1.4–5 % | strike-slip fault dying into a normal-fault array |
| Pull-aparts | ~2–3 % | releasing steps in strike-slip zones |
| Major range-front fault segments | **~2 %** | thick clay gouge, low permeability — *not* prospective |

Two consequences used by this repository:

1. **Interaction zones, not master traces.** >85 % of systems — and nearly all >130 °C systems —
   sit in fault *interaction* zones rather than along main range-front segments
   ([Faulds et al. 2019, SGW](https://pangea.stanford.edu/ERE/pdf/IGAstandard/SGW/2019/Faulds.pdf)).
   Geothermal-relevant unmapped structures are therefore expected **near, but off,** mapped master
   traces: linking strands in step-overs, splays at tips, and cross-faults at intersections.
   This is the geological justification for the repository's `tip_continuation` and `orientation`
   features and for the "collar" family of submissions.
2. **Geometry statistics are quantitative.** In the INGENIOUS study area, right-stepping
   step-overs dominate (≈59 %), relay-ramp widths average **2.8–3.5 km**, and >73 % of step-overs
   are on strands striking N to NNE, mostly west-dipping
   ([Giddens & Faulds 2025, SGW](https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Giddens.pdf)).
   A 2.8–3.5 km ramp width is **28–35 pixels** on the competition's 100 m grid — i.e. the
   "missing" linking structure in a step-over is usually *tens* of pixels from the mapped trace,
   not 3–5.

### 1.3 Validated discoveries by this method
Nevada Play Fairway Phase 3 drilled two blind systems found by this reasoning: **Gabbs Valley**
(≈125 °C at ~152 m) and **Granite Springs Valley** (≈96 °C at 250 m)
([GBCGE project page](https://gbcge.org/recent-projects/nevada-play-fairway-phase-3/);
[USGS publication 70201803](https://pubs.usgs.gov/publication/70201803)). Both sit in
displacement-transfer / fault-termination settings with **no** surface expression — the end-member
case of a fault that a surface-trace catalogue cannot contain.

---

## 2. The data that can expose an unmapped fault

| signature | layer in this competition | physical basis |
|---|---|---|
| Offset of magnetic marker horizons; linear gradients | `mag_anom`, `rtp`, `tmi`, `tmi_hg`, `tmi_vg` | a fault juxtaposes rocks of different susceptibility; terracing/horizontal-gradient maxima track the contact |
| Basin-depth steps | `depth_to_base_surf`, `iso_grav_anom`, `..._hg`, `..._vg`, `geod_2ndinv` | normal faults step the basin floor; gravity horizontal-gradient maxima sit over the fault |
| Hydrothermal alteration / K-enrichment | GeoDAWN radiometrics (K, Th, U, TC and ratios) | up-flow zones alter wall rock, changing surface K/Th |
| Surface scarps | lidar-derived scarp morphometry (3DEP) | Quaternary ruptures leave metre-scale scarps |
| Active strain | `geod_shearrate`, `geod_dilaterate` | GPS strain-rate fields; systems cluster in high-strain transtensional belts ([Faulds et al. 2012](https://gdr.openei.org/files/383/Faulds%20et%20al%202012%20GeoNZ%20Paper.pdf)) |
| Thermal fluids at surface | GDR 1391 wells/springs | direct evidence of an up-flow conduit |
| Independent geologic mapping | SGMC faults | faults mapped by a different programme than the competition catalogue |

Official sources for the external layers (all free, no login):

- **USGS GeoDAWN** airborne magnetic and radiometric surveys, NW Great Basin —
  [doi:10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ),
  [USGS data page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- **INGENIOUS / GDR submission 1391** — [gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391),
  project page [gbcge.org/current-projects/ingenious](https://gbcge.org/current-projects/ingenious/).
- **USGS SGMC** (State Geologic Map Compilation) — national geologic map database.
- **USGS 3DEP** lidar — source of the scarp morphometry layer.
- **GDR 355** structural inventory of Great Basin geothermal systems —
  [gdr.openei.org/submissions/355](https://gdr.openei.org/submissions/355).

Machine-learning precedent inside play-fairway analysis:
[Exploratory analysis of ML techniques in the Nevada PFA, *Geothermics* 2023](https://www.sciencedirect.com/science/article/abs/pii/S0375650523000470).

---

## 3. The competition metric, and what it rewards

Official definition (problem description page
[967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)):
with `k(d) = max(1 − d/R, 0)` and `R = 300 m` (**3 pixels** at 100 m),

```
TP_w = Σ_{g∈G}  max_{x : d(x,g)≤R} p(x)·k(d(x,g))
FP_w = Σ_{x : p(x)>0} p(x)·[1 − max_{g} k(d(x,g))]
FN_w = Σ_{g∈G} [1 − max_{x} p(x)·k(d(x,g))]
DTI  = TP_w / (TP_w + α·FP_w + β·FN_w + ε),   α = 0.2, β = 0.8
```

Three algebraic consequences drive every design decision in this repository
(derivation and unit tests in `src/metric.py`, `tests/test_metric_exact.py`):

1. **`FN_w = |G| − TP_w` exactly**, so with `α + β = 1` the metric collapses to
   `DTI = T / (0.2·T + 0.2·(S − M) + 0.8·|G|)` where `T = TP_w`, `S = Σp`, `M = Σ_x p·maxₖ`.
   `0.8·|G|` is a **constant** — the denominator floor nobody can move.
2. **Mass is bang-bang.** Scaling every prediction by γ scales T, S and M but not `0.8|G|`, so DTI
   increases monotonically in γ: emit 1.0 or nothing. Fractional "confidence" maps are strictly
   dominated.
3. **The dot budget is endogenous.** A dot far from truth adds `0.2` to the denominator and its
   coverage credit to the numerator, so it pays only if that credit exceeds
   `θ′ = 0.2θ/(1 − 0.2θ)` — **0.059 at θ = 0.28**. Dots sitting *on* truth cost nothing
   (`m = 1`), so optimal spacing is tight where confidence is high and absent where it is not.

Independent corroboration of the masking rule: the organizers mask pixels belonging to the
provided fault catalogue, pixel-exactly, including at final re-scoring
([organizer forum clarification, mirrored](https://github.com/Svyable/GEMS-CONTEST);
[free local scorer write-up](https://dev.to/munimv2/what-the-doe-gems-prize-metric-actually-rewards-and-a-free-local-scorer-4054);
[open scorer implementation](https://github.com/munimtechnologies/gems-fault-mapping)).
**Confirmed independently in this repository**: two of our rasters are pixel-identical off the
catalogue, differ by 54,533 on-catalogue pixels, and scored identically (0.1563).

Official baseline: [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
— U-Net (resnet18/imagenet), 5 Monte-Carlo splits, 5 epochs, AdamW 1e-4, Tversky loss (0.2/0.8).
It contains no scoring code.

---

## 4. Evaluation design for "faults missing from a catalogue"

The only labels available are the catalogue itself, so any local evaluation is a **proxy**. Two
designs, with the bias each carries — measured, not assumed:

| design | what it measures | measured bias |
|---|---|---|
| **Buffered whole-segment hide-and-recover** (this repo, `src/holdout.py`) — withhold entire fault segments by spatial block, rebuild catalogue-derived features from visible faults only, mask visible faults, score with the exact metric | ability to find a *mapped trace* that the catalogue does not show | structurally blind to collar-style predictions: a raster whose dots are all ≥ 3.4 px off-catalogue can never score on withheld catalogue pixels (kernel support is 3 px). Measured: the incumbent raster scores **0.0048** here versus **0.052** for a uniform lattice. |
| **Chance baseline by translation** (Munim) — shift the prediction 14–21 km and re-score | how much of a score is geography rather than skill | needs a real score to compare against |

Neither proxy is the real target (expert-mapped faults absent from the catalogue). The repository
therefore reports both a HOLDOUT-DTI with a spatial-block bootstrap CI **and** a model-free
inversion of actual organizer-scored rasters, and refuses to convert either into a predicted
leaderboard score.

---

## 5. Reusable findings from this repository (2026-10-24)

1. **|G| ≈ 12,500 hidden-fault pixels.** A uniform 5 px lattice covers every pixel with the same
   expected kernel credit, so its score pins the number of hidden-fault pixels independent of
   where they are: **12,440–12,632** (0.246 % of the scored domain, ≈ 1/5 of the catalogue's
   60,988 px). `evidence/blind_probe_inversion.json`.
2. **The incumbent won on price, not accuracy.** Implied credit `T` saturates at 5,000–6,900
   (40–55 % of |G|) for every targeted raster; they differ mainly in dot count. The best-scoring
   file is simply the cheapest member of that family (0.134 credit/dot vs a 0.059 break-even),
   not the most accurate one. Everything above ~40 k dots in that family was bought below cost.
3. **A learner trained by hide-and-recover does not reproduce the organizer-score history.** With
   the field constrained to a physically valid occupancy field (0 ≤ π ≤ 1, Σπ = |G|), the best fit
   across 14 scored rasters has RMSE 0.061–0.093 and under-predicts every targeted raster by
   roughly a factor of 2. A model-free, band-wise non-negative inversion does no better
   (RMSE 0.085, LOO 0.111). Something about where those dots sit is not captured by
   distance-to-catalogue *or* by the current feature stack. `evidence/calibration_fit.json`,
   `evidence/band_profile.json`.
4. **Collar files are invisible to catalogue hide-and-recover**, quantified above — so a holdout
   win over a collar baseline is *not* evidence of a leaderboard win over it.

---

## 6. Open leads worth trying next (not yet tested)

1. **Step-over geometry at the published scale.** Relay ramps average 2.8–3.5 km wide
   (28–35 px). Detect overlapping, same-dip strand pairs in the catalogue and emit dots along the
   *linking* direction inside the ramp, not in a uniform 3–4 px collar. This is the single
   best-supported geological prior in the literature and the repository has never tested it at the
   published ramp scale.
2. **Horsetail splays at fault tips.** ~16–25 % of systems sit at terminations; splays fan out
   over kilometres. The existing `tip_continuation` feature extends a trace along strike only.
3. **Oppositely-dipping strand pairs (accommodation zones).** Needs a dip attribute; SGMC carries
   dip direction for many mapped faults, and the GDR 1391 Quaternary fault table carries slip
   rates and can be joined by centroid.
4. **Gravity/magnetic gradient-maxima lineaments as direct fault proxies** (worm analysis), which
   predict faults with no surface expression at all — the true blind case.
