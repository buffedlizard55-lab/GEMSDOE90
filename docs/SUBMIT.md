# Human submission packet — GEMSDOE90 PRUNE candidates

**Agent does not submit.** These local GeoTIFFs are ignored by Git to keep competition rasters out of this public repository and any public release. Only pick one candidate per scored slot; do not submit both encodings.

On a clean checkout, restore only the three exact pairs already marked `BUILT` in the ledger, then verify them (this does not reserve or create another experiment):

```sh
.venv/bin/python scripts/build_r0_variants.py --restore-recorded
.venv/bin/python scripts/build_r0_variants.py --verify
```

## Files and form notes

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | Form note (under 140 chars) |
|---|---|---|---|
| PRUNE 3.5 px | `releases/h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` | `releases/h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=3.5px, fixed-count refill; predicted +0.002 DTI MODEL` |
| PRUNE 4.5 px | `releases/h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217.tif` | `releases/h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=4.5px, fixed-count refill; predicted +0.000 DTI MODEL` |
| PRUNE 5.5 px | `releases/h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7.tif` | `releases/h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=5.5px, fixed-count refill; predicted -0.003 DTI MODEL` |

SHA-256 and detailed format receipts: `evidence/build_receipt.json`. Parent byte-rebuild receipt: `evidence/r0_rebuild_receipt.json`. Each primary is NaN outside the supplied sample footprint; each `-zeros.tif` fallback has 0 outside. The portal's handling of these encodings is not inferred here; choose the one the human has previously confirmed.

## Validation summary

All three have 37,654 unit-mass pixels (same count as R0), zero catalogue mass, and minimum Euclidean distance to the catalogue greater than 3 px. CRS, dimensions, transform, float32/single band, in-footprint finite/range, outside-footprint encoding, parent diff and file SHA are checked after re-reading from disk. Exact parent R0 hashes and H19-5→d2.8 ranking reproduction are in the receipts. The binary ranking is FIFO-BFS visit order, not a geological confidence score.

No candidate has a live score. Predictions in the ledger are **MODEL**, and R0's 0.2778 remains **CLAIM** until a submission-page receipt is supplied. A live change below 0.01 is no evidence. The human must supply: current TOP_PUBLIC and date; weekly/total slots used and remaining; confirmed deadline/cutoff; and submission-page score receipts (R0 plus any candidate). Never submit more than the entity's quota.
