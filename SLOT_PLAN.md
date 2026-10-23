# SLOT PLAN — R0 MASS dose-ladder rungs (2026-10-23, session arena/307b04fc)

**Agent-selected session axis: MASS.** Parent R0 `h33-h33-2-b2` (37,654 unit dots; `0.2778` = **CLAIM**, no receipt) rebuilt byte-identically (`evidence/r0_rebuild_receipt.json`). The brief's ±10 % MASS pairs (and −20 %, and a 10 % swap) are already built by parallel sessions GEMSDOE84/85/86/87/88/89/91/92 under several selection policies; this session fills the missing rungs of one dose ladder on the parent's own recorded ranking (H19-5 FIFO-BFS traversal): **drop5pct-tail, add5pct-next, add20pct-next** — free in every checked ledger (audit in `ledger/experiment_reservations.json`). Three fixed-count-family candidates are local under ignored `releases/`. No submission was made. `TOP_PUBLIC` (with date) and weekly slots used/remaining are **unknown**; human must confirm before allocating any slot.

**Mechanism.** Dose is the only edited quantity. Drop = remove the 1,883 lowest-ranked (traversal-tail) dots (5.00 % of R0). Add = place the next-ranked cells the parent's own 2.8 px thinning suppressed (99.5 %+ sit <2.8 px from an existing dot; added cells keep d_cat ≥ 3 px). DTI pays a dot only if its marginal kernel credit beats ≈0.2·DTI, so redundant adds should cost and tail drops trade unique coverage against false-positive mass. Report-only PROXYs (catalogue hide-and-recover; SGMC control) lean drop-negative and add-neutral; they are not scores and do not gate anything.

## Next three slots (conditional on human quota; one entity only; coordinate with sibling ledgers)

| Order | Candidate | Prediction (MODEL, not a score) | What its receipt changes |
|---|---|---|---|
| 1 | `h33-h33-2-b2-MASSadd20pct-next-20261023-63954e89.tif` | −0.008; plausible −0.020 to +0.004 | The only unbuilt top rung of the add ladder. Δ≥+0.010 falsifies kernel redundancy and promotes spaced/larger adds (the sibling +10 % files become prime). Δ≤−0.010 closes the add direction for redundant cells. |
| 2 | `h33-h33-2-b2-MASSdrop5pct-tail-20261023-ce48329b.tif` | −0.002; plausible −0.010 to +0.003 | Adjudicates the sibling split on drops (GEMSDOE84 predicts drops help, GEMSDOE85/86 predict drops hurt) at the safe 5 % end. Δ≥+0.010 re-opens the built −10/−20 % rungs; Δ≤−0.010 closes drops. |
| 3 | `h33-h33-2-b2-MASSadd5pct-next-20261023-46f0886b.tif` | −0.002; plausible −0.009 to +0.005 | Only worth a slot if slot 1 shows a slope (its receipt gives the curvature point between R0 and +20 %). If all receipts sit inside ±0.010: no evidence — do not promote on a PROXY. |

Under the session rule, **any absolute live change below 0.01 is no evidence**; public-chunk effects may not transfer to private chunks. Compare each candidate against R0 with a human-copied receipt, preferably the same rolling week. Upload one encoding per slot; the `-zeros.tif` twin is a fallback, not a second experiment.

## Calendar to supplied deadline

Deadline `2026-12-03` and the 3-per-rolling-week quota are supplied by the brief, not freshly checked (automated access to DrivenData is prohibited). Human confirms the cutoff and quota: https://www.drivendata.org/competitions/306/competition-doe-gems/ · rules https://docs.nlr.gov/docs/fy26osti/96647.pdf.

- **Weeks 1–2 (Oct 23–Nov 5):** slot 1 (add20) if a slot exists after any higher-priority sibling candidates the human wants first; request R0 + candidate receipts.
- **Weeks 3–4 (Nov 6–19):** slots 2–3 only per the table's conditions; this is also the combination window — combine the two *receipt-backed* best axes, not the two best predicted ones.
- **Weeks 5–6 (Nov 20–Dec 3):** confirm, choose the final file and a fallback blind, re-validate the format of both. One final submission only. Keep slots if no rung has cleared ±0.010.

## Better axes proposed only (not built this session)

- **KERNEL_BUDGET:** at fixed mass, re-space nearby R0 dots along the 300 m kernel so each dot covers a distinct truth segment (greedy max-coverage thinning at fixed count). *Mechanism:* reduces max-operator redundancy inside the 0.2(S−M) term without changing the dose. *Confounder:* close parallel strands and step-overs are real faults; de-clustering can erase real damage-zone strands. *Falsifier:* paired live Δ≤−0.010 vs R0 at the same count.
- **EDGE_COHERENCE:** require multi-scale linear-gradient persistence (TMI/gravity HGM concordance) before a dot may sit on H19-5 support. *Mechanism:* fault traces persist across independent potential-field edges; lithologic/drainage lineaments usually do not. *Confounder:* unfaulted contacts and bedrock-crests also persist; the GeoDAWN 400 m line spacing blurs edges by ~1 kernel radius (USGS 657e1d85d34e23d3533209f7). *Falsifier:* paired live Δ≤−0.010 or no repeatable gain on untouched spatial folds.
- **TRACE_ALIGN (pre-TTRACKB):** rotate each dot ≤1 px to align its local 3-px neighbourhood with the strike of its connected H19-5 strand. *Mechanism:* Phase-2 experts expand labels from submitted faults; strike-consistent chains read as faults and survive review (problem-page Phase 2 description). *Confounder:* polished traces on non-fault lineaments could mislead reviewers and get orphaned. *Falsifier:* geologist review rejects >50 % of chains as non-faults before the final choice.

**TRACKB** remains a Phase-2 deliverable (strike-consistent ≥1 km traces as GeoJSON + raster + evidence paragraphs), not a weekly-slot candidate unless the human decides; no slot in this plan spends on it.
