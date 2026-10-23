# SLOT PLAN — R0 PRUNE collar dose (2026-10-23)

**Agent-selected session axis: PRUNE.** Parent R0 is `h33-h33-2-b2`, 37,654 unit dots. Its `0.2778` live value is a **CLAIM**, not a receipt. Exact R0 rebuild and input hashes are in `evidence/r0_rebuild_receipt.json`; three fixed-count candidates are local under ignored `releases/`. No submission was made. `TOP_PUBLIC`, dated leaderboard target and weekly slots used/remaining are unknown; human confirmation required before allocating any slot.

**Mechanism.** Known-catalogue pixels are masked pixel-exactly; a nearby new fault can still be scored. The PRUNE dose asks whether R0's >2 px catalogue collar is too narrow. At each cutoff, remove all R0 dots at or inside the cutoff and refill the exact count from the H19-5 support, outside the new collar, in its deterministically reconstructed FIFO-BFS d2.8 visit order. That order is a thinning tie-break, not a geological probability. This preserves count and isolates collar radius/refill policy. The candidates all have minimum catalogue distance >3.5 px and zero catalogue mass.

## Next three slots (conditional on human slot count; one entity only)

| Order | Candidate | Prediction (MODEL, not a score) | What its receipt changes |
|---|---|---|---|
| 1 | `h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` | +0.002 DTI; plausible -0.010 to +0.010 | A paired live Δ≥+0.010 supports widening just beyond the 3 px kernel collar. Δ≤-0.010 rejects this cutoff/refill policy. |
| 2 | `h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217.tif` | +0.000 DTI; same plausible interval | Tests a wider exclusion only if slot 1 leaves the PRUNE question unresolved or is positive. If both are within ±0.010, no evidence: do not promote on a proxy. |
| 3 | `h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7.tif` | -0.003 DTI; same plausible interval | Wide-collar counterpoint. A Δ≤-0.010 supports retaining nearby predictions and closes widening; Δ≥+0.010 supports a broader collar. |

**Pre-slot step (required).** The candidate rasters are gitignored and do not survive a clone. On 2026-10-23 they were re-emitted from the pinned inputs byte-identically to their recorded hashes (`evidence/releases_restore_receipt.json`); run `scripts/restore_data.py` then `scripts/restore_releases.py` before any upload and match the SHA-256 to the ledger row.

Under the session rule, **any absolute live change below 0.01 is no evidence**; public-chunk effects may not transfer to private chunks. Predictions are deliberately uncertain. Each comparison should use a human-copied submission receipt for R0 and the candidate, preferably in the same rolling week. Upload at most one candidate per available slot. Use only one encoding per slot; `-zeros.tif` is the fallback twin, not a second experiment.

## Calendar to supplied deadline

Deadline `2026-12-03` and the 3-submissions-per-rolling-week rule are supplied by the brief, not freshly checked (automated access to DrivenData is prohibited). Human must confirm exact cutoff and current quota from the official page/rules: https://www.drivendata.org/competitions/306/competition-doe-gems/ and https://docs.nlr.gov/docs/fy26osti/96647.pdf.

- **Weeks 1–2 (Oct 23–Nov 5):** at most the first candidate if a weekly slot is available; request receipt and date.
- **Weeks 3–4 (Nov 6–19):** consider candidate 2 only if the first receipt is ≥+0.01 or the first result is below the evidence threshold and the collar question remains worth testing.
- **Weeks 5–6 (Nov 20–Dec 3):** candidate 3 only if earlier receipts warrant it; otherwise preserve slots. Choose the final file and fallback blind, then revalidate both. One final submission only.

## Report-only diagnostics

Catalogue hide-and-recover PROXY and SGMC control: **not run**; there is no fold-clean, calibrated instrument validated for this refill comparison, and neither is a gate or score. Leakage canary: report-only, 19 supplied feature bands, all 60,988 known-catalogue positives plus a seeded sample of 250,000 off-catalogue footprint pixels; sentinel values median-filled after masking. Maximum symmetric AUC 0.5700 (`geod_2ndinv`), so no single-feature >0.90 trigger. This canary is not evidence of live performance.

## Better axes proposed only (not built)

- **EDGE_COHERENCE:** require multi-scale linear-gradient persistence to favor fault-like edges. *Confounder:* unfaulted lithologic contacts and drainage scarps are also coherent. *Falsifier:* paired live Δ≤-0.010 or no repeatable improvement on untouched spatial folds.
- **KERNEL_BUDGET:** re-space nearby R0 dots at fixed mass to reduce redundant 300 m kernel coverage. *Confounder:* close parallel strands and step-overs can be real faults. *Falsifier:* paired live Δ≤-0.010.
