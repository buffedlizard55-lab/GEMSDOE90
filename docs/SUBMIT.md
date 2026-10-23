# Human submission packet — GEMSDOE90 PRUNE candidates

**Agent does not submit.** These local GeoTIFFs are ignored by Git to keep competition rasters out of this public repository and any public release. Only pick one candidate per scored slot; do not submit both encodings.

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

## Regenerating the local rasters (do this first on a fresh clone)

`releases/*.tif` is gitignored — this repository is public and competition rasters must not be committed — so the candidate files do **not** travel with the repo. Regenerate them from the pinned inputs, then check the bytes against the recorded hashes:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py          # 26 pins, SHA-256 verified, -> .cache/gems_data/
.venv/bin/python scripts/restore_releases.py      # re-emits the 3 pairs; stops on any hash mismatch
.venv/bin/python scripts/build_r0_variants.py --verify   # independent re-read + re-emit check
.venv/bin/python -m pytest -q                     # 22 tests
```

`scripts/restore_releases.py` reproduces the already-recorded (PRUNE, value) pairs; it is not a new experiment, and it refuses to write a file whose SHA-256 differs from `evidence/build_receipt.json` and `ledger/submissions.csv`. `--build` remains blocked by the (AXIS, value) reservation guard.

| Candidate | n_dots | % of R0 changed | min distance to catalogue | SHA-256 (NaN encoding) |
|---|---|---|---|---|
| PRUNE 3.5 px | 37,654 | 14.352% | 3.606 px | `8b96d8913b97b884…` |
| PRUNE 4.5 px | 37,654 | 25.750% | 5.000 px | `be7a1217907a8019…` |
| PRUNE 5.5 px | 37,654 | 32.560% | 5.657 px | `a69816c73b148933…` |

Full hashes and per-file gate results: `evidence/releases_restore_receipt.json`; the zero-catalogue-mass, in-footprint range/finiteness, CRS/shape/transform/dtype and outside-footprint encoding checks were re-run against the files on disk after writing.
