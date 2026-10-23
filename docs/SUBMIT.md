# Human submission packet — GEMSDOE90 candidates (SNAP 2026-10-23, PRUNE 2026-10-23)

**Agent does not submit.** These GeoTIFFs are gitignored to keep competition rasters out of this public repository and any public release. Pick **one file per scored slot**; never upload both encodings of the same candidate, and never exceed the entity's 3-per-rolling-week quota.

## This session: SNAP (cross-strike, cap 2 px)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | Form note (≤140 chars) |
|---|---|---|---|
| strict ε×4 | `releases/h33-h33-2-b2-SNAPXk4p0-20261023-3dd81141.tif` | `releases/h33-h33-2-b2-SNAPXk4p0-20261023-3dd81141-zeros.tif` | `h33-h33-2-b2; SNAP cross-strike cap 2px, eps x4 (TMI+grav hg consensus); pred +0.004 DTI MODEL` |
| standard ε×1 | `releases/h33-h33-2-b2-SNAPXk1p0-20261023-c2dcf0b5.tif` | `releases/h33-h33-2-b2-SNAPXk1p0-20261023-c2dcf0b5-zeros.tif` | `h33-h33-2-b2; SNAP cross-strike cap 2px, eps x1 (TMI+grav hg consensus); pred +0.003 DTI MODEL` |
| permissive ε×0.25 | `releases/h33-h33-2-b2-SNAPXk0p25-20261023-7ac0b578.tif` | `releases/h33-h33-2-b2-SNAPXk0p25-20261023-7ac0b578-zeros.tif` | `h33-h33-2-b2; SNAP cross-strike cap 2px, eps x0.25 (TMI+grav hg consensus); pred +0.001 DTI MODEL` |

## Previous session: PRUNE (collar), still valid

| Candidate | Preferred file (NaN outside) | Fallback twin (zeros outside) | Form note (≤140 chars) |
|---|---|---|---|
| PRUNE 3.5 px | `releases/h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` | `releases/h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=3.5px, fixed-count refill; predicted +0.002 DTI MODEL` |
| PRUNE 4.5 px | `releases/h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217.tif` | `releases/h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=4.5px, fixed-count refill; predicted +0.000 DTI MODEL` |
| PRUNE 5.5 px | `releases/h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7.tif` | `releases/h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7-zeros.tif` | `h33-h33-2-b2; PRUNE dcat<=5.5px, fixed-count refill; predicted -0.003 DTI MODEL` |

## Validation summary (all six pairs, re-run after writing and after re-reading from disk)

| Candidate | n_dots | % of R0 changed | min distance to catalogue | mean displacement | SHA-256 (NaN encoding) |
|---|---|---|---|---|---|
| SNAPXk4p0 | 37,654 | 71.04 % (SNAP is exempt from the 1–50 % rule) | 3.000 px | 2.00 px | `3dd8114149d70a42…` |
| SNAPXk1p0 | 37,654 | 113.48 % | 3.000 px | 2.00 px | `c2dcf0b592162caa…` |
| SNAPXk0p25 | 37,654 | 125.68 % | 3.000 px | 2.00 px | `7ac0b578271d1479…` |
| PRUNE 3.5 px | 37,654 | 14.35 % | 3.606 px | — | `8b96d8913b97b884…` |
| PRUNE 4.5 px | 37,654 | 25.75 % | 5.000 px | — | `be7a1217907a8019…` |
| PRUNE 5.5 px | 37,654 | 32.56 % | 5.657 px | — | `a69816c73b148933…` |

Every pair passes: CRS EPSG:32611, shape/transform equal to `sample_submission.tif`, float32, one band, values in [0,1], finite inside the footprint, NaN (primary) or zero (fallback) outside it, zero mass on catalogue pixels, ≥3 px from the catalogue, exact 37,654 dots, file re-read from disk, parent-diff statistics recorded, SHA-256 absent from every other ledger row. Full per-file gate results: `evidence/snap_build_receipt.json` and `evidence/build_receipt.json`. Regeneration receipts: `evidence/releases_restore_receipt.json`.

## Regenerate on a fresh clone (do this before uploading)

`releases/*.tif` is gitignored, so the files do **not** travel with the repository:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py              # 26 pins, SHA-256 verified -> .cache/gems_data/
.venv/bin/python scripts/restore_releases.py           # re-emits the 3 PRUNE pairs, fails closed on any hash mismatch
.venv/bin/python scripts/build_snap_variants.py --verify   # re-emits + re-reads the 3 SNAP pairs
.venv/bin/python -m pytest -q                          # 33 tests
```

Then confirm the SHA-256 on disk equals the ledger row before upload:

```bash
sha256sum releases/h33-h33-2-b2-SNAPXk4p0-20261023-3dd81141.tif
```

## What is NOT claimed

No candidate has a live score. The R0 `0.2778` is a **CLAIM** (owner-reported, no receipt). Predictions are **MODEL**, never scores. A live change below 0.01 is no evidence. The human must supply: current `TOP_PUBLIC` with date; weekly/total slots used and remaining; confirmed deadline/cutoff; the R0 receipt from portal history (no slot needed); and a fresh receipt for each candidate submitted.
