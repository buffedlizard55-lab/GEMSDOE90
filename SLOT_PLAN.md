# SLOT_PLAN — GEMSDOE90 (AXIS=PRUNE chosen by agent, 2026-10-23)

State: R0 = h33-h33-2-b2, 0.2778 **CLAIM** (no receipt). TOP_PUBLIC = ____
(human, with date). Slots: ONE entity, 3/week; left this week __ / total __
(human). Deadline 2026-12-03 (UNVERIFIED — human confirms on competition
page) ≈ 6 weeks ≈ ≤18 slots from 2026-10-23. **No variant is built yet**:
inputs missing (IRREGULARITIES #1). Once the human pins `data/` (see
docs/SUBMIT.md), `python -m src.build_prune` builds all three below; submit
in this order, one file per slot, NaN-outside version.

## Next 3 slots
1. **PRUNE ≤3 + refill (count-held)** — pushes the incumbent's own direction.
   ≥ +0.01: outward prune is real → try ≤4 in combination week. ≤ −0.01:
   3 px ring holds true (re-mapped) geometry → never prune beyond 2 again.
   |Δ| < 0.01: no evidence; slot 3 (control) becomes decisive.
2. **PRUNE ≤1 (count-held)** — completes the dose–response slope.
   Slope sign across ≤1/≤2/≤3 picks the operating distance; a flat slope
   means distance is exhausted as an axis — spend nothing more on it.
3. **PRUNE ≤3 no-refill (control)** — only if slots 1–2 are ambiguous.
   V1≈V3 ⇒ effect was mass → next session MASS −10% by parent ranking.
   V1≫V3 ⇒ ranking tail has signal → MASS +10% becomes worth a slot.

## Weeks to deadline (default plan, adapted)
- Wk 1–2: PRUNE dose–response (above), then the single most informative of
  MASS ∓10% (needs parent ranking — already required for refill) or SNAP
  (needs TMI/gravity gradient bands supplied).
- Wk 3–4: combine the two best axes, one change at a time from the then-best
  receipt parent; re-verify each parent by exact rebuild before editing.
- Wk 5–6: confirm best file, choose final + fallback blind, re-run
  `src.validate` on both from disk, freeze code + manifest for sponsor
  reproducibility, finish AI_USE.md disclosure.

## Proposed better axes (not built this session)
- **KERNEL-AWARE THINNING**: iteratively drop the dot with the lowest exact
  marginal gain (metric code, catalogue PROXY truth) instead of by field
  rank — mechanism: neighbouring dots cannibalise each other's credit within
  300 m. Confounder: optimises to catalogue, which anti-correlated with live
  before (PROXY ρ −0.87…+0.54). Falsifier: live Δ < 0 vs rank-thinned twin.
- **TIP/STEP-OVER EXTENSION**: add dots only along-strike beyond catalogue
  fault tips and across step-overs (new geometry of existing systems counts
  as truth). Confounder: tips in the catalogue may be real terminations.
  Falsifier: extension dots' share of credit ≈ random far dots in PROXY.
