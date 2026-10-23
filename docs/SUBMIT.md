# Human submission packet — GEMSDOE90 MASS candidates (2026-10-23)

**The agent does not submit.** These GeoTIFFs are gitignored (this repo is public; competition rasters must
never be committed). Pick ONE file per scored slot; never upload both encodings of the same id.

## Files, names and notes

| # | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | n_dots | Form note (≤140 chars) |
|---|---|---|---|---|
| 1 | `releases/h33-h33-2-b2-MASSuniq20-20261023-5138de0f.tif` | `…-5138de0f-zeros.tif` | 28,512 | `h33-h33-2-b2; MASS uniq20: drop 7,531 least-unique-credit dots + 3px collar; pred +0.005 DTI MODEL` |
| 2 | `releases/h33-h33-2-b2-MASSuniq30-20261023-56c5f82f.tif` | `…-56c5f82f-zeros.tif` | 24,747 | `h33-h33-2-b2; MASS uniq30: drop 11,296 least-unique-credit dots + 3px collar; pred +0.007 DTI MODEL` |
| 3 | `releases/h33-h33-2-b2-MASSfifo20-20261023-1be8302f.tif` | `…-1be8302f-zeros.tif` | 28,512 | `h33-h33-2-b2; MASS fifo20: drop 7,531 lowest-FIFO-rank dots + 3px collar; pred +0.001 DTI MODEL` |

Full SHA-256, per-file gate results and parent-diff statistics: `evidence/build_receipt_mass.json`.
Format receipts for the two earlier PRUNE candidates: `evidence/build_receipt.json`.

## Gates re-run after writing (all pass, both encodings of all three files)

CRS EPSG:32611, shape 3730×3292, transform, float32, single band, values in [0,1], no NaN inside the 5,167,373-px
footprint, NaN outside (primary) / 0 outside (twin), **zero catalogue mass**, **minimum Euclidean distance to the
catalogue 3.000 px**, expected mask re-derived and compared after re-reading from disk, SHA-256 not present in any
other ledger row, and no repeated `(parent, axis, value)` pair.

## Regenerate on a fresh clone (do this before any upload)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py            # 26 pins, SHA-256 verified -> .cache/gems_data/
.venv/bin/python scripts/build_mass_variants.py --build    # re-emits and records hashes
.venv/bin/python scripts/build_mass_variants.py --verify   # re-derives masks, compares on-disk bytes
.venv/bin/python scripts/write_mass_ledger.py              # refreshes the 3 MASS ledger rows
.venv/bin/python -m pytest -q                              # 30 tests
```

The build is deterministic: re-running it must print the same SHA-256 values as the ledger. Confirm the SHA-256
on disk equals the ledger row before uploading. `-zeros.tif` twins are byte-stable under the same command.

## What the human must supply

Current TOP_PUBLIC with date; weekly/total slots used and remaining; confirmed deadline/cutoff; and
submission-page **receipts** for R0 and for each candidate (paste score + date into `ledger/submissions.csv`
`receipt_score` / `date`, and set `receipt` to Y). R0's 0.2778 remains a **CLAIM** until then. A live change
below 0.01 is no evidence.
