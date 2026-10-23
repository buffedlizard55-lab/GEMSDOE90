# SLOT PLAN — one entity, 3 slots/week (last edit 2026-10-23, session `AXIS=MASS` add direction)

**Incumbent R0:** `h33-h33-2-b2` (37,654 unit-mass dots, rebuilt byte-identically; `0.2778` is **CLAIM** until a portal receipt is logged). `TOP_PUBLIC` (with date) and weekly/total quota used are blank and must be supplied by the human before any upload. Quota is ONE entity at 3 scored submissions/rolling week and ONE blind final submission per official rules (https://docs.nlr.gov/docs/fy26osti/96647.pdf; problem/metric spec: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). Any public-chunk live `|Δ| < 0.010` DTI is **no evidence**.

**Why `AXIS=RELIEF` (session 2026-10-23d).** Equal-area landform relief terciles (`0.85·pct(det_elev) + 0.15·pct(gaussian_3km(det_elev_slope))`) show R0 allocates **17.2% Basin / 44.8% Piedmont / 37.9% Range-front**, whereas the USGS/INGENIOUS catalogue sits at **28.2% / 42.6% / 29.2%** (known pixels masked pixel-exactly; adjacent new faults scored: https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) and off-catalogue USGS SGMC bedrock faults sit at **9.3% / 24.9% / 65.7%**. Undisclosed test sources (https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527) and 400 m GeoDAWN line spacing (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7) make physiographic allocation an orthogonal single-axis lever alongside `MASS` and `PRUNE`, holding count at 37,654 on `H19-5` with `d_cat >= 3.0 px` on 100% of additions.

## Session 2026-10-23e (this branch): `AXIS=MASS`, ADD direction — the first region-even add rung

Built `MASSadd5pctq50` / `MASSadd10pctq50` / `MASSadd20pctq50` from byte-identical R0: +1,883 / +3,765 / +7,531
unit dots chosen by **exact marginal kernel credit** on the H19-5 support, apportioned over **5 km blocks in
proportion to the block's R0 dot count** (largest remainder + water fill), every addition `d_cat >= 3 px`, no
deletion, no move (`evidence/mass_infill_receipt.json`). Why the add side: the delete side is fully instrumented
(10/20/30/40/48 % + random control) while every recorded add rung — this repo's withdrawn `add5pct-next` /
`add20pct-next` and the sibling `plus10pct` family — ranks by the parent's FIFO-BFS order, which IR90-20 measured to
be geographic. Mechanism: R0's thinning enforces 2.8 px spacing against a 3 px kernel, so a strand pixel midway
between two dots can reach only ~0.53 credit; the per-dot ceiling is 1/D for an addition versus 0.2/D for a
deletion. Evenness is preserved: block-density CV 0.726 → 0.728 / 0.726 / 0.730, occupied blocks unchanged at 1,788,
max 4 / 9 / 18 additions in any one block.

**The predictions are MODEL and the raw model is 8-10x larger than the adopted number** (raw +0.07 / +0.13 / +0.22
DTI). The adopted +0.008 / +0.014 / +0.022 applies a documented 0.10 transfer discount, because the first-order
model assumes the truth set is an unbiased sample of the H19-5 support, and it is not: the lineage's own thinning and
collar concentrated coverage where it was most confident, so the residual credit deficit is concentrated where it was
least confident. That discount is a judgement, not a measurement (IR90-23).

## Next 3 slots in order (one entity; upload NaN `.tif` primary only, never both twins)

| Slot | Candidate | Predicted Δ vs R0 (`MODEL`) | Decision rule from live receipt |
|---|---|---|---|
| 1 | `h33-h33-2-b2-MASSadd5pctq50-20261023-c4e6144c.tif` (+1,883d → 39,537) | **+0.008** (-0.004 to +0.030) | Cheapest decisive sign test of the whole mass axis. `Δ >= +0.010`: the truth is line-like and under-sampled — go to Slot 2 and licence a same-week thinned file. `Δ <= -0.010`: mass behaves as pure penalty, the add direction closes, and Slot 3 becomes `MASSshadow40pct`. `|Δ| < 0.010`: no evidence; Slot 2 becomes `MASSshadow40pct` to test the opposite sign. |
| 2 | `h33-h33-2-b2-MASSadd10pctq50-20261023-5edc84de.tif` (+3,765d → 41,419) | **+0.014** (-0.008 to +0.045) | Slope between two add doses. Rising Δ vs Slot 1 ⇒ under-dosed, take `add20pctq50` in Slot 3. Flat or falling ⇒ the mid-strand deficit is exhausted at ~5 %, and Slot 3 should combine the winning direction with the strongest other axis instead. |
| 3 | Conditional: `h33-h33-2-b2-MASSadd20pctq50-20261023-f94efff4.tif` **or** `h33-h33-2-b2-MASSshadow40pct-20261023-e2546fbe.tif` | **+0.022** / **+0.014** | Take `add20pctq50` only if both add receipts were positive; otherwise take `MASSshadow40pct` so the week still returns a sign test on the mass axis at matched dose magnitude, not a second null. |

Retained but not slotted this week: `RELIEFr2p12p5pct` (+0.004), `PRUNEanisoA4L2` (+0.003), `MASSshadow20pct`
(+0.009). They stay valid; the add ladder is ordered first because it is the only arm whose sign is genuinely
unknown and whose ceiling (1/D per dot) is five times the deletion ceiling.

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms on competition page)

