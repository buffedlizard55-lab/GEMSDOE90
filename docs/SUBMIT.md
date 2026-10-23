# Human submission packet — GEMSDOE90 candidates (`AXIS=RELIEF` + prior `PRUNE`)

**Agent never submits.** GeoTIFFs in `releases/` are gitignored so competition-derived rasters never enter this public repository or any GitHub release. Upload **at most one encoding per scored slot** (prefer the NaN-outside `.tif`; `-zeros.tif` is a fallback twin, never a second experiment).

## Current session candidates (`AXIS=RELIEF`, 2026-10-23)

| Variant | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | Submission name | Form note (`<=140` chars) |
|---|---|---|---|---|
| **RELIEF 12.5% Range→Piedmont** | `releases/h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f.tif` | `releases/h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f-zeros.tif` | `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f` | `h33-h33-2-b2; RELIEF 12.5% (4707d) range->piedmont; pred +0.004 DTI MODEL` |
| **RELIEF 10.0% Range→Basin** | `releases/h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17.tif` | `releases/h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17-zeros.tif` | `h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17` | `h33-h33-2-b2; RELIEF 10% (3766d) range->basin; pred +0.003 DTI MODEL` |
| **RELIEF 15.0% Piedmont→Range** | `releases/h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f.tif` | `releases/h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f-zeros.tif` | `h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f` | `h33-h33-2-b2; RELIEF 15% (5648d) piedmont->range; pred -0.004 DTI MODEL` |

### Format & gate receipt (`evidence/relief_build_receipt.json`)

Every file was re-read from disk after writing and passed `src/validate.py` plus parent-diff checks against `sample_submission.tif` (`EPSG:32611`, `3730×3292`, identical affine transform, `float32`, 1 band, finite `[0, 1]` inside the 5,167,373-px footprint, `NaN` outside on primary / `0.0` outside on `-zeros.tif`, `0.0` catalogue mass, `d_cat >= 3.0 px` on 100% of newly added dots, unique SHA-256 across the ledger):

| Submission name | `n_dots` | Mass shifted | `% changed` (`|C ^ R0| / |R0|`) | Added min `d_cat` | SHA-256 (NaN primary) | SHA-256 (`-zeros` fallback) |
|---|---:|---:|---:|---:|---|---|
| `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f` | 37,654 | 12.501% (4,707d) | 25.001% | 3.000 px | `5e64d01f26b6687f69751785cf21063b441609282c5267345074c4ca495e5065` | `c50e5a8b98b0f6c3ccc987f41b656a990a5ee6c0deef0a60cb6dda038d23aefc` |
| `h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17` | 37,654 | 10.002% (3,766d) | 20.003% | 3.000 px | `9e7b5e17ad3b27ddd3164a77ce89c22e77fe1d72891d8e8be9a7f9746adf9f06` | `870a92b2cfb98c786309b5fe73078648b8c58c478e93f24e2b29524ae885ad2a` |
| `h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f` | 37,654 | 15.000% (5,648d) | 29.999% | 3.000 px | `ad95e30f857011f9f8580053bbb60abdba46bc5046aeaafd996e09ff920749b3` | `66d1abb217ce9cfba3a45aab0ba44fbb64f8957319163999923e1403cb967db6` |

## Prior session candidates retained on `main` (`AXIS=PRUNE`, `evidence/build_receipt.json`)

| Candidate | Preferred file (NaN outside) | `% changed` | Min `d_cat` | SHA-256 (NaN primary) | Form note (`<=140` chars) |
|---|---|---:|---:|---|---|
| PRUNE 3.5 px | `releases/h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` | 14.352% | 3.606 px | `8b96d8913b97b884…` | `h33-h33-2-b2; PRUNE dcat<=3.5px, fixed-count refill; predicted +0.002 DTI MODEL` |
| PRUNE 4.5 px | `releases/h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217.tif` | 25.750% | 5.000 px | `be7a1217907a8019…` | `h33-h33-2-b2; PRUNE dcat<=4.5px, fixed-count refill; predicted +0.000 DTI MODEL` |
| PRUNE 5.5 px | `releases/h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7.tif` | 32.560% | 5.657 px | `a69816c73b148933…` | `h33-h33-2-b2; PRUNE dcat<=5.5px, fixed-count refill; predicted -0.003 DTI MODEL` |

## Regenerating and verifying all local rasters on a fresh clone

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py                  # restores & SHA-256 verifies all 26 pinned inputs
.venv/bin/python scripts/restore_releases.py              # re-emits all 6 candidate pairs (PRUNE + RELIEF) & verifies SHA-256
.venv/bin/python scripts/build_relief_variants.py --verify
.venv/bin/python -m pytest -q                             # 29 unit & ledger-integrity tests
```

## Human inputs required before any upload

1. Dated `TOP_PUBLIC` from the official leaderboard (agent never accesses DrivenData).
2. Weekly and cumulative scored slots used/remaining for the single registered entity, plus official deadline confirmation (`2026-12-03` UNVERIFIED).
3. Submission-page receipt for parent R0 (`0.2778` is currently `CLAIM`) and for each uploaded candidate (`receipt_score` + `date` in `ledger/submissions.csv`).
