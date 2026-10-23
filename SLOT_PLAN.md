# SLOT PLAN — merged state after the 2026-10-23 sessions (MASS ladder incl. high doses, both PRUNE collars)

Two mechanisms were built today against the same parent, `h33-h33-2-b2` (R0: 37,654 unit dots, **CLAIM** 0.2778,
no submission-page receipt on file). **Twelve candidates, none submitted, none scored.** `TOP_PUBLIC`, the dated
leaderboard target and the weekly quota are still unknown — the human confirms them before any slot is used.
This file merges the MASS shadow-dose ladder and the strike-aligned PRUNE collar into one ordered plan.

## What exists and what each result would tell us

| Candidate | Change from R0 | Prediction (MODEL) | Falsifier / what the receipt changes |
|---|---|---|---|
| `MASSshadow10pct` (33,889 dots) | drop the 10 % of dots with least exclusive kernel credit | **+0.005** (−0.010…+0.015) | Δ ≤ −0.005 → stop the ladder; Δ ≥ +0.010 → the mass direction is real, take the top rung next. |
| `MASSshadow20pct` / `30pct` (30,123 / 26,358) | same ranking, deeper | **+0.009** / **+0.012** | Nested rungs: a monotone rise supports "R0 is over-massed"; a peak at 10 % says the tail still earns credit. |
| `MASSshadow40pct` / `48pct` (22,592 / 19,580) | same ranking, deepest doses that stay spatially uniform | **+0.014** / **+0.015** | Δ ≤ 0 while 20/30 % were positive puts the turnover between 30 % and 48 %; Δ ≤ −0.005 ends the direction. 48 % is the ceiling: at 50 % the greedy starts emptying whole regions (IR90-17). |
| `MASSrandom40pct` (22,592) | identical dose, **credit-blind** seeded subset | **+0.013** | The control for the whole ladder: within 0.005 of `shadow40` ⇒ the ranking adds nothing, only dose matters; ≥ 0.005 better ⇒ the ranking is wrong. It also keeps 136 of R0's 838 ≥ 1 km strands, which `shadow40` destroys entirely. |
| `PRUNEanisoA4L2` (`…0bf248e2`) | strike-aligned collar, 4 px across / 2 px along, count held | **+0.003** (−0.010…+0.010) | Δ ≤ −0.010 → the collar direction is exhausted; \|Δ\| < 0.010 → no evidence, do not buy A5. |
| `PRUNEanisoA5L2` / `A6L2` | wider across-strike collar, 19.5 % / 24.6 % of dots changed | **+0.002** / **+0.000** | A monotone decline over A4→A6 rejects the dose response the mechanism implies. |
| `PRUNE3p5px` / `4p5px` / `5p5px` (earlier session) | isotropic collar, count held | **+0.002** / **+0.000** / **−0.003** | The isotropic comparator: with A4 it separates "wider collar" from "along-strike exemption". |