- **Weeks 1–2 (Oct 23 – Nov 5, max 6 slots):** Confirm R0 live receipt first if missing; run Slots 1–3 above, then remaining orthogonal single-axis checks (`MASSshadow40pct` vs `MASSrandom40pct`, `PRUNEanisoA4L2` vs `PRUNE3p5px`) without repeating any `(AXIS, value)`.
- **Weeks 3–4 (Nov 6 – Nov 19, max 6 slots):** Combine the two axes whose live receipts cleared `Δ >= +0.010` (e.g., winning `RELIEF` tercile shift × winning `MASS` thinning or `PRUNE` collar) on exact parent code.
- **Weeks 5–6 (Nov 20 – Dec 3, max 6 slots + 1 blind final):** Confirm top composite, select ONE blind final `.tif` (accounting for private chunks + Phase 2 expert-expanded faults: https://community.drivendata.org/t/where-do-you-draw-the-line/11536) and its `-zeros.tif` fallback, and re-run `scripts/restore_releases.py` + `src/validate.py` before upload.

## Report-only diagnostics (`PROXY` / `REPORT ONLY` — never gates, never scores)

- **Leakage canary:** 19 supplied bands + `relief_idx` on 60,988 catalogue positives vs 250,000 seeded (`20261023`) off-catalogue pixels: max symmetric AUC = `0.5700` (`geod_2ndinv`), `relief_idx` = `0.5063` (`< 0.90` pass).
- **Catalogue hide-and-recover & SGMC controls (`PROXY`, `evidence/relief_build_receipt.json`):** 38 withheld 20×20 km catalogue blocks (`n = 13,920`, R0 `0.0072`): `r2b10pct` `Δ = -0.0003`, `r2p12p5pct` `Δ = -0.0004`, `p2r15pct` `Δ = -0.0006` (`>=3 px` additions earn zero catalogue credit). Off-catalogue SGMC (`n = 62,122`, R0 `0.0954`): `p2r15pct` `Δ = -0.0033` > `r2b10pct` `Δ = -0.0091` > `r2p12p5pct` `Δ = -0.0108` (reflecting SGMC's 65.7% bedrock-range bias).

## Session 2026-10-23d result (this branch): FIFO-ranked MASS rungs withdrawn — do not slot

Three dose-ladder rungs on the parent's own recorded ranking (`drop5pct-tail`, `add5pct-next`, `add20pct-next`;
receipt `evidence/mass_dose_ladder_receipt.json`) were built from exact R0 and **withdrawn before submission**
(Hard Constraint #5, IR90-20): the global FIFO-BFS rank is geographic — the 5 % tail drop empties an 81-block
(2,025 km²) SE hole and fails the region-evenness gate on all three clauses, and both add rungs place every cell
in northern grid strips (y≤101 / y≤288). Rows are kept WITHDRAWN as occupancy guards; rasters are out of
`releases/`. The ordered plan above is unchanged and remains the next three slots. Do not submit any
FIFO-ranked dose rung (including the sibling `MASS ±10%`/`plus10pct` files that use the same order) as a dose test.

**Replacement rung proposed for a future session (not built):** `MASSadd10pct-blocknext` — add 10 % mass by the
parent's ranking *budgeted per 5 km block* (each block's next-ranked suppressed cells, quota ∝ its R0 count).
*Mechanism:* tests the add slope at fixed geography, the half of the dose question the shadow ladder cannot see.
*Confounder:* block quotas are an evenness convention, not geology; suppressed cells remain kernel-redundant
(99.5 % sit <2.8 px from a parent dot). *Falsifier:* paired Δ≤−0.010 vs R0, or failure of the region-evenness gate.

## Better axes proposed (all sessions — not built)

- **CONTINUITY_AWARE_DOSE.** Same 40 % dose, but the greedy may not delete a dot whose removal splits a
  ≥ 1 km strand at 5 px linking. *Mechanism:* keeps the mass saving while preserving the line-like coverage
  `T` is paid for. *Confounder:* 5 px linking is a geometric choice, not evidence the strand is a fault, so
  it can preserve false mass. *Falsifier:* paired Δ ≤ −0.010 against `shadow40`.
- **KERNEL_ORACLE_DOSE.** Re-space survivors to a ~6 px anti-cluster (just outside the kernel, where
  exclusive credit equals the isolated maximum 9.42) instead of deleting. *Mechanism:* maximises ΣE per
  retained dot. *Confounder:* 600 m spacing cannot trace a 300 m-offset strand pair. *Falsifier:* paired
  Δ ≤ −0.010 against `shadow48`.
- **COLLAR_NOREFILL:** strike-aligned collar, mass allowed to fall. *Confounder:* mass and geometry move together.
  *Falsifier:* paired live Δ ≤ −0.010, or a gain no larger than the isotropic no-refill rungs.
- **REDUNDANCY_BUDGET:** drop dots whose 300 m kernel disk is ≥ 90 % covered by neighbours, no refill.
  *Mechanism:* `T` is a max-credit sum, so fully covered mass is pure penalty. *Confounder:* real parallel strands
  legitimately overlap. *Falsifier:* paired live Δ ≤ −0.010.
- **CROSS_STRIKE_RIDGE_SNAP:** Snap R0 dots `<=2 px` strictly orthogonal to local `H19-5` strike onto high-pass magnetic tilt (`tc`) + `det_elev_slope` ridges (raw `tmi_hg`/`iso_grav_anom_slope` window-max pulls 84–86% of dots off `H19-5` due to multi-km wavelength). *Confounder:* dipping lithologic contacts offset magnetic gradients downdip from surface fault traces. *Falsifier:* paired live `Δ <= -0.010` vs R0.
- **STRAND_CONTINUITY_REBUDGET:** Reallocate or thin R0 dots while preserving `>=1 km` along-strike strand continuity (addressing `MASSshadow40pct` dropping all 838 `>=1 km` strands) by replacing short `<500 m` `H19-5` fragments with `2.8 px`-spaced extensions on multi-km corridors. *Confounder:* long unfaulted dikes, hogbacks, or pluvial shorelines also form multi-km corridors. *Falsifier:* paired live `Δ <= -0.010` vs R0 (or `<= -0.005` vs matched-count `MASSrandom`).

## Confounds stated, not hidden

- **The count-held refills are dilutive.** 98.7–99.5 % of the collar variants' refill dots land within 3 px of a
  retained dot (median 1.00 px) and replace a dot a median 845–888 px away: mostly penalty, little fresh credit.
  That is why the collar predictions net to ≈ 0 (IR90-12). If a collar receipt is null, the next test is the same
  collar **without** refill — not a wider collar.
- **Both ladders share one parent and one 2026-10-23 build.** A positive receipt on slot 1 does not validate the
  collar, and vice versa; only the paired receipts compare.
- **The deep ladder trades continuity for credit.** At 5 px linking `shadow40` keeps 0 of R0's 838 ≥ 1 km
  strands and pushes mean dot spacing to 6.19 px (beyond the 300 m kernel); `rand40` keeps 136. The
  credit model says the ranked file is better; the structure says it may not be. That is why the control
  gets a slot instead of a sixth dose (IR90-17).
- **No prediction here is a score.** R0's 0.2778 is a CLAIM, all predictions are MODEL, the canary is a PROXY.
