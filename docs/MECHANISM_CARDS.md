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


---

## Session 2026-10-23f — AXIS = MASS, direction = ADD (region-even block budget, placement contrast)

**Shared hypothesis (structural geologist's version).** R0's field was thinned to 37,654 unit-mass dots at the
lineage's own 2.8 px spacing and then collared at 2 px from mapped traces. If that thinning went past the mass
optimum, then *adding* unit dots back onto the same corroborated ridge network — following the parent's own regional
mix, never inside the 3 px collar — should recover new-fault credit that is worth more than the 0.2 each dot costs in
the denominator. The opposite is equally tellable: if the ridge network is saturated, the added dots earn almost
nothing and the file loses by exactly the mass penalty.

**Mechanism (why the sign is knowable at all).** With `DTI = T/(0.2T + 0.2(S−M) + 0.8|G|)`, one added dot moves the
score by `dDTI = [E(D − 0.2T) − 0.2T(1 − c)]/D²`: it pays iff its exclusive truth credit `E` exceeds ≈ 0.056 at the
claimed 0.2778. `T` is a **max** over dots, so an addition can never remove credit — the failure mode is bounded by
the mass penalty alone. That asymmetry is the reason an ADD rung is worth a slot: every deletion rung risks a
credit loss as well as a mass saving.

**Placement (the only things that differ between the two live files).** Eligibility: H19-5 support, in footprint, not
catalogue, Euclidean `d_cat ≥ 3.0 px`, unoccupied. Quota per 5 km block is proportional to that block's own R0 count,
capped at +50 %, zero where R0 has no dots. `blocknext` takes the parent's own FIFO-ranked suppressed cells inside
each quota; `gapmax` takes the cells with the largest remaining `R = 3 px` kernel credit (global coverage updated after
every pick, so neighbouring blocks see each other). Nothing else changes: 0 dots removed, no moves, no collar edit.

| Variant | Dots | Change | Mean marginal support credit / dot | Predicted (MODEL) | Non-fault confounder | Falsifier |
|---|---|---|---|---|---|---|
| ~~`…add10pctGapmax-…98408334`~~ **WITHDRAWN** | 41,419 | +3,765 (10.0 %) | 1.013 | *withdrawn (IR90-24)*: same eligible pool, ranking and quotas as the merged `MASSadd10pctq50`, so it is one experiment expressed twice. | — | — |
| `…add10pctBlocknext-…89d16c16` | 41,419 | +3,765 (10.0 %) | 0.486 | **+0.0044** (+0.0003 … +0.0107) | Same, plus: the FIFO-ranked suppressed cells sit 1–2.8 px from existing dots, so most of their kernel is already covered — this arm tests the brief's literal recipe, not the best placement. | `Δ ≤ −0.010` while gapmax is positive would mean the "next-ranked" recipe is actively harmful and should be dropped from the brief's defaults. |
| `…add20pctBlocknext-…260d987e` | 45,185 | +7,531 (20.0 %) | 0.464 | **+0.0084** (+0.0005 … +0.0205) | Same; the deeper dose also pushes into the second ring around each existing dot, where kernel room is thinner. | A null here while the 10 % arm is ≥ +0.010 would mean the add gradient saturates before +20 %. |

**Prediction decomposition.** The point prediction uses support precision 0.20 (the value implied by
`T ≈ 16.6 k` over 121,131 support px at `mean k ≈ 0.7`) and the point parent fit `(G, M/S) = (65,000, 0.44)`. The
bracket is the min/max over `G ∈ {60,988, 65,000, 90,000} × M/S ∈ {0.20, 0.44, 0.60} × precision ∈ {0.10, 0.20, 0.35}`;
it spans zero for both blocknext arms and stays positive for gapmax. The whole spread is worth ~±0.010 — the same
size as the session's no-evidence band, which is stated openly rather than hidden.

**Region-evenness evidence (Hard Constraint #5).** 5 km blocks: p05 / median / p95 addition share 0.087 / 0.100 / 0.115
at the 10 % dose, max 0.12; 0 of 848 blocks holding ≥ 20 R0 dots receive nothing; 1,499 blocks receive additions;
added centroid within 30 px of the parent's. All six files: format gate PASS, zero catalogue mass, min added
`d_cat = 3.0 px` exactly, 0 added dots below 3 px, inherited R0 collar unchanged (IR90-18).

**Report-only.** SGMC off-catalogue fault coverage rises +39.2 / +73.1 / +53.0 credit units (R0 baseline in
`evidence/mass_add_receipt.json`) — consistent with the additions landing on independently mapped structure, but SGMC
over-represents exposed bedrock and standalone SGMC scored 0.0512 CLAIM. Catalogue hide-and-recover is analytically
zero for this axis (every addition is ≥ 3 px away from every catalogue pixel with a 3 px kernel): a blind spot, not a
pass. No PROXY ranks these files.

---

## Session 2026-10-23 (continuity): `AXIS=MASS`, value family = continuity-aware shadow drop (`evidence/mass_continuity_receipt.json`)

**Shared design (written for a structural geologist):** Identical ranking, doses and parent as the recorded shadow ladder — ascending exclusive 300 m kernel credit, deletion-only strict subsets of R0 at exactly 7,531 / 11,296 / 15,062 removals — plus one eligibility rule. In the graph linking R0 dots ≤ 6 px apart (kernel diameter: linked dots' 300 m disks touch or overlap), the 857 components with ≥ 10 dots are treated as ≥ 1 km strands. A strand dot may not be removed while it is an articulation point of its strand (removal would split the trace) nor once its strand is down to 10 dots. Every strand therefore survives as one kernel-continuous trace, where unconstrained shadow-40 keeps 0/857 strands whole at 6 px (0/838 at the legacy 5 px instrument) and random-40 keeps 136 at 5 px. The measured price is small: +2.7% / +5.8% / +7.4% exclusive credit destroyed vs shadow at matched count, and shadowcont-40 (E = 99,483) still destroys less credit than the credit-blind random-40 control (E = 102,441). Right instrument, honest limit: at 5 px linking the 40% arm still reads only 70 strands ≥ 10 dots, because protection permits 5–6 px along-strand gaps that preserve kernel coverage but break the tighter 5 px chain. Axis choice: fresh sibling audit (IR90-26; convergent in-repo measurement IR90-25) found all seven axes built with zero receipts and every brief-literal CONCENTRATION-up arm ≤ 0 on GEMSDOE86's SGMC MODEL; this is the unbuilt `CONTINUITY_AWARE_DOSE` rung this repo's `SLOT_PLAN.md` proposed.

### 1. `h33-h33-2-b2-MASSshadowcont20pct-20261023-66d961ba` (drop 20% = 7,531 dots → 30,123; 20.0005% changed)
- **Hypothesis:** At the ladder's 20% dose, strand protection is nearly free (+2.7% credit) and keeps every ≥ 1 km trace kernel-continuous (6 px survival 857/857 vs 234/857 unconstrained; 5 px strands ≥10: 196 vs R0's 838, mean NN 4.49 px), so live DTI should match the shadow arm's mass saving without its structural cost.
- **Mechanism:** DTI charges 0.2 per dot but credits T once per truth pixel; R0 samples strands every ~2.8–3 px where ~5–6 px sampling still covers line-like truth (the per-dot bar falls for lines, brief §2). Protection thins strand interiors toward that spacing instead of letting the greedy sever strands at their most shadowed — densest — stretches.
- **Non-fault process that could mimic it:** ≥ 1 km unfaulted corridors — dikes, hogbacks, drainage divides, Lake Lahontan shoreline berms — are protected with the same force as faults; deleted short fragments may be genuine < 1 km relay tips and step-over splays.
- **Predicted live change (`MODEL`):** **+0.009 DTI** (point +0.0088; formula bracket +0.001 to +0.048; not a score). The credit model alone ranks it a hair below shadow-20 (+0.009); the continuity term is the unquantified upside.
- **Falsifier:** Paired receipts, |Δ| < 0.010 = no evidence: Δ vs R0 ≤ −0.010 falsifies the dose direction; shadowcont−shadow ≤ −0.010 at matched count abandons protection; ≥ +0.010 adopts it as the ladder ranking.

### 2. `h33-h33-2-b2-MASSshadowcont30pct-20261023-885f6fee` (drop 30% = 11,296 dots → 26,358; 29.9995% changed)
- **Hypothesis:** The protected dose-response keeps rising to 30% (+5.8% credit price; 6 px survival 857/857 vs 26/857 unconstrained; 5 px strands ≥10: 105, mean NN 5.16 px).
- **Mechanism:** As above; at this dose the unconstrained greedy has already fragmented 97% of strands at 6 px, so the pair isolates continuity at mid-dose.
- **Non-fault process that could mimic it:** As above, stronger: strand interiors approach the 10-dot floor on short strands, so protection increasingly preserves whatever geometry R0 happened to draw, fault or not.
- **Predicted live change (`MODEL`):** **+0.011 DTI** (point +0.0113; bracket −0.001 to +0.071; not a score), vs shadow-30's recorded +0.012.
- **Falsifier:** As above, read against shadow-30 and R0 at matched count.

### 3. `h33-h33-2-b2-MASSshadowcont40pct-20261023-92be4121` (drop 40% = 15,062 dots → 22,592; 40.0011% changed)
- **Hypothesis:** At the dose where the strand-destruction finding was measured, protection is the difference between a point cloud (shadow-40: 0 strands whole, mean NN 6.19 px, 100% of dots beyond kernel reach of a neighbour) and a thinned trace set (857/857 whole at 6 px, 70 at 5 px, mean NN 5.67 px) at only +7.4% credit — still less credit destroyed than random-40, which keeps just 136 five-px strands.
- **Mechanism:** As above; this is the three-way corner (shadow = min credit / no continuity; random = mid credit / accidental continuity; shadowcont = near-min credit / full continuity) that lets one week of receipts order credit vs continuity vs dose.
- **Non-fault process that could mimic it:** As above; additionally, if test truth is effectively point-like at 100 m sampling (isolated pixels rather than lines), continuity buys nothing and the +7.4% credit penalty is pure loss.
- **Predicted live change (`MODEL`):** **+0.013 DTI** (point +0.0130; bracket −0.003 to +0.092; not a score), vs shadow-40 +0.014 / random-40 +0.013 recorded.
- **Falsifier:** As above, plus: if random-40 beats both ranked arms by ≥ 0.010, every exclusive-credit ranking in this repo is wrong, not just this one.

Report-only `PROXY`s for this session (never gates, never used to rank; `evidence/mass_continuity_receipt.json`): catalogue hide-and-recover (38 withheld 20×20 km blocks, n = 13,920 positives, R0 0.0072) Δ = −0.0005 / −0.0010 / −0.0017 with 95% CIs excluding 0, and off-catalogue SGMC (n = 62,122, R0 0.0954) Δ = −0.0111 / −0.0193 / −0.0276 — both dose-monotone negative exactly as expected mechanically for deletion-only subsets scored against fixed positive sets (fewer dots near positives; R0 was pruned against the full catalogue). Leakage canary: not applicable (no feature band read; cf. RELIEF session's 19-band max symmetric AUC 0.5700 on identical inputs).
## Session 2026-10-23 (final): AXIS = PRUNE, A5 along-strike ladder, fixed-count refill

Parent R0 is exact (`c55bafc4…` zeros / `baeae321…` NaN). The catalogue mask is pixel-exact and nearby new-fault pixels remain scoreable (organizer clarification: https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516); newly mapped geometry of existing systems is also target geometry (https://community.drivendata.org/t/where-do-you-draw-the-line/11536). GeoDAWN Area 2's 400 m line spacing motivates a positional-uncertainty test, not a claim that every gradient is a fault (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7).

All three files hold **37,654 dots**, refill from H19-5 with the recovered FIFO-BFS order, preserve R0's `d_cat>2 px` baseline, and emit zero catalogue mass. A5 is fixed across strike; only L changes. Predictions were frozen before REPORT ONLY proxies. These are BUILT, unscored experiments; 0.2778 is CLAIM and every delta below is MODEL.

### `h33-h33-2-b2-PRUNEanisoA5L1p5-20261023-9486c7e6`

- **Edit / parent diff:** A=5 px, L=1.5 px; remove 3,130 and refill 3,130; symmetric difference 6,260 px = **16.6251%** of R0. NaN SHA-256 `9486c7e6e3a1e6cea7c483c4d23f5746f43311432b475747ffba86e624272ad1`; zeros `0daafb5bf2dfc4183409cd69717293eaa7bb55ddbbe91fe4cd10d4a0671608d8`.
- **Hypothesis:** The recorded A5/L2 collar prunes too far along mapped strike. Narrowing only the along radius to 1.5 px should preserve genuine unmapped continuations and avoid dilutive refill while retaining the across-strike flank cleanup.
- **Mechanism:** The ellipse removes 3,130 R0 dots where (along/1.5)^2 + (across/5)^2 <= 1 at coherent catalogue traces, then restores exactly 37,654 dots from outside-collar H19-5 support with d_cat>2 px (R0's baseline) in the recovered FIFO-BFS order. Relative to A5/L2, fewer along-strike dots are removed and fewer distant refill dots are needed. Catalogue pixels remain exactly zero mass.
- **Non-fault mimic / confounder:** A mapped-tip continuation can be a real fault, but an apparently continuous magnetic/topographic lineament can also be a lithologic contact, drainage, shoreline, road, or pipeline. Preserving more along-strike dots can therefore retain false mass; the FIFO refill can also prefer unrelated geographic components rather than fault likelihood.
- **Predicted live sign and size:** +0.004 DTI (MODEL; plausible -0.008 to +0.012; not a score) Decomposition: MODEL: across-strike collar gain approximately held from A5/L2; along-strike continuation loss and refill dilution both decrease. 98.3% of this file's refills sit within 3 px of a retained dot, so the remaining refill still offsets part of the collar gain.
- **Falsifier:** A paired live receipt against R0 with delta <= -0.010 falsifies the A5/L1.5 policy; |delta| < 0.010 is no evidence. If A5/L2 outscores the narrower-L files by >=0.010, the hypothesis that L2 over-prunes real continuations is falsified.
- **Structural review:** Inspect retained mapped-tip projections and step-overs, not just across-strike flanks. The collar is a positional-uncertainty experiment, not a geological claim that continuations inside the ellipse are absent.

### `h33-h33-2-b2-PRUNEanisoA5L1-20261023-cd2c60ce`

- **Edit / parent diff:** A=5 px, L=1 px; remove 2,386 and refill 2,386; symmetric difference 4,772 px = **12.6733%** of R0. NaN SHA-256 `cd2c60ce045a914b3421538333a7c5beb3585cf12dbc4aba05d6d42c62fc4cdb`; zeros `fcc218c8e78fc391a863d01041df48754e94e55fe72eaa682e1b782ebb3590dc`.
- **Hypothesis:** The recorded A5/L2 collar prunes too far along mapped strike. Narrowing only the along radius to 1 px should preserve genuine unmapped continuations and avoid dilutive refill while retaining the across-strike flank cleanup.
- **Mechanism:** The ellipse removes 2,386 R0 dots where (along/1)^2 + (across/5)^2 <= 1 at coherent catalogue traces, then restores exactly 37,654 dots from outside-collar H19-5 support with d_cat>2 px (R0's baseline) in the recovered FIFO-BFS order. Relative to A5/L2, fewer along-strike dots are removed and fewer distant refill dots are needed. Catalogue pixels remain exactly zero mass.
- **Non-fault mimic / confounder:** A mapped-tip continuation can be a real fault, but an apparently continuous magnetic/topographic lineament can also be a lithologic contact, drainage, shoreline, road, or pipeline. Preserving more along-strike dots can therefore retain false mass; the FIFO refill can also prefer unrelated geographic components rather than fault likelihood.
- **Predicted live sign and size:** +0.005 DTI (MODEL; plausible -0.008 to +0.014; not a score) Decomposition: MODEL: across-strike collar gain approximately held from A5/L2; along-strike continuation loss and refill dilution both decrease. 98.0% of this file's refills sit within 3 px of a retained dot, so the remaining refill still offsets part of the collar gain.
- **Falsifier:** A paired live receipt against R0 with delta <= -0.010 falsifies the A5/L1 policy; |delta| < 0.010 is no evidence. If A5/L2 outscores the narrower-L files by >=0.010, the hypothesis that L2 over-prunes real continuations is falsified.
- **Structural review:** Inspect retained mapped-tip projections and step-overs, not just across-strike flanks. The collar is a positional-uncertainty experiment, not a geological claim that continuations inside the ellipse are absent.

### `h33-h33-2-b2-PRUNEanisoA5L0p5-20261023-91ff3771`

- **Edit / parent diff:** A=5 px, L=0.5 px; remove 1,333 and refill 1,333; symmetric difference 2,666 px = **7.0803%** of R0. NaN SHA-256 `91ff37719b126c9253b1bae0c6c6eb127710c04910a47ab6dd3b93dd89dffa6b`; zeros `d2741f40650fd849c1250c57d9d20fe5fab8166e39f64d421ab220f8ab9013c6`.
- **Hypothesis:** The recorded A5/L2 collar prunes too far along mapped strike. Narrowing only the along radius to 0.5 px should preserve genuine unmapped continuations and avoid dilutive refill while retaining the across-strike flank cleanup.
- **Mechanism:** The ellipse removes 1,333 R0 dots where (along/0.5)^2 + (across/5)^2 <= 1 at coherent catalogue traces, then restores exactly 37,654 dots from outside-collar H19-5 support with d_cat>2 px (R0's baseline) in the recovered FIFO-BFS order. Relative to A5/L2, fewer along-strike dots are removed and fewer distant refill dots are needed. Catalogue pixels remain exactly zero mass.
- **Non-fault mimic / confounder:** A mapped-tip continuation can be a real fault, but an apparently continuous magnetic/topographic lineament can also be a lithologic contact, drainage, shoreline, road, or pipeline. Preserving more along-strike dots can therefore retain false mass; the FIFO refill can also prefer unrelated geographic components rather than fault likelihood.
- **Predicted live sign and size:** +0.003 DTI (MODEL; plausible -0.010 to +0.012; not a score) Decomposition: MODEL: across-strike collar gain approximately held from A5/L2; along-strike continuation loss and refill dilution both decrease. 97.9% of this file's refills sit within 3 px of a retained dot, so the remaining refill still offsets part of the collar gain.
- **Falsifier:** A paired live receipt against R0 with delta <= -0.010 falsifies the A5/L0.5 policy; |delta| < 0.010 is no evidence. If A5/L2 outscores the narrower-L files by >=0.010, the hypothesis that L2 over-prunes real continuations is falsified.
- **Structural review:** Inspect retained mapped-tip projections and step-overs, not just across-strike flanks. The collar is a positional-uncertainty experiment, not a geological claim that continuations inside the ellipse are absent.

**Report-only diagnostics:** leakage canary max symmetric AUC 0.5695. Catalogue hide-and-recover (38 withheld 20 km blocks; n=13,920 positives) and off-catalogue SGMC (n=62,122) have 95% block-bootstrap CIs in `evidence/aniso_along_refill_receipt.json`. Both are PROXY, never gates or scores; the catalogue control is especially blind to collar edits because known pixels are live-masked.

**Compliance stop:** SNAP was withdrawn before raster emission when 30 inherited dots proved to have no >=3 px destination within 2 px (IR90-28). Three delete-only PRUNE probes were then withdrawn before submission because the brief requires fixed-count refill (IR90-29); they are not alternatives to the cards above.

## Session 2026-10-23e: `AXIS=CONCENTRATION` — HELD after merge — 15 km structural-edge / strain prior

Parent R0 has 15 km block-density CV `0.5103`, inside the brief's reported `0.51–0.59` band. The prior is the mean of equal in-footprint absolute-percentile ranks of pinned `tmi_hg`, `geod_2ndinv`, `geod_shearrate` and `iso_grav_anom_hg` per 150 px block; no wells, springs, vents or hidden/public truth are used. Dots are removed from the lowest-prior 35% of blocks by minimum exclusive `R=3 px` kernel credit and added in the highest-prior 35% by maximum marginal credit on H19-5. Count is fixed at 37,654; all additions clear `d_cat >= 3 px`; untouched parent dots retain the 2.236 px floor (IR90-31).

### 1. `h33-h33-2-b2-CONCENTRATIONb15kmstruct10pct-20261023-8deb8269`
- **Hypothesis:** moving 3,765 dots (10%) toward active-deformation / potential-field edge corridors improves hit rate before over-concentration dominates.
- **Mechanism:** CV 0.5103→0.5990; symmetric parent diff 19.998%; lost/gained H19-5 support credit 4,009.4 / 3,036.1. No donor block loses ≥90%; p05 donor removal share 0.194.
- **Non-fault mimic:** geodetic strain can follow subsidence/volcanic inflation; potential-field edges can mark dikes, contacts, shorelines or cultural infrastructure.
- **Predicted live change:** **+0.002 DTI `MODEL`** (plausible -0.008..+0.012).
- **Falsifier:** paired live Δ≤-0.010 rejects the 10% structural-prior move; |Δ|<0.010 is no evidence.

### 2. `h33-h33-2-b2-CONCENTRATIONb15kmstruct15pct-20261023-fdba3c0a`
- **Hypothesis:** if the prior is predictive, 15% should beat 10%; if the CV band is causal, redundancy should cancel it.
- **Mechanism:** 5,648 dots moved; CV 0.5103→0.6949; symmetric diff 29.999%; support credit 6,851.9 lost / 3,923.8 gained; max donor removal 70.8%.
- **Non-fault mimic:** same as above, amplified by denser mapping and exposed bedrock in high-prior blocks.
- **Predicted live change:** **-0.002 DTI `MODEL`** (plausible -0.013..+0.009).
- **Falsifier:** Δ≤-0.010 rejects the middle dose; a positive 10% arm plus negative 15% arm localizes the optimum near the CV band.

### 3. `h33-h33-2-b2-CONCENTRATIONb15kmstruct20pct-20261023-bc411adb`
- **Hypothesis / counterpoint:** 20% is the strong-dose test; overshooting the reported CV band should hurt if concentration is causal.
- **Mechanism:** 7,531 dots moved; CV 0.5103→0.7769; symmetric diff 40.001%; support credit 10,320.1 lost / 4,811.5 gained; max donor removal 80.0%.
- **Non-fault mimic:** high-prior corridors may be unfaulted lithologic/cultural edges, while removed low-prior ground may contain blind basin faults.
- **Predicted live change:** **-0.006 DTI `MODEL`** (plausible -0.018..+0.006).
- **Falsifier:** Δ≥+0.010 would falsify the CV-band penalty and support strong prior concentration; Δ≤-0.010 confirms the predicted monotonic cost.

**Report only:** hide/recover PROXY n=13,920, R0 0.007191, Δ +0.000001 / +0.000024 / +0.000011 (95% CIs span zero); SGMC PROXY Δ -0.006381 / -0.009540 / -0.014211; leakage canary max symmetric AUC 0.574747. These are not scores and were not gates. Full receipt: `evidence/concentration_build_receipt.json`.

**Post-merge note:** IR90-25/26 show fixed-count concentration has little credit headroom at R0 and
non-positive sibling MODELs. The 15 km prior is string-distinct and all gates pass, but the files are held
from slots unless a future live receipt changes the evidence state.
