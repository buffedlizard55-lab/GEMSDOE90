# SLOT PLAN — MASS shadow-dose ladder (2026-10-23b)

**Agent-selected axis: MASS.** Parent R0 `h33-h33-2-b2`, 37,654 unit dots, claimed live **0.2778
(CLAIM — no receipt on file)**. Three fixed subsets were BUILT locally; none was submitted. Doses are
nested: 10 % (33,889 dots), 20 % (30,123), 30 % (26,358). They delete dots in ascending *exclusive
300 m kernel credit* and add or move nothing. At the same 3,765 removals the parent's stored FIFO-BFS
order destroys 53 % more exclusive credit, so this is a mechanically distinct experiment from the
existing `MASS ±10 %` candidates in the sibling ledgers.

**Why this axis now.** The one line of evidence that is not noise in the ledger is the claimed ladder
on a fixed support: 121,131 px 0.1922 → 60,069 dots 0.2477 → 40,199 (solo d2.8) 0.2708 → 37,654 (R0)
0.2778. Every step down in mass gained. Nobody has continued that ladder with the *cheapest* dots
removed; the sibling MASS doses remove spatially contiguous runs instead. A three-point ladder
measures the slope and locates the turnover in one week instead of one point per week.

## Next three slots (conditional on human quota; one entity)

| Order | Candidate (local, ignored `releases/`) | Prediction (MODEL, not a score) | What its receipt changes |
|---|---|---|---|
| 1 | `h33-h33-2-b2-MASSshadow10pct-20261023-e2e518d5.tif` | +0.005; bracket +0.001 to +0.025 | Δ ≥ +0.010 promotes dose 2 next week. Δ ≤ −0.005 kills the mass-reduction direction; then stop, do not spend slots 2–3. \|Δ\| < 0.010 = no evidence. |
| 2 | `h33-h33-2-b2-MASSshadow20pct-20261023-c4ce118b.tif` | +0.009; bracket +0.001 to +0.048 | Doubling the dose separates "mass term dominates" (Δ grows) from "already saturating" (Δ flat). Only run if slot 1 was ≥ 0.00 or if its receipt is unavailable. |
| 3 | `h33-h33-2-b2-MASSshadow30pct-20261023-9d64151a.tif` | +0.012; bracket 0.000 to +0.071 | A decline here with a gain at dose 2 brackets the optimum in 20–30 % and gives a defensible final file. A gain means continue into the PRUNE/MASS combination next week. |

Submit at most one candidate per rolling-week slot, in order, and copy the submission-page receipt
(score + date) back into `ledger/submissions.csv` (`receipt_score`, `date`, `receipt` = Y). The
`-zeros.tif` twin is a fallback encoding for the *same* experiment, never a second slot.

**Pre-slot step (required).** The candidate rasters are gitignored and do not survive a clone. Run
`scripts/restore_data.py`, then `scripts/build_mass_shadow.py --build --verify` for this ladder (or
`scripts/restore_releases.py` for the PRUNE pairs) and match the SHA-256 on disk to the ledger row
before any upload. Both paths fail closed on a hash mismatch; the 2026-10-23 clean-sandbox run
reproduced every recorded hash (`evidence/releases_restore_receipt.json`, `evidence/mass_build_receipt.json`).
Any absolute live change below 0.01 is no evidence; use only one encoding per slot.

## Calendar to the supplied deadline (2026-12-03, UNVERIFIED)

- **Wk 1 (Oct 23–29):** slot 1. If Δ ≥ +0.010, the mass term is exploitable → slot 2 next week.
- **Wk 2 (Oct 30–Nov 5):** slot 2. If Δ(20 %) > Δ(10 %), slot 3; if flat, keep the best file and stop
  spending slots on mass.
- **Wk 3–4 (Nov 6–19):** whichever of the PRUNE collar (3.5 px) and the best MASS dose won, combine
  once — cheapest dots removed *and* collar widened. Do not combine before both singles are measured.
- **Wk 5–6 (Nov 20–Dec 3):** confirm the two best files, choose the final submission and a fallback
  blind to the public score, re-validate both formats, and stop. One final submission only.

Deadline and the 3-per-rolling-week rule are from the brief, not re-checked: automated access to
DrivenData is prohibited. Human confirms both, plus current `TOP_PUBLIC` and slots used.

## Better axes proposed, NOT built this session

- **KERNEL_BUDGET / trace re-spacing:** raise the minimum dot spacing from 2.8 px to 3.6–4.2 px at
  *matched credit* rather than matched count (re-thin H19-5 with a coverage-preserving criterion).
  *Confounder:* coarsening loses along-strike continuity, so a loss confounds mass with resolution.
  *Falsifier:* Δ ≤ −0.005 at equal exclusive credit.
- **TIP_PRIOR:** concentrate mass on tips, step-overs and terminations of known traces (the Faulds
  inventory is a prior on fault-interaction zones, not on truth). *Confounder:* the catalogue is
  masked, so growth geometry is the only usable signal and it may not predict new-fault pixels.
  *Falsifier:* Δ ≤ 0 relative to an equal-count random move.
- **MASS × PRUNE interaction:** at 20 % shadow dose plus a 3.0 px collar, then held count. Only after
  both singles are measured; it should not be built blind.

## Report-only diagnostics

Catalogue hide-and-recover and the SGMC control were **not run**: R0 was itself pruned against the
full catalogue, so a catalogue holdout cannot separate real new-fault credit from the collar and
would only reward mass. The leakage canary is **not applicable** to a mass-only subset edit (no
feature band, no label). Measured structural report instead: removed sets hold 6.5 / 14.7 / 24.7 % of
R0's total exclusive credit at 10 / 20 / 30 % of its mass.

The three PRUNE collar candidates from the earlier session (`-8b96d891`, `-be7a1217`, `-a69816c7`)
remain built and unsubmitted. If the MASS ladder dies at slot 1, spend the next slot on PRUNE 3.5 px
instead of on dose 2 — the two axes ask different questions (mass vs near-catalogue mass) and only one
of them can be resolved per week.
