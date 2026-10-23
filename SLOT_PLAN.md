# SLOT PLAN — merged state after the 2026-10-23 sessions

Two mechanisms were built today against the same parent, `h33-h33-2-b2` (R0: 37,654 unit dots, **CLAIM** 0.2778,
no submission-page receipt on file). **Nine candidates, none submitted, none scored.** `TOP_PUBLIC`, the dated
leaderboard target and the weekly quota are still unknown — the human confirms them before any slot is used.
This file merges the MASS shadow-dose ladder and the strike-aligned PRUNE collar into one ordered plan.

## What exists and what each result would tell us

| Candidate | Change from R0 | Prediction (MODEL) | Falsifier / what the receipt changes |
|---|---|---|---|
| `MASSshadow10pct` (33,889 dots) | drop the 10 % of dots with least exclusive kernel credit | **+0.005** (−0.010…+0.015) | Δ ≤ −0.005 → stop the ladder; Δ ≥ +0.010 → the mass direction is real, take the top rung next. |
| `MASSshadow20pct` / `30pct` (30,123 / 26,358) | same ranking, deeper | **+0.009** / **+0.012** | Nested rungs: a monotone rise supports "R0 is over-massed"; a peak at 10 % says the tail still earns credit. |
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
| 1 | `MASSshadow10pct` (33,889 dots) | Cheapest entry to the nested ladder; largest predicted gain per unit of change (+0.005 at 10 % of dots), and it is a strict subset of R0 so no new geometry is invented. | ≥ +0.010 → slot 3 goes to `MASSshadow30pct`. +0.005…+0.010 → slot 3 to `MASSshadow20pct`. ≤ −0.005 → stop the ladder, keep slot 3. |
| 2 | `PRUNEanisoA4L2` (`…0bf248e2`) | A different mechanism on the same parent; the safest dose of the only other lever with prior support, and it keeps 1,193 along-strike dots an isotropic 4 px collar would delete. | Δ ≤ −0.010 → close the collar line. \|Δ\| < 0.010 → no evidence; do not spend a slot on A5/A6. |
| 3 | Escalation on whichever of slots 1–2 cleared +0.010, else **hold** | One confirmation of the winning direction is worth more than a third blind mechanism, and the final submission is still unspent. | If both are null, hold the slot and re-validate R0 as the final file. |

A live change under **0.01** is no evidence: the public leaderboard covers only part of the region and the private
score may differ. Never let a local diagnostic promote a file — the leakage canary and the hide-and-recover proxy
rank nothing.

## Calendar to the supplied deadline

Deadline `2026-12-03` and the 3-scored-submissions-per-rolling-week rule come from the brief, not a fresh check
(automated access to DrivenData is prohibited by its terms). Confirm both, plus current quota, from
https://www.drivendata.org/competitions/306/competition-doe-gems/ and
https://docs.nlr.gov/docs/fy26osti/96647.pdf.

- **Week 1 (Oct 23–29):** slot 1 = `MASSshadow10pct`. Request the submission-page receipt and date.
- **Week 2 (Oct 30–Nov 5):** slot 2 = `PRUNEanisoA4L2`, only with slot 1's receipt in hand.
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
- **No prediction here is a score.** R0's 0.2778 is a CLAIM, all predictions are MODEL, the canary is a PROXY.

## Proposed next axes (not built this session)

- **COLLAR_NOREFILL:** strike-aligned collar, mass allowed to fall. *Confounder:* mass and geometry move together.
  *Falsifier:* paired live Δ ≤ −0.010, or a gain no larger than the isotropic no-refill rungs.
- **REDUNDANCY_BUDGET:** drop dots whose 300 m kernel disk is ≥ 90 % covered by neighbours, no refill.
  *Mechanism:* `T` is a max-credit sum, so fully covered mass is pure penalty. *Confounder:* real parallel strands
  legitimately overlap. *Falsifier:* paired live Δ ≤ −0.010.
