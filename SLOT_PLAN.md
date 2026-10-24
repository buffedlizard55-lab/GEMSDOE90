# SLOT PLAN — integrated MASS-add / continuity / fixed-count PRUNE (2026-10-23)

**R0:** `h33-h33-2-b2`, 37,654 dots; 0.2778 is **CLAIM**, not a receipt. Human supplies dated `TOP_PUBLIC`, quota use, and confirms 2026-12-03. ONE entity, 3 scored slots/rolling week, ONE blind final ([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Live `|Δ|<0.010` is **no evidence**; private chunks can differ.

## Next 3 slots (NaN primary only; human decides)

| Order | Candidate(s), predicted Δ (`MODEL`) | Decision from receipt |
|---|---|---|
| **1** | `h33-h33-2-b2-MASSadd5pctq50-20261023-c4e6144c.tif` — **+0.008** | `Δ>=+0.010`: add sign pays; Slot 2 = q50-10. `Δ<=-0.010`: close adds for now; Slot 2 = continuity-aware drop **shadowcont20**. `|Δ|<0.010`: no evidence; Slot 2 = orthogonal fixed-count **A5/L1**. |
| **2** | Add branch: `…MASSadd10pctq50-20261023-5edc84de.tif` — **+0.014**. Negative-add branch: `…MASSshadowcont20pct-20261023-66d961ba.tif` — **+0.009**. Null-add branch: `…PRUNEanisoA5L1-20261023-cd2c60ce.tif` — **+0.005** | Add: rising `Δ` licenses q50-20; flat but positive favors matched-placement blocknext10; negative closes the ladder. Continuity: `Δ>=+0.010` → shadowcont40; `Δ<=-0.010` → shadow20 to separate dose from protection. PRUNE: `Δ>=+0.010` → L0.5; `Δ<=-0.010` → recorded A5/L2; null → shadowcont20. |
| **3** | Add: `…MASSadd20pctq50-20261023-f94efff4.tif` — **+0.022**, or matched-dose `…MASSadd10pctBlocknext-20261023-89d16c16.tif` — **+0.0044**. Continuity: `…MASSshadowcont40pct-20261023-92be4121.tif` — **+0.013** / `…MASSshadow20pct-…-c4ce118b.tif` — **+0.009**. PRUNE: `…PRUNEanisoA5L0p5-…-91ff3771.tif` — **+0.003** / recorded **A5/L2** / shadowcont20 | Take exactly one conditional arm. q50-20 requires two positive add receipts and a rising slope; blocknext10 isolates placement at matched dose/geography. L0.5 follows only a positive L1; A5/L2 follows only a negative L1. A null result never licenses a same-axis dose guess. |

Retained but not slotted first: **A5/L1.5** (+0.004), `RELIEFr2p12p5pct` (+0.004), `PRUNEanisoA4L2` (+0.003), `MASSshadowcont30pct` (+0.011), `MASSshadow40pct` (+0.014), and `MASSrandom40pct` (+0.013). They remain valid single-axis candidates; do not spend a slot on any WITHDRAWN FIFO/gapmax/no-refill row or on infeasible SNAP.

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms)

- **Weeks 1–2 (Oct 23–Nov 5):** obtain R0's receipt if possible; execute the conditional order, then only the strongest orthogonal mechanism. No exact-hash or `(AXIS,value)` repeats.
- **Weeks 3–4 (Nov 6–Nov 19):** combine only axes with receipts `Δ>=+0.010`; reserve one slot for parent-vs-composite. q50-20 remains available only if the add slope rises.
- **Weeks 5–6 (Nov 20–Dec 3):** confirm the leader, select ONE blind final plus a `-zeros` fallback, and revalidate both. Account for private chunks and expert-expanded labels ([clarification](https://community.drivendata.org/t/where-do-you-draw-the-line/11536)).

**PRUNE receipt:** `evidence/aniso_along_refill_receipt.json`; all three candidates hold 37,654 dots and `d_cat>2 px`. Canary max AUC 0.5695; catalogue n=13,920 and SGMC n=62,122 are **PROXY / REPORT ONLY**, with 95% CIs, never gates or scores. Predictions were frozen first.

**Continuity receipt:** `evidence/mass_continuity_receipt.json`; all 857 R0 strands survive whole at 6 px at every dose. State the link distance in geological review (IR90-27).

**Future axis, not built — `REFILL_RANK`:** use 5 km-block-stratified exact marginal-kernel refill at fixed collar/count. *Mechanism:* reduce ~98% redundant refill without regional holes. *Confounder:* H19-5 contacts/drainages and quotas are not truth. *Falsifier:* paired live `Δ<=-0.010` or region-evenness failure. `COLLAR_NOREFILL` is withdrawn (IR90-29); cross-strike SNAP is infeasible for 30 dots (IR90-28).

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

## Session 2026-10-23 result (continuity session, merged): `CONTINUITY_AWARE_DOSE` built as MASS shadowcont 20/30/40%

The previously proposed continuity-aware dose is now built (`src/continuity.py`, receipt
`evidence/mass_continuity_receipt.json`): shadow ranking unchanged, strand eligibility added (≤ 6 px link
graph — kernel diameter, a deliberate loosening of the 5 px sketch in the proposal below so along-strand
thinning to ~5–6 px sampling stays legal; ≥ 10-dot strands; articulation + 10-dot floor). All 857 R0 strands
survive whole at 6 px at every dose (unconstrained shadow: 234 / 26 / 0 whole at 20/30/40%); on the legacy
5 px instrument shadowcont-40 still reads only 70 strands ≥ 10 dots (IR90-27), so map review must state its
link distance. Credit price +2.7/+5.8/+7.4% vs shadow; predictions `MODEL` +0.009 / +0.011 / +0.013. Axis
choice audit: all seven axes built sibling-side, zero receipts entity-wide, brief-literal CONCENTRATION-up
≤ 0 on GEMSDOE86's SGMC MODEL at every built dose (IR90-26), converging with this repo's IR90-25
credit-uniformity measurement — do not spend a slot re-cutting it. In the merged order above, shadowcont-20
is the first drop-direction probe (negative-add Slot 2 branch / Slot 3 escalation); it does not displace the
add-direction sign test that now leads the week.

## Better axes proposed (all sessions — not built)

- **CONTINUITY_AWARE_DOSE.** ~~Same 40 % dose, but the greedy may not delete a dot whose removal splits a
  ≥ 1 km strand at 5 px linking.~~ **Built 2026-10-23** as `MASSshadowcont20/30/40pct` at 6 px linking
  (session result above); kept here as the proposal of record. *Falsifier:* paired Δ ≤ −0.010 against `shadow40`.
- **TIP_FLOOR (strand floor by length / tip-cone protection).** The built floor counts dots (≥10), so short
  < 1 km fragments — including genuine relay tips in 0.3–2.5 km along-strike cones ahead of catalogue
  terminations (Faulds step-over prior, interaction zones only per brief §2) — are unprotected and leave
  early. *Mechanism:* protect fragments by strand length and tip-cone membership instead of dot count.
  *Confounder:* fan-head channels at canyon mouths occupy the same cones. *Falsifier:* paired Δ ≤ −0.010
  against `shadowcont40`.
- **KERNEL_ORACLE_DOSE.** Re-space survivors to a ~6 px anti-cluster (just outside the kernel, where
  exclusive credit equals the isolated maximum 9.42) instead of deleting. *Mechanism:* maximises ΣE per
  retained dot. *Confounder:* 600 m spacing cannot trace a 300 m-offset strand pair. *Falsifier:* paired
  Δ ≤ −0.010 against `shadow48`.
- **COLLAR_NOREFILL:** **WITHDRAWN (IR90-29)** — A4/A5/A6,L2 probes changed mass as well as geometry and violated this session's fixed-count refill recipe. Do not upload or use as a follow-up.
- **REDUNDANCY_BUDGET:** drop dots whose 300 m kernel disk is ≥ 90 % covered by neighbours, no refill.
  *Mechanism:* `T` is a max-credit sum, so fully covered mass is pure penalty. *Confounder:* real parallel strands
  legitimately overlap. *Falsifier:* paired live Δ ≤ −0.010.
- **CROSS_STRIKE_RIDGE_SNAP:** **INFEASIBLE under current constraints (IR90-28)**; do not build unless a constraint changes. Historical proposal: snap R0 dots `<=2 px` strictly orthogonal to local `H19-5` strike onto high-pass magnetic tilt (`tc`) + `det_elev_slope` ridges (raw `tmi_hg`/`iso_grav_anom_slope` window-max pulls 84–86% of dots off `H19-5` due to multi-km wavelength). *Confounder:* dipping lithologic contacts offset magnetic gradients downdip from surface fault traces. *Falsifier:* paired live `Δ <= -0.010` vs R0.
- **STRAND_CONTINUITY_REBUDGET:** Reallocate or thin R0 dots while preserving `>=1 km` along-strike strand continuity (addressing `MASSshadow40pct` dropping all 838 `>=1 km` strands) by replacing short `<500 m` `H19-5` fragments with `2.8 px`-spaced extensions on multi-km corridors. *Confounder:* long unfaulted dikes, hogbacks, or pluvial shorelines also form multi-km corridors. *Falsifier:* paired live `Δ <= -0.010` vs R0 (or `<= -0.005` vs matched-count `MASSrandom`).

## Confounds stated, not hidden

- **The count-held refills are dilutive.** 98.7–99.5 % of the collar variants' refill dots land within 3 px of a
  retained dot (median 1.00 px) and replace a dot a median 845–888 px away: mostly penalty, little fresh credit.
  That is why the collar predictions net to ≈ 0 (IR90-12). If a collar receipt is null, the next proposed test is
  **REFILL_RANK at fixed collar and count**, not a wider collar; delete-only COLLAR_NOREFILL is withdrawn (IR90-29).
- **Both ladders share one parent and one 2026-10-23 build.** A positive receipt on slot 1 does not validate the
  collar, and vice versa; only the paired receipts compare.
- **The deep ladder trades continuity for credit.** At 5 px linking `shadow40` keeps 0 of R0's 838 ≥ 1 km
  strands and pushes mean dot spacing to 6.19 px (beyond the 300 m kernel); `rand40` keeps 136. The
  credit model says the ranked file is better; the structure says it may not be. That is why the control
  gets a slot instead of a sixth dose (IR90-17).
- **No prediction here is a score.** R0's 0.2778 is a CLAIM, all predictions are MODEL, the canary is a PROXY.

## Session 2026-10-23f (this branch): placement contrast for the add ladder — swap-in, not a 4th candidate

The merged add ladder (`MASSadd5pctq50` / `add10pctq50` / `add20pctq50`, PR #16) ranks candidates by **marginal kernel
credit**. This session built the same doses and the same region-even quotas but ranked by the **parent's own FIFO-BFS
order** — the brief's literal "next-ranked" recipe, with its geography repaired. Two live files:
`MASSadd10pctBlocknext` (41,419 dots, pred **+0.0044 MODEL** [+0.0003…+0.0107]) and `MASSadd20pctBlocknext` (45,185,
pred **+0.0084 MODEL** [+0.0005…+0.0205]). A third arm, `MASSadd10pctGapmax`, was withdrawn as a duplicate of
`MASSadd10pctq50` (IR90-24).

**How to use it.** It is a *control*, so it should not displace the ladder's first two slots. Insert
`MASSadd10pctBlocknext` as the third slot in either of these cases:
- `MASSadd5pctq50` and `MASSadd10pctq50` both land in `Δ >= +0.010` → the sign is settled, and the open question becomes
  *which placement earns it*. blocknext10 shares dose and geography with q50-10 and differs only in ranking, so the pair
  measures the ranking directly. `blocknext` ≥ +0.010 means plain mass addition pays and the credit ranking is
  second-order (cheaper to scale); `blocknext` ≈ 0 while q50 ≥ +0.010 means kernel-room placement is the whole effect,
  and every future add must be gap-ranked.
- `MASSadd5pctq50` and `MASSadd10pctq50` are both null (`|Δ| < 0.010`) → the ladder's own placement is not the issue and
  the cheaper check is whether *any* placement adds: blocknext10 answers it at the same dose.

If the ladder's first two slots are negative (`Δ <= −0.010`), do not slot blocknext: R0 is at or past its mass optimum
and the next slot belongs to the drop direction (`MASSshadow20pct`), not to a third add file.
`MASSadd20pctBlocknext` is only worth a slot if the 10 % contrast has already shown that placement matters.
