# Human submission packet — GEMSDOE90 (MASS session 2026-10-23; PRUNE candidates retained)

**Agent does not submit.** Local GeoTIFFs are ignored by Git to keep competition rasters out of this public repository and any public release. Only pick one candidate per scored slot; do not submit both encodings of a file. A live change under 0.01 is no evidence; public-chunk effects need not transfer to private chunks.

## This session — AXIS=MASS dose-ladder rungs (new)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | Form note (under 140 chars) |
|---|---|---|---|
| MASS drop5pct-tail | `releases/h33-h33-2-b2-MASSdrop5pct-tail-20261023-ce48329b.tif` | `releases/h33-h33-2-b2-MASSdrop5pct-tail-20261023-ce48329b-zeros.tif` | `h33-h33-2-b2; MASS drop5pct-tail (n=35771); predicted -0.002 DTI MODEL` |
| MASS add5pct-next | `releases/h33-h33-2-b2-MASSadd5pct-next-20261023-46f0886b.tif` | `releases/h33-h33-2-b2-MASSadd5pct-next-20261023-46f0886b-zeros.tif` | `h33-h33-2-b2; MASS add5pct-next (n=39537); predicted -0.002 DTI MODEL` |
| MASS add20pct-next | `releases/h33-h33-2-b2-MASSadd20pct-next-20261023-63954e89.tif` | `releases/h33-h33-2-b2-MASSadd20pct-next-20261023-63954e89-zeros.tif` | `h33-h33-2-b2; MASS add20pct-next (n=45185); predicted -0.008 DTI MODEL` |

Recipe: count-only edits along the parent's own recorded ranking (H19-5 8-connected FIFO-BFS traversal). `drop5pct-tail` removes the 1,883 lowest-ranked (traversal-tail) parent dots. `add5pct-next` / `add20pct-next` add the 1,883 / 7,531 next-ranked suppressed H19-5 support cells (d_cat ≥ 3 px; 99.5–99.6 % of them sit within 2.8 px of an existing parent dot). Zero catalogue mass in all files; placed dots keep the ≥3 px floor; inherited parent dots keep the parent's recorded ≥2 px collar (IR90-01/IR90-06). Predictions are **MODEL**; the human fills `receipt_score`/`date` in `ledger/submissions.csv`.

## Prior session — AXIS=PRUNE collar dose (unchanged ledger rows)

The three PRUNE rasters were rebuilt byte-identically into `releases/` by `scripts/regen_prune_rasters.py` (hashes match `ledger/submissions.csv`). Submit at most one encoding per slot.

| Candidate | Preferred file | Fallback twin | Form note |
|---|---|---|---|
| PRUNE 3.5 px | `releases/h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` | `releases/h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=3.5px, fixed-count refill; predicted +0.002 DTI MODEL` |
| PRUNE 4.5 px | `releases/h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217.tif` | `releases/h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=4.5px, fixed-count refill; predicted +0.000 DTI MODEL` |
| PRUNE 5.5 px | `releases/h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7.tif` | `releases/h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=5.5px, fixed-count refill; predicted -0.003 DTI MODEL` |

## Format receipt (both sessions)

All files: float32, 1 band, CRS/transform/shape of `sample_submission.tif`, values in [0,1], finite inside the footprint, NaN (or 0 in the `-zeros` twin) outside, zero catalogue mass. SHA-256 and per-file check receipts: `evidence/mass_build_receipt.json` (MASS) and `evidence/build_receipt.json` (PRUNE). Parent byte-rebuild receipt: `evidence/r0_rebuild_receipt.json`. The portal's handling of NaN-vs-zeros encodings is not inferred here; use the encoding the human has previously confirmed.

No candidate has a live score. R0's `0.2778` stays **CLAIM** until a submission-page receipt is in the ledger. The human must supply: current TOP_PUBLIC and date; weekly/total slots used and remaining; confirmed deadline/cutoff; and submission-page receipts (R0 plus any candidate). Never submit more than the entity's quota (3 scored / rolling week, one final file). Cross-session note: parallel sessions GEMSDOE84-92 built further PRUNE/MASS/SNAP/CONCENTRATION/RELIEF/SPACING candidates; coordinate slot order across ledgers so no (parent, axis, value) pair or exact hash is submitted twice.