Why these two mechanisms and nothing else: the collar is the only step in the ledger with a live gradient behind
it (parent's own 2 px rung, 0.2708 → 0.2778 **CLAIM**), and mass is the only lever with a closed-form prediction
from the metric algebra — removing a dot with no exclusive credit lowers `0.2·(S−M)` and leaves `T` untouched.
Every field-replacement lane (radon, hydro-conduit, Euler, tensor, basement step, SAR/EM, tilt ring) scored
0.00–0.19 and is closed. Every allowed axis has already been built elsewhere with no receipt (GEMSDOE84–88:
117 axis rows, one scored), so novelty alone is no longer a reason to build.

## Next three slots, in order

| Order | File | Why here | If the receipt says |
|---|---|---|---|
| 1 | `MASSshadow20pct` (30,123 dots) | The mild rung: 20 % of dots gone, a strict subset of R0, no new geometry. Buying the cheap end first keeps a slot in reserve if the direction is wrong. | ≥ +0.010 → slot 2 goes deep (`MASSshadow40pct`). +0.005…+0.010 → slot 2 stays on the ladder (`MASSshadow30pct`). ≤ −0.005 → stop the ladder; slot 2 becomes `PRUNEanisoA4L2`. |
| 2 | `MASSshadow40pct` (22,592) | The deep rung with the largest predicted gain, and the only dose above 30 % that stays spatially uniform. | ≥ +0.010 → slot 3 = `MASSshadow48pct` (next week) and keep `MASSrandom40pct` for the ranking test. ≤ −0.005 → the ladder is a pure low-dose effect: slot 3 = `MASSrandom40pct` to see whether ranking or mass caused it. |
| 3 | `MASSrandom40pct` (22,592) | Same dose as slot 2, credit-blind. Three receipts (0 % anchor, ranked 40 %, random 40 %) separate dose from selection in one week. | Beats `shadow40` by ≥ 0.005 → abandon the exclusive-credit ranking and build the continuity-aware variant proposed below. Within ±0.005 → ranking adds nothing; spend later slots on the collar. |

`PRUNEanisoA4L2` is the reserve: it is the only other lever with a prior (the parent's own 2 px rung,
0.2708 → 0.2778 CLAIM) and it is a different mechanism on the same parent, so it is the slot to take if the
mass ladder goes null in both directions. Never take two mechanisms in one week when one receipt would
explain both.

A live change under **0.01** is no evidence: the public leaderboard covers only part of the region and the private
score may differ. Never let a local diagnostic promote a file — the leakage canary and the hide-and-recover proxy
rank nothing.

## Better axes, proposed only (not built this session)

- **CONTINUITY_AWARE_DOSE.** Same 40 % dose, but the greedy may not delete a dot whose removal splits a
  ≥ 1 km strand at 5 px linking. *Mechanism:* keeps the mass saving while preserving the line-like coverage
  `T` is paid for. *Confounder:* 5 px linking is a geometric choice, not evidence the strand is a fault, so
  it can preserve false mass. *Falsifier:* paired Δ ≤ −0.010 against `shadow40`.
- **KERNEL_ORACLE_DOSE.** Re-space survivors to a ~6 px anti-cluster (just outside the kernel, where
  exclusive credit equals the isolated maximum 9.42) instead of deleting. *Mechanism:* maximises ΣE per
  retained dot. *Confounder:* 600 m spacing cannot trace a 300 m-offset strand pair. *Falsifier:* paired
  Δ ≤ −0.010 against `shadow48`.

## Calendar to the supplied deadline

Deadline `2026-12-03` and the 3-scored-submissions-per-rolling-week rule come from the brief, not a fresh check
(automated access to DrivenData is prohibited by its terms). Confirm both, plus current quota, from
https://www.drivendata.org/competitions/306/competition-doe-gems/ and
https://docs.nlr.gov/docs/fy26osti/96647.pdf.

- **Week 1 (Oct 23–29):** slots = `MASSshadow20pct`, `MASSshadow40pct`, `MASSrandom40pct` if three slots are
  free; if only one, `MASSshadow20pct`. Request the submission-page receipts and dates.
- **Week 2 (Oct 30–Nov 5):** `PRUNEanisoA4L2` (or `MASSshadow48pct` if slot 2 cleared +0.010), only with the
  week-1 receipts in hand.
- **Weeks 3–4 (Nov 6–19):** slot 3 = escalation or hold, per the table. Do not build more variants: nine
  unscored candidates for three weekly slots is already the bottleneck.
- **Weeks 5–6 (Nov 20–Dec 3):** choose the final file and a fallback **blind**, re-run `src.validate` on both,
  confirm neither sha256 was ever submitted (at least 8 historical slots were exact repeats), and check the quota.

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

## Proposed next axes (not built this session)

- **COLLAR_NOREFILL:** strike-aligned collar, mass allowed to fall. *Confounder:* mass and geometry move together.
  *Falsifier:* paired live Δ ≤ −0.010, or a gain no larger than the isotropic no-refill rungs.
- **REDUNDANCY_BUDGET:** drop dots whose 300 m kernel disk is ≥ 90 % covered by neighbours, no refill.
  *Mechanism:* `T` is a max-credit sum, so fully covered mass is pure penalty. *Confounder:* real parallel strands
  legitimately overlap. *Falsifier:* paired live Δ ≤ −0.010.
