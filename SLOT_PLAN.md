# SLOT_PLAN.md — next 3 slots in order (≤1 page)

**Deadline:** 2026-12-03 (confirm on https://www.drivendata.org/competitions/306/) | **Quota:** 3 scored submissions / rolling week + ONE final (chosen blind) | **Entity:** ONE | **Parent R0:** h33-h33-2-b2 (37,654 dots, CLAIM 0.2778 — no receipt) | **Beat:** TOP_PUBLIC = ___ (human fills from leaderboard with date)

## This session (2026-10-23) — AXIS=CONCENTRATION (agent-chosen, no prompt per brief)
Block 1 km (10 px). Moved 10/15/20% of dots low→high prior blocks; CV 1.20→2.97/3.64/4.16; n=37,654 held; ≥3px catalogue. Predicted Δ: +0.001/+0.002/+0.003 MODEL. Status: **SYNTHETIC stand-ins only** — cannot submit until parent rebuild passes sha256 + pinned manifest (see IRREGULARITIES.md). Ledger: `ledger/submissions.csv` (3 BUILT).

## Next 3 slots (once unblocked) — in priority order
1. **Slot 1 — MASS-10down (PRUNE 10% lowest-ranked dots, no refill).** Hypothesis: marginal dots below 0.2·DTI (~0.056 credit) hurt score (D). Change: drop 3,765 lowest-marginal-gain dots by exact DTI ranking (`scripts/dti.py`). Predicted: +0.002 to +0.005 if R0 over-dense; confounder is field strength vs mass. **Falsifier:** score drops or <0.01 → R0 mass is near-optimal; stop mass tests.
2. **Slot 2 — PRUNE ≥3px + refill to hold count.** Hypothesis: known-fault halo leaks mass into masked zone (wasted S without T). Change: remove any R0 dots ≤3 px of catalogue, refill from next-ranked outside halo. Predicted: −0.002 to +0.004 (depends on how much R0 already hides near traces). Falsifier: <0.01 → masking is already sufficient; catalogue proximity is not leaking.
3. **Slot 3 — RELIEF shift 12% basin→range-front.** Hypothesis: geothermal systems sit at range-front step-overs (Faulds inventory prior), not basin pediments; new-fault truth may follow same. Change: move 12% mass from low-relief tercile to high-relief tercile (detrended elevation). Predicted: +0.003 to +0.008 if prior is causal; confounder is exposure bias (ranges better mapped). Falsifier: score ≤ baseline → prior is exposure artifact; pivot to SNAP.

**What each result changes:**
- If Slot 1 wins → proceed to MASS-10up vs MASS-15down to bracket optimum mass.
- If Slot 2 wins → combine with best CONC (e.g., CONC15 + PRUNE3px) in week 3.
- If Slot 3 wins → week 3 combines RELIEF + CONCENTRATION; week 4 adds SNAP refinement (≤2 px snap to lidar/TMI gradient) on top of winner.

## Weeks to deadline (5.5 weeks)
- **Wk1–2 (now–2026-11-06):** Unblock parents → run slots 1–3 above, each as one controlled (parent,axis,value) with ledger entry. Do not build two axes at once.
- **Wk3–4 (2026-11-07–11-20):** Combine two best axes (e.g., best MASS or PRUNE + best CONC/RELIEF) at matched count; test at most 2 combos.
- **Wk5 (2026-11-21–11-27):** Confirmation: re-score winner conceptually vs R0 on private-chunk intuition (public score Δ<0.01 is no evidence). No new axis.
- **Wk6 (2026-11-28–12-03):** Choose final + fallback (fallback = R0 or runner-up), re-validate both formats (`scripts/validate.py` with true footprint + catalogue + sha256 dedupe), freeze ledger, submit final blind.

## Better axes proposed (mechanism, confounder, falsifier) — do not build this session
- **INTERSECTION density:** Prior = count of known-fault intersections per km² (Faulds steps). Mechanism: new faults nucleate at transfer zones. Confounder: intersection maps co-locate with well-mapped swaths → exposure. Falsifier: CONC already captures it (CV does not improve over intersection-weighted move).
- **Gravity gradient abruptness (basement step):** Prior = horizontal gravity gradient magnitude (USGS). Mechanism: basement offset localizes cover faults. Confounder: gradient highs are also range fronts → colinear with RELIEF. Falsifier: SNAP to梯度 shows no displacement gain vs uniform.
- **Hydro-conduit confluence:** Prior = drainage confluence + thermal-spring proximity (NBMG). Mechanism: faults channel fluids → alter detectable chemistry/temperature. Confounder: sampled springs are clustered where roads exist. Falsifier: mass moved to confluences scores worse than uniform.
