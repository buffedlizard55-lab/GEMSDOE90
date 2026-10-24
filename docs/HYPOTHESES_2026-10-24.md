# Untried hypotheses, ranked — 2026-10-24

Required format: layer(s) → physical signature / transform → why it finds faults the
USGS/INGENIOUS catalogue lacks → how it differs from existing repository work → expected DTI gain
and cost. Ranked by expected gain per unit cost. **H1 was the one implemented and tested this
session.** Nothing here is a score; expectations are explicitly labelled.

Geological grounding and citations: [`KNOWLEDGE_BASE_GEOTHERMAL.md`](KNOWLEDGE_BASE_GEOTHERMAL.md).

---

## H1 — Credit-efficient adaptive emission (IMPLEMENTED AND TESTED)

- **Layers.** All 19 competition bands + GeoDAWN radiometrics and ratios + lidar scarp
  morphometry + SGMC faults + GDR 1391 wells/springs/Quaternary slip rates/vents (54 static
  features), plus 9 catalogue-geometry features rebuilt per fold.
- **Signature / transform.** Learn `P(unmapped fault trace | x)` by buffered whole-segment
  hide-and-recover, then emit unit-mass dots greedily against the exact coverage objective and
  stop where marginal credit crosses the metric's break-even `0.2θ/(1−0.2θ)`.
- **Why it finds missing faults.** It is trained on the actual task — "the catalogue does not show
  this segment, can the geophysics still see it?" — rather than on proximity to what the catalogue
  already shows.
- **Difference from existing work.** Every prior candidate in this repository and its siblings is
  an arrangement operator applied to the same parent collar raster (prune, respace, shadow, relief
  reallocation, concentration). None learns a surface, and none chooses its own budget.
- **Expected gain / cost.** Gain unknown a priori; cost ≈ 25 min of compute.
- **Result.** HOLDOUT-DTI **0.3019** [0.2834, 0.3208] at the measured optimal budget of 35,000
  dots, versus 0.0524 for a uniform-lattice chance baseline at the same budget and 0.0044 for a
  fold-honest rebuild of the collar recipe. **But** the holdout is structurally blind to collar
  files, and two calibrations against the 14 owner-reported scores failed, so no leaderboard
  claim is made. Candidate shipped for human review; see `docs/run-card.json`.

## H2 — Relay-ramp linking structures at the published scale (NEXT, highest expected value)

- **Layers.** `existing_faults.tif` geometry; `geod_shearrate` / `geod_dilaterate`;
  `iso_grav_anom_hg`; `tmi_hg`.
- **Signature / transform.** Detect overlapping, same-dip strand pairs whose along-strike overlap
  and separation match the published relay-ramp statistics — mean width **2.8–3.5 km = 28–35 px**,
  ~59 % right-stepping, dominantly N–NNE striking — then emit along the *linking* direction inside
  the ramp (the hard-linkage fractures), not in a uniform collar.
- **Why it finds missing faults.** Step-overs host ~32–40 % of all Great Basin geothermal systems
  while main range-front segments host ~2 %; the linking strands inside a ramp are small, often
  unmapped, and are exactly where enhanced fracture permeability is expected.
- **Difference from existing work.** The repository's collar operates at 3–4.5 px. This operates at
  28–35 px, an order of magnitude further out, with a geometry test rather than a distance rule.
  No sibling has tested ramp geometry at the published scale.
- **Expected gain / cost.** Highest of the untested set: it is the only hypothesis with a published
  quantitative prior for *both* position and scale. Cost ≈ 1–2 h (pair detection on 3,199
  segments, then emission).

## H3 — Horsetail splay fans at fault terminations

- **Layers.** Catalogue tip geometry; lidar scarp morphometry; `det_elev_slope`.
- **Signature / transform.** At each mapped trace tip, fan candidate splays over ±30° within
  1–5 km and keep the arcs supported by scarp morphometry or slope breaks.
- **Why it finds missing faults.** Terminations host ~16–25 % of systems and splay into many short
  strands that a regional catalogue typically generalises into a single line.
- **Difference from existing work.** `src/featstack.py:tip_continuation` extends a trace along
  strike as a single ray; this is an angular fan with an independent surface-morphology test.
- **Expected gain / cost.** Moderate gain, ≈ 1 h.

## H4 — Accommodation zones from opposed dip directions

- **Layers.** SGMC fault dip-direction attributes; GDR 1391 Quaternary fault table (slip rates,
  joined by centroid); `geod_dilaterate`.
- **Signature / transform.** Find belts where mapped faults of *opposite* dip intermesh, and emit
  between the opposed arrays.
- **Why it finds missing faults.** Accommodation zones host ~6–9 % of systems and generate many
  subsurface intersections whose surface traces are short and poorly mapped.
- **Difference from existing work.** No repository feature currently uses dip direction at all.
- **Expected gain / cost.** Lower share of systems, but it is an untouched signal. ≈ 1–2 h, with a
  data risk: dip attributes must be recovered from SGMC, which is not yet pinned in the manifest.

## H5 — Potential-field "worms": gradient-maxima lineaments as direct fault proxies

- **Layers.** `iso_grav_anom` and `tmi` multiscale horizontal-gradient maxima.
- **Signature / transform.** Upward-continue at several heights, track horizontal-gradient maxima,
  and keep lineaments that persist across scales (classic worm analysis).
- **Why it finds missing faults.** It detects basement-offset contacts with **no surface
  expression at all** — the true blind case, which neither a surface-trace catalogue nor lidar can
  contain.
- **Difference from existing work.** The repository uses raw gradient magnitudes as pixel features;
  nothing performs multiscale ridge tracking into lineaments.
- **Expected gain / cost.** Potentially the largest reach, but the highest variance: gradient
  maxima also track intrusive contacts and lithologic boundaries that are not faults. ≈ 2 h.

---

## Named non-fault mimic (required, applies to all of the above)

**Quaternary alluvial-fan toe scarps and pluvial Lake Lahontan shoreline terraces.** Both produce
metre-scale, kilometres-long linear slope breaks whose lidar morphometry is nearly identical to a
young fault scarp, and the Lahontan shorelines additionally wrap every range front at constant
elevation. Neither carries a magnetic or gravity offset. This is why the feature stack keeps
potential-field gradients separate from scarp morphometry instead of fusing them into one
"lineament" score, and why H5 must be cross-checked against lithologic contacts.
