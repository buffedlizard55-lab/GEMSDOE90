# docs/SUBMIT.md — what the human uploads
# Gate: format receipt from submission page must be pasted into ledger/submissions.csv receipt_score

## Current variant set (2026-10-23, AXIS=CONCENTRATION, SYNTHETIC — DO NOT SUBMIT)
All three files below are **SYNTHETIC stand-ins** (see IRREGULARITIES.md). They exist to prove the validator/ledger/release pipeline, not to score. For a real submission, rebuild against the true `sample_submission.tif` footprint and catalogue, then fill this table.

| File (releases/) | Upload name | Form note (≤140 ch) | sha8 | n_dots | % changed | Predicted Δ | Format receipt |
|---|---|---|---|---|---|---|---|
| `h33-h33-2-b2-CONC10-20261023-41a772a7.tif` | `h33-h33-2-b2-CONC10-20261023-41a772a7` | Parent h33-h33-2-b2; CONC 10% low→high 1km blocks CV1.20→2.97; pred +0.001 | 41a772a7 | 37654 | 10.0 | +0.001 MODEL | ☐ |
| `h33-h33-2-b2-CONC15-20261023-e81f5ae6.tif` | `h33-h33-2-b2-CONC15-20261023-e81f5ae6` | Parent h33-h33-2-b2; CONC 15% low→high 1km blocks CV1.20→3.64; pred +0.002 | e81f5ae6 | 37654 | 15.0 | +0.002 MODEL | ☐ |
| `h33-h33-2-b2-CONC20-20261023-a1d6a0ce.tif` | `h33-h33-2-b2-CONC20-20261023-a1d6a0ce` | Parent h33-h33-2-b2; CONC 20% low→high 1km blocks CV1.20→4.16; pred +0.003 | a1d6a0ce | 37654 | 20.0 | +0.003 MODEL | ☐ |

## Fallback zeros variant
Each has a `-zeros.tif` twin (0 outside footprint vs NaN). Competition spec requires **NaN outside**; zeros file is fallback only if uploader rejects NaN. Human uploads **only one per slot**.

## How to validate before uploading (MUST pass)
```bash
python3 scripts/validate.py releases/<id>.tif <path/to/sample_submission.tif> <path/to/catalogue_mask.tif>
# Expect: PASS CRS, shape, transform, dtype, values [0,1], no NaN inside, NaN outside, zero catalogue mass, re-read match
# Also: sha256 not in ledger/submissions.csv
```

## After scoring
Copy receipt score into `ledger/submissions.csv` columns `receipt_score` + `receipt_date`, commit, and update README CURRENT STATE.
