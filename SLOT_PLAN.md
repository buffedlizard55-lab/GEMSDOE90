# SLOT PLAN — high-dose MASS + credit-blind control (2026-10-23c)

**Agent-selected axis: MASS.** Parent R0 `h33-h33-2-b2`, 37,654 unit dots, claimed live **0.2778
(CLAIM — no receipt on file)**. This session BUILT three new, unclaimed `(MASS, value)` pairs; none was
submitted. All are strict subsets: **no additions, no moves, no collar change**.

| Built | Dots | Change vs R0 | Selection |
|---|---|---|---|
| `…MASSshadow40pct-20261023-e2546fbe` | 22,592 | −40.0011 % (15,062 removed) | ascending exclusive 300 m kernel credit |
| `…MASSshadow48pct-20261023-88a2e8cc` | 19,580 | −48.0002 % (18,074 removed) | same, deeper |
| `…MASSrandom40pct-20261023-894b5b4a` | 22,592 | −40.0011 % (15,062 removed) | seeded uniform random (`rng(20261023)`), credit-blind |

**Why MASS.** Every recorded step down the mass ladder on this lineage gained: 121k px 0.1922 → 44k dots
0.2477/0.2600 → 37.6k 0.2708 → R0 0.2778 (all CLAIM except the d2.8 0.2600). The in-repo 10/20/30 %
shadow doses are still unscored; 40 % and 48 % are the only new doses above them, and `rand40` is the
control the ladder never had.

**Two arms were probed and rejected before submission** (recorded, not built — `evidence/mass_high_dose_receipt.json`):
*FIFO-order drops* 10/20/40 % (the parent's stored BFS order, used by the sibling MASS doses) delete one
south-east corner and at 40 % empty 41 % of 5 km blocks in a single 632-block hole — region-isolated,
Hard Constraint #5; *shadow 50 %* starts emptying whole regions (largest emptied cluster 17 blocks =
425 km²), which is why the deep arm stops at 48 %.

## Next three slots (conditional on the human's remaining quota; one entity)

| Order | Candidate | Prediction (MODEL, not a score) | What its receipt changes |
|---|---|---|---|
| 1 | `MASSshadow40pct` | **+0.014** (bracket +0.004 to +0.025) | Δ ≥ +0.010: the deep direction is real → slot 2 = `shadow48pct`; Δ ≤ −0.005: mass reduction is finished, slot 2 = `shadow10pct` or a PRUNE file, and stop spending slots on dose; \|Δ\| < 0.010 = no evidence → slot 2 = `shadow20pct` (milder dose, same ranking). |
| 2 | `shadow48pct` **if** slot 1 ≥ +0.010, else `shadow20pct` | +0.015 (+0.002 to +0.030) / +0.009 | A second positive dose with a smaller increment locates the turnover between 40 % and 48 %. A decline at 48 % while 40 % was positive puts the optimum at 30–40 %. |
| 3 | `MASSrandom40pct` (same week as slot 1 if possible) | +0.013 (+0.004 to +0.023) | Same dose, credit-blind. If rand40 lands within 0.005 of shadow40, the exclusive-credit ranking adds nothing and the ladder is a pure mass effect — then the next session should spend no effort on ranking. If rand40 beats shadow40 by ≥ 0.005, the ranking is wrong (see the continuity finding below) and must be abandoned. |

Pair every candidate against a *same-week* R0 receipt. R0's 0.2778 is a CLAIM, so a paired delta is the
only measurement that counts. One encoding per slot: `-zeros.tif` is a fallback twin, never a second
experiment. A live change below 0.01 is **no evidence** (public chunks only).

**Structural warning that competes with the prediction.** At 5 px linking, R0 has 838 strands ≥ 1 km;
`shadow40` keeps **0** of them (mean dot spacing 3.74 → 6.19 px, 100 % of dots beyond the kernel radius),
while `rand40` keeps 136 (spacing 4.70 px). The ranking removes densely sampled stretches and leaves
isolated singletons. If new-fault truth is line-like, the credit argument can lose to lost along-strike
continuity and `shadow40` may score *below* `rand40`. Both predictions are recorded; the paired receipts
decide. That is exactly why `rand40` deserves a slot.

## Calendar to the supplied deadline (2026-12-03, UNVERIFIED — human confirms)

Deadline and the 3-scored-submissions-per-week rule come from the brief; automated access to DrivenData
is prohibited, so neither is re-checked here. Confirm both on the competition page and in the rules PDF
(https://docs.nlr.gov/docs/fy26osti/96647.pdf).

- **Wk 1 (Oct 23–29):** slot 1 = `shadow40`, slot 3 = `rand40` (the pair is the experiment); slot 2 only if
  two slots are free.
- **Wk 2 (Oct 30–Nov 5):** the conditional second dose, plus one PRUNE file (`PRUNE3p5px`) as the
  independent lever — it is the only other mechanism with a recorded positive prior.
- **Wk 3–4 (Nov 6–19):** combine the two best axes **only after** both receipts are ≥ +0.010; keep `rand40`
  as the ranking control.
- **Wk 5–6 (Nov 20–Dec 3):** confirm the best verified pair, choose the final file and one fallback blind,
  re-validate both against `sample_submission.tif`, and keep one slot in reserve. Ask the organisers
  whether the final submission may repeat an already-scored file — that changes the week-6 arithmetic.

## Better axes, proposed only (not built this session)

- **CONTINUITY_AWARE_DOSE.** Same dose as `shadow40`, but the greedy may not delete a dot whose removal
  splits a ≥ 1 km strand at 5 px linking. *Mechanism:* keeps the mass saving while preserving the
  line-like coverage that T is paid for. *Confounder:* strand linking at 5 px is a geometric choice, not
  evidence the strand is a fault; preserving a false strand keeps false mass. *Falsifier:* paired Δ ≤ −0.010
  against `shadow40`, or no gain on untouched spatial folds.
- **KERNEL_ORACLE_DOSE.** Re-space the surviving dots to a distance-6 px anti-cluster (just outside the
  kernel, where exclusive credit equals the isolated-dot maximum 9.42) instead of deleting them.
  *Mechanism:* maximises ΣE per retained dot. *Confounder:* 600 m spacing cannot trace a 300 m-offset
  strand pair. *Falsifier:* paired Δ ≤ −0.010 versus `shadow48`.
