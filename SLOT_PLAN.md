# SLOT_PLAN.md

**Status: PLAN ONLY — nothing confirmed.** R0 has not been rebuilt (see
IRREGULARITIES.md item 1). No file here is a commitment until the parent's sha256 is
recorded in `ledger/submissions.csv`. The axis is still TBD: the brief says "pick your
own session", so no session axis has been committed to either.

## Required inputs to unblock (exact list)
1. `sample_submission.tif` (CRS/shape/transform/dtype/band count; the format gate).
2. The fault catalogue used to build R0 (to enforce zero catalogue mass + 3 px).
3. The R0 generation script + ranking output, OR the R0 `.tif` itself to match sha256.
4. `registry/data_manifest.json` with sha256 for every input.
5. TOP_PUBLIC + the current week's slot count (human-entered from the leaderboard).

## Default weekly plan (shifted by the unblock delay)
- **wk1–2:** MASS → CONCENTRATION → SNAP → PRUNE → RELIEF (one change per slot, each a
  controlled edit of R0). START at MASS.
- **wk3–4:** combine the two best axes into one variant (predicted sign + size; live
  change < 0.01 ⇒ no evidence).
- **wk5–6:** confirm the leader, choose the final file + a fallback, re-validate the
  format of both against `sample_submission.tif`, and prepare TRACKB evidence only if
  the human elects it for Phase 2.

## Next 3 slots in order (once unblocked)
1. **R0 rebuild + hash match** — not a scored slot; gates everything. If sha256 does not
   match, stop.
2. **MASS-down10** — drop R0's lowest-ranked 10% by its own ranking.
   What a win would change: confirms the parent's ranking is carrying signal rather than
   the count, and frees 3.8k slots to be spent on CONCENTRATION next.
3. **CONCENTRATION-up10** — move 10–20% of dots from the lowest-prior km-scale blocks to
   the highest-prior ones; report block-density CV before/after (target band 0.51–0.59).
   What a win would change: makes the next SNAP/RELIEF slot a pure geometry question.

## Proposed better axes (PROPOSED ONLY — not built this session)
- **AXIS: LINEARITY** — replace ~20% of dots with strike-consistent runs ≥ 1 km drawn from
  R0's top-ranked dots. Mechanism: the metric's algebra note says line-like truth lowers
  the credit bar (≈ 0.056 at 0.28 for an isolated pixel), so collinear dot runs should pay
  on more truth pixels per dot. Confounder: dot clustering mimics linearity. Falsifier:
  live change < 0.01; also fails if the run alignment is an artifact of the catalogue.
- **AXIS: CATALOGUE-FRINGE** — place new mass in the 3-px annulus beside known catalogue
  traces, since the organizers state new-fault truth can lie within 300 m of known traces
  and the pixels beside known pixels are scored normally. Mechanism: a systematic offset
  toward likely new mapping of existing systems. Confounder: looks identical to simply
  being sloppy about the catalogue mask. Falsifier: a live change no larger than R0's
  own noise floor.
- **AXIS: KERNEL-FRINGE / PROXIMITY-SHARPEN** — emphasize the 100–200 m band around
  high-prior dots, betting that a thin field beats a diffuse one at the same count.
  Confounder: confounded with MASS (fewer, sharper dots). Falsifier: live change < 0.01
  or a collapse below R0.

## Evidence labels
RECEIPT | CLAIM | PROXY | MODEL — a PROXY/MODEL is never a score.
