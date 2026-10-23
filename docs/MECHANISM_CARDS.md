# Mechanism cards


## Session 2026-10-23 (2): AXIS = PRUNE, value family = strike-aligned (anisotropic) collar

Parent R0 `h33-h33-2-b2`: 37,654 unit-mass dots, isotropic >2 px catalogue collar; 0.2778 is a **CLAIM**
(no submission-page receipt). These three files are **BUILT**, format-gated and unscored. Their predictions are
**MODEL**. Files live in ignored `releases/`; hashes and full statistics are in `evidence/build_aniso_receipt.json`.

Shared hypothesis, written for a structural geologist: the parent's collar treats positional error as
direction-free, but the two directions do different work. Across strike, a dot 2–3 px from a mapped trace is
usually flank mass: the known pixels there are masked anyway, so it earns penalty without new credit. Along
strike, a dot near a mapped trace is plausibly the continuation of that system — geometry the organiser says is
still scored as "new". A collar that widens only across strike should therefore buy the precision gain of a
3 px uniform collar while keeping the along-strike credit a uniform 3 px collar would throw away.

Mechanism: local strike from a structure tensor of the catalogue mask (major eigenvector = across strike, since a
thin trace's gradients run across it); each dot is projected onto that frame at its nearest catalogue pixel and
removed if `(along/2)² + (across/A)² ≤ 1`. Where the tensor is incoherent (< 0.3), no along-strike exemption is
granted and the collar falls back to isotropic A. The count is held at 37,654 by refilling from the pinned
H19-5 support in the lineage's recovered FIFO-BFS thinning order, outside the collar.

| Variant | Removed / refilled | % of R0 changed | Along-strike dots kept that an isotropic collar of the same radius deletes | Predicted live change (MODEL) | Non-fault confounder | Falsifier |
|---|---|---|---|---|---|---|
| A4 (`…0bf248e2`) | 2,632 | 13.98 % | 1,193 | **+0.003** (−0.010 to +0.010) | A parallel strand or a step-over a few pixels across strike from a mapped trace is a real fault, not flank noise; steeply dipping strands surface offset from their mapped trace. | Paired same-week Δ ≤ −0.010 rejects the across-strike-only collar at this dose; \|Δ\| < 0.010 is no evidence. |
| A5 (`…15218061`) | 3,663 | 19.46 % | 1,974 | **+0.002** (−0.010 to +0.010) | Same, plus: the refill pool shrinks and its replacement pixels get worse as the collar widens. | As above; a monotone decline over A4→A6 rejects the dose-response the mechanism implies. |
| A6 (`…72dcdbd3`) | 4,625 | 24.57 % | 2,176 | **+0.000** (−0.010 to +0.010) | Same; a 600 m across-strike halo is beyond survey positional error, so genuine adjacent truth starts to be deleted. | Paired same-week Δ ≥ +0.010 would falsify the predicted flattening and support a still wider collar. |

Prediction decomposition (why the numbers are small and nearly flat): positive collar term scales with removed
dots (+0.004…+0.008), negative refill term scales with refills (−0.001…−0.005). The refill is the weak link:
98.7–99.5 % of refill dots land within 3 px of a retained dot (median 1.00 px), i.e. they mostly add the
0.2·(S−M) penalty and very little fresh kernel credit, and the replacement is non-local (median 845–888 px from
the dot it replaces). This dilution is inherited from the parent lineage's refill policy and is **not** part of
the collar geometry under test — see `IRREGULARITIES.md` IR90-12. Removed dots sit at median 2.8–3.2 px across
strike and 0.5 px along strike, so the edit is a genuine flank edit.

Report-only diagnostics: leakage canary max symmetric AUC 0.5695 over 19 supplied bands (60,988 catalogue
positives + 250,000 seeded off-catalogue pixels) — no single feature above 0.90. Catalogue hide-and-recover and
SGMC control were not run; no fold-clean instrument is calibrated for a collar geometry, and none of these
numbers rank a file.

---

## Session 2026-10-23 (1): AXIS = PRUNE, isotropic collar rungs 3.5 / 4.5 / 5.5 px

---


One card per built variant, written for a structural geologist. Every prediction is **MODEL**, not a
score. Parent for both sessions: R0 `h33-h33-2-b2` (37,654 unit-mass dots, claimed live 0.2778 =
**CLAIM**, no receipt in `ledger/`). The agent has never submitted a file.

---

## Session 2026-10-23b — AXIS = MASS (shadow-drop ladder)

**Shared mechanism.** The brief's algebra is `DTI = T / (0.2T + 0.2(S − M) + 0.8|G|)`, where `T` is
kernel credit, `S` the emitted mass, `M = Σ p·max_g k` and `|G|` the truth pixel count. Because `T`
is a *max* over dots inside the 300 m kernel, a dot whose disk is already covered by closer
neighbours still pays its full `0.2` share of `S − M` while supplying almost no new `T`. Deleting
such a dot strictly lowers the denominator; the only risk is the credit it uniquely supplied.

That risk is measured exactly, without truth, as **exclusive credit** `E_j`: the credit dot `j`
supplies at pixels where every other kept dot supplies less (`src/mass.py`, exact under A1/A2 for the
triangular 300 m kernel). Three doses delete 10 / 20 / 30 % of R0 in ascending `E_j`, recomputed after
each deletion. The doses are nested, so each larger file is a strict superset of the previous
deletion set. **No additions, no moves, no collar change** — a pure mass edit.

At the same 3,765 removals the parent's *stored* FIFO-BFS thinning order destroys 53 % more
exclusive credit than this order does, so the existing `MASS -10 %` style candidates are a different
and mechanically worse experiment (`evidence/mass_build_receipt.json`).

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| `MASSshadow10pct` → 33,889 dots | Deletes the 3,765 dots with least exclusive credit (mean E 4.44 of an isolated dot's 9.42); keeps 93.5 % of R0's total exclusive credit. | Exclusive credit is truth-free: a low-E dot can still be the only dot over a truth pixel in its exclusive lens; contacts, drainage margins and topographic lineaments inside the H19-5 support look identical. | **+0.005** (first-order bracket +0.001 to +0.025; ladder-slope estimate +0.004) | Same-week paired receipt vs R0 with Δ ≤ −0.005. \|Δ\| < 0.010 is no evidence under the session rule. |
| `MASSshadow20pct` → 30,123 dots | Deletes 7,531 dots (mean E 5.00); keeps 85.3 % of exclusive credit. Tests whether the mass term still dominates the credit loss at twice the dose. | As above; the second dose starts reaching dots on sparser strands, where exclusive credit is higher because neighbours are farther. | **+0.009** (+0.001 to +0.048; ladder +0.008) | A Δ at least as good as dose 1 but not better (i.e. flat) means the mass term is already saturating; a decline means credit loss dominates. |
| `MASSshadow30pct` → 26,358 dots | Deletes 11,296 dots (mean E 5.59); keeps 75.3 % of exclusive credit. Deliberately past the likely turnover to locate it in one week. | As above, plus: at 30 % the file starts to look like a different sampling design (sparser), so a drop could reflect lost trace continuity rather than mass. | **+0.012** (0.000 to +0.071; ladder +0.012) | Δ ≤ 0 while dose 2 was ≥ +0.010 locates the turnover between 20 and 30 %; Δ ≤ −0.005 at any dose ends this direction. |

The predictions are bracketed, not fitted: `c` (the deleted dots' own credit to truth) and `|G|` are
unobservable without labels, so the brackets span `c ∈ [0.15, 0.45]` and `|G| ∈ [20k, 100k]`. The
adopted number for each dose is the ladder-slope estimate — the claimed chain 121k px → 37.6k dots
bought +0.0856 for 83,477 dots removed (+0.00102/dot) → +0.0038 / +0.0077 / +0.0116 — plus 0.001,
because per-dot credit loss is smaller here than in uniform coarsening.

**Collar note.** Brief §4 asks for ≥ 3 px from the catalogue. R0's own minimum is 2.236 px (1,611
dots, IR90-01). These variants inherit that collar unchanged, because moving it would be a second
axis, and they add no mass at all (see IRREGULARITIES IR90-07).

---

## Session 2026-10-23a — AXIS = PRUNE (previous, unchanged)

Parent R0 rebuilt byte-identically from the pinned h27-4 solo-d2.8 parent
(`evidence/r0_rebuild_receipt.json`). Shared hypothesis: the >2 px catalogue collar may be too
narrow. Known pixels are masked pixel-exactly, yet new-fault truth may lie adjacent to known traces,
so a broader collar can remove true new-fault credit as well as false-positive mass. Each variant
removes parent dots at or inside a larger Euclidean-distance threshold and refills to exactly 37,654
from the H19-5 support outside the threshold. Refill priority is the rebuilt FIFO-BFS visitation
order — an algorithmic tie-break, **not** a geological probability.

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| PRUNE 3.5 px | Extending the collar just beyond the 300 m kernel radius removes redundant near-catalogue mass while retaining most of the incumbent's high-priority ridge set. 2,702 removed/refilled. | New mapped splays, parallel strands or geometry extensions within 350 m of known traces; refill lineaments may be contacts or drainage margins. | +0.002 (−0.010 to +0.010) | Paired Δ ≤ −0.010. |
| PRUNE 4.5 px | A wider uncertainty halo further cuts false-positive mass but sacrifices more near-catalogue truth. 4,848 removed/refilled. | As above, plus broadened collar more likely to delete newly mapped faults. | +0.000 (−0.010 to +0.010) | Paired Δ ≤ −0.010. |
| PRUNE 5.5 px | A 550 m halo is likely beyond useful positional uncertainty, so lost adjacent new-fault credit may exceed any false-positive saving. 6,130 removed/refilled. | Possibly real displacement of mapped geometry from its true trace. | −0.003 (−0.010 to +0.010) | Paired Δ ≥ +0.010. |

Full inputs, hashes, parent diffs and format receipts: `evidence/build_receipt.json`.

---

## Session 2026-10-23c — AXIS = MASS (high dose + credit-blind control)

**Shared mechanism.** `DTI = T / (0.2T + 0.2(S − M) + 0.8|G|)`. The mass term is paid per dot; `T` is a
*max* over dots inside the 300 m kernel. A dot whose disk is covered by closer neighbours pays its full
`0.2` share and supplies almost no `T`, so deleting it lowers the denominator. Exclusive credit `E_j`
(exact, truth-free, `src/mass.py`) is the cheapest available ordering. These arms continue the
10/20/30 % ladder to 40 % and 48 %, and add the control the ladder never had: the same 40 % dose with a
seeded uniform random subset, which is blind to credit but keeps R0's spatial distribution in expectation.

**Two dose/ordering choices were probed and rejected before submission**, and both probes are recorded in
the receipt. (1) The parent's *stored* 8-connected FIFO-BFS order — the ordering the sibling `MASS ±10 %`
doses use — deletes one south-east corner: at 10 % of R0 it already empties 162 contiguous 5 km blocks,
at 40 % it empties 632 (41 % of all blocks holding ≥ 20 dots). That is a region-isolated file under Hard
Constraint #5 and confounds dose with geography. (2) A 50 % shadow drop is the deepest dose, and there the
greedy starts emptying whole contiguous regions too (largest emptied cluster 17 blocks = 425 km²). The
deep arm therefore stops at **48 %**, the largest shadow dose whose every candidate passes the
region-evenness gate.

**Structural finding that competes with the predicted sign.** At 5 px linking R0 carries 838 strands of
≥ 10 dots (≥ 1 km). `shadow40` keeps **none** of them and pushes mean dot spacing from 3.74 px to
6.19 px, so every surviving dot is farther than the kernel radius from its nearest neighbour. `rand40`
keeps 136 of those strands at 4.70 px spacing. The exclusive-credit greedy preferentially deletes densely
sampled stretches — the parts of a trace that are best observed — and keeps isolated singletons. If new
faults are line-like, that can cost more `T` than the mass saving is worth.

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| `MASSshadow40pct` → 22,592 dots | Deletes 15,062 dots (mean E 6.15 of an isolated dot's 9.42), 36.2 % of R0's total exclusive credit, in ascending-E order recomputed after each deletion. | Low-E dots can still be the only dot over a genuine new strand shadowed by a mapped one; contacts, drainage margins and topographic lineaments behave identically. Deletes 401 of R0's 1,611 sub-3 px collar dots as a side effect. | **+0.014** (bracket +0.004 to +0.025); competing prediction: could fall *below* `rand40` because it destroys all 838 long strands | Paired Δ ≤ −0.005 vs R0 ends the direction. `rand40` within 0.005 of this file ⇒ ranking adds nothing. \|Δ\| < 0.010 = no evidence. |
| `MASSshadow48pct` → 19,580 dots | Deletes 18,074 dots (mean E 6.61), 46.7 % of total exclusive credit. The deepest dose that keeps the file spatially even; locates the turnover. | As above, plus: at 48 % the file is a different sampling design (0.38 % of the footprint), so a drop may reflect lost trace continuity rather than mass. | **+0.015** (+0.002 to +0.030) | Δ ≤ 0 while 40 % was ≥ +0.010 puts the optimum between 30 % and 48 %. Δ ≤ −0.005 at any dose ends this direction. |
| `MASSrandom40pct` → 22,592 dots | Credit-blind control: 15,062 dots drawn uniformly at random, seed 20261023. At matched count it destroys 10.6 % more exclusive credit than `shadow40` (E 102,441 vs 92,598 of 255,848 total) but keeps 136 long strands. | Random deletion has no geological content at all; its score measures what *any* 40 % thinning does, which is exactly what makes it the control. | **+0.013** (+0.004 to +0.023) | If it beats `shadow40` by ≥ 0.005 the exclusive-credit ranking is wrong and must be abandoned; within 0.005 of it, ranking adds nothing and only dose matters. |

**Collar note.** Brief §4 asks for ≥ 3 px from the catalogue; R0's own minimum is 2.236 px (1,611 dots,
IR90-01). These arms only delete, so no new near-catalogue mass is created, but the inherited collar is
unchanged. Moving it is a second axis and was not done here.

**Reproduce.** `scripts/build_mass_high_dose.py --build` then `--verify`; receipt
`evidence/mass_high_dose_receipt.json`; ledger rows in `ledger/submissions.csv` (`status=BUILT`,
`receipt=N`, `receipt_score` empty — the agent never submits).

---

## Report-only instruments

Neither session used a PROXY to rank or gate a candidate. The catalogue hide-and-recover holdout
correlated −0.87 to +0.54 with live scores (n = 12–14 files) in the ledger, so it cannot adjudicate a
±0.01 question. The leakage canary is not applicable to the MASS ladder: its ranking uses no feature
band and no label — only the parent's own dot coordinates.

# Mechanism cards — AXIS=MASS, FIFO-ranked dose rungs (2026-10-23d) — WITHDRAWN before submission

**Status: all three candidates withdrawn (IR90-20).** They were built from exact R0 on the parent's own recorded ranking (H19-5 8-connected FIFO-BFS traversal, pixel-exact reproduction in `evidence/r0_rebuild_receipt.json`) and passed every §6 gate (format, zero catalogue mass, fresh hashes, parent-diff, re-read + byte re-emit). Post-merge they were measured against the region-evenness gate (Hard Constraint #5) and failed: the global FIFO rank is geographic, so a rank-tail drop deletes one SE corner and rank-head adds land in northern strips. The cards remain as the record of the hypothesis that was tested and the diagnostics that falsified it *before* any slot was spent. Predictions below are **MODEL** records, not promotions; the rasters live in `.cache/region_probes/`, not `releases/`.

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL, record) | Outcome |
|---|---|---|---|---|
| MASS drop5pct-tail (`ce48329b`, n=35,771) | Traversal-tail dots (visit ranks 114,510–121,128) still carry unique kernel credit on short late-visited strands, so removing 1,883 of them lowers DTI slightly. Dropping saves 0.2(S−M) per dot but deletes max-kernel credit where the dot was the best coverer. | FIFO-BFS order is a raster convention, not geological confidence; tail dots are late components and far ends, where drainage divides and lithologic contacts mimic fault strands. Report-only PROXYs leaned negative (catalogue Δ−0.0003; SGMC Δ−0.008). | −0.002 (−0.010…+0.003) | **WITHDRAWN:** region-isolated deletion — 3.89 % of 20+-dot blocks ≥90 % emptied, p05 block share 0.0, largest contiguous hole 81 blocks (2,025 km²); fails the gate on all three clauses. |
| MASS add5pct-next (`46f0886b`, n=39,537) | The next-ranked cells suppressed by the parent's 2.8 px thinning are kernel-redundant (99.5 % sit <2.8 px from an existing dot, median 1.0 px), so their max-operator credit is largely pre-claimed while each grows S. | Dense ridge corridors populate suppressed cells; damage-zone width is the opposing confounder (real strand pairs inside the 300 m kernel). PROXYs ≈0, split signs. | −0.002 (−0.009…+0.005) | **WITHDRAWN:** patterned file — all 1,883 added cells lie in grid rows y≤101 (northern strip). |
| MASS add20pct-next (`63954e89`, n=45,185) | Same redundancy mechanism at 4× dose; the second tranche is strictly worse-ranked, so the penalty grows faster than any coverage gain. | Same as add5; at 45,185 dots the file also exits the ledger's 37–44k band. | −0.008 (−0.020…+0.004) | **WITHDRAWN:** patterned file — all 7,531 cells lie in rows y≤288. |

What survives for the entity: the measurement that **any** global-FIFO dose edit is geographic (this also indicts the sibling `MASS ±10%`/`plus10pct` FIFO-family candidates as submission hazards), the catalogue hide-and-recover and SGMC control PROXY tables in `evidence/mass_dose_ladder_receipt.json` (n = 60,988 / 79,615 withheld positives, 64-px paired tile bootstrap, seed 20261023 — REPORT ONLY, never scores), and the proposed region-even add rung in `SLOT_PLAN.md`.
---

## Session 2026-10-23d: `AXIS=RELIEF` (2026-10-23, `evidence/relief_build_receipt.json`)

**Shared geological & metric design (written for a structural geologist):**
- **Landform relief index:** Equal-area terciles over the 5,167,373-pixel footprint (`~1,722,458` px each) from `det_elev` (Band 12, 0.85 percentile weight) and 3.0 km Gaussian-smoothed `det_elev_slope` (Band 19, 0.15 percentile weight). Smoothing `det_elev_slope` at landform scale (`sigma = 30 px = 3 km`) prevents 100 m intrabasin fault scarps on flat valley floors from being misclassified out of the Basin tercile.
- **Physiographic baseline:** R0 allocates **17.25% Basin (T1) / 44.81% Piedmont (T2) / 37.95% Range-front & Range (T3)**, compared with **28.23% / 42.58% / 29.19%** on the known USGS/INGENIOUS Quaternary/geothermal fault catalogue and **9.33% / 24.94% / 65.73%** on off-catalogue USGS SGMC bedrock geologic-map faults.
- **Within-tercile operator:** Count is fixed at **37,654 unit-mass dots**, and 100% of dots remain on the off-catalogue `H19-5` corroborated ridge network (`h19_5 & footprint & ~catalogue`). Donor dots are removed greedily in ascending order of exclusive `R = 3 px` triangular-kernel loss on `H19-5`, and recipient dots (`d_cat >= 3.0 px` strictly) are added greedily in descending order of incremental `R = 3 px` kernel gain—matching exact DTI marginal ordering (`src/dti.py`) for unit-mass on-support dots while eliminating row-scan North–South bias (`north_half_share` stays `0.722–0.740` vs R0's `0.733`).

### 1. `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f` (Shift 12.5% = 4,707 dots: Range-front T3 → Piedmont T2)
- **Hypothesis:** Shifting 12.5% of R0 mass out of uplifted horst/range interiors (`T3`: `37.95% -> 25.44%`) into piedmont/bajada aprons (`T2`: `44.81% -> 57.31%`) trims false-positive bedrock erosional ridges while densifying coverage across range-bounding synthetic splays, relay ramps, and accommodation step-overs without gambling mass on deep playa fill.
- **Mechanism:** Removes the 4,707 lowest-exclusive-credit `T3` dots and adds the 4,707 highest-marginal-credit `T2` `H19-5` pixels (`d_cat >= 3.0 px`; `25.001%` symmetric diff). Because GeoDAWN Area 2 was flown at 400 m line spacing (`~150–300 m` lateral lineament uncertainty: https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7), tighter `H19-5` sampling in `T2` increases lateral kernel reach across piedmont fault corridors.
- **Non-fault process that could mimic it:** Incised alluvial-fan feeder channels, terrace risers, Pleistocene Lake Lahontan highstand beach ridges, and linear piedmont infrastructure (roads/pipelines) can generate corroborated `H19-5` lineaments in `T2`.
- **Predicted live change (`MODEL`):** **+0.004 DTI** (plausible interval `-0.010` to `+0.015`; not a score).
- **Falsifier:** A paired live receipt against R0 with `Δ <= -0.010` DTI rejects down-relief piedmont enrichment at fixed count and triggers switching to the up-relief counterpoint (`p2r15pct`). `|Δ| < 0.010` is no evidence.

### 2. `h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17` (Shift 10.0% = 3,766 dots: Range-front T3 → Basin T1)
- **Hypothesis:** Shifting 10.0% of R0 mass from `T3` (`37.95% -> 27.94%`) into `T1` (`17.25% -> 27.25%`) removes `H19-5`'s bedrock-topography bias and aligns R0's physiographic allocation (`27.3% / 44.8% / 27.9%`) within 1 percentage point of the Great Basin USGS/INGENIOUS Quaternary fault prior (`28.2% / 42.6% / 29.2%`).
- **Mechanism:** Concealed intrabasin normal faults and blind geothermal step-overs beneath Plio-Quaternary valley fill lack steep surface scarps and rely on aeromagnetic/gravity gradients. Reallocating 3,766 unit dots (`20.003%` symmetric diff) from crowded/short `T3` bedrock segments to uncovered `T1` `H19-5` kernel gaps (`d_cat >= 3.0 px`) raises kernel credit on buried axial-graben faults at fixed total mass.
- **Non-fault process that could mimic it:** Pluvial shoreline berms (Lake Lahontan), axial river/playa margins, shallow intrabasin basaltic sills/flows, and valley-axis rail/powerline magnetic artifacts mimic concealed intrabasin faults in `T1`.
- **Predicted live change (`MODEL`):** **+0.003 DTI** (plausible interval `-0.012` to `+0.015`; not a score).
- **Falsifier:** Paired live `Δ <= -0.010` DTI vs R0 falsifies concealed-basin enrichment. `|Δ| < 0.010` is no evidence.

### 3. `h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f` (Shift 15.0% = 5,648 dots: Piedmont T2 → Range-front T3)
- **Hypothesis:** Bidirectional structural counterpoint: if undisclosed organizer "new fault" labels (https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527) derive mainly from newly compiled bedrock quadrangles and steep range-front scarps (like off-catalogue SGMC, which sits 65.7% in `T3`), shifting 15.0% of R0 mass up-relief (`T2`: `44.81% -> 29.81%`; `T3`: `37.95% -> 52.95%`) will raise live DTI; under our primary concealed-Quaternary GeoDAWN hypothesis, it is predicted slightly negative (`-0.004 MODEL`).
- **Mechanism:** Greedily moves 5,648 unit dots (`29.999%` symmetric diff) from `T2` to `T3` on `H19-5` (`d_cat >= 3.0 px` on all additions), holding total count at 37,654.
- **Non-fault process that could mimic it:** Unfaulted volcanic/intrusive contacts, dikes, cooling joints, resistant stratigraphic hogbacks, and steep erosional drainage divides in uplifted horsts mimic bedrock fault lineaments in `T3`.
- **Predicted live change (`MODEL`):** **-0.004 DTI** (plausible interval `-0.015` to `+0.012`; not a score).
- **Falsifier:** Uploaded only if down-relief (`r2p12p5pct` or `r2b10pct`) yields `Δ <= -0.010`; if `p2r15pct` also yields `Δ <= -0.010`, monotonic relief reallocation is falsified in both directions.

