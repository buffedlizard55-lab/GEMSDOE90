# SUBMIT.md

Placeholder — no submission has been prepared this session (R0 could not be rebuilt).

## When a variant is ready
- **File:** `releases/<id>.tif` (NaN outside footprint, float32, EPSG:32611, 100 m, one
  band, values in [0,1]). Fallback twin: `releases/<id>-zeros.tif`.
- **Name:** `<parent>-<axis><value>-<yyyymmdd>-<sha8>` (<=140 chars).
- **Note (<=140 chars):** parent; change; predicted change.
- **Format receipt:** re-read the file from disk, re-run the validator (CRS, shape,
  transform, dtype, band count, values in [0,1], no NaN inside the footprint, NaN
  outside, zero catalogue mass). Record the sha256 in `ledger/submissions.csv` with
  status BUILT; the human fills `receipt_score` and `date` from the submission page.
- The human submits from their own registered account. This agent never submits.
