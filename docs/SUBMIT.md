# SUBMIT — human checklist

**Nothing is submittable yet.** No variant raster exists (IRREGULARITIES #1).

## 1. Supply inputs (from your own registered account; never commit them)
Place in `data/` (gitignored), then pin hashes:
| file | what |
|---|---|
| `data/sample_submission.tif` | official sample (format reference) |
| `data/h33-h33-2-b2.tif` | R0 exactly as submitted for the 0.2778 CLAIM |
| `data/catalogue_labels.tif` | USGS/INGENIOUS training-label raster on the sample grid |
| `data/preprune_dots.tif` | dot raster before the ≤2 px prune (solo-d28 lineage) |
| `data/ranked_candidates.csv` | `row,col,rank` (1=best): every pre-prune dot + next-best candidates from the parent field |
| `data/metric_code.py` | official DTI code, if available to competitors |

Also paste: R0's submission receipt into `ledger/raw_paste.txt`; TOP_PUBLIC +
date and slots-left into README CURRENT STATE; confirm the 2026-12-03 deadline.

## 2. Build (one command; hard-stops rather than approximating R0)
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.manifest --fill      # pin sha256 of what you supplied
.venv/bin/python -m pytest -q                # algebra + gates on synthetic data
.venv/bin/python -m src.build_prune          # rebuild-check, 3 variants, ledger rows
.venv/bin/python -m src.validate releases/<id>.tif data/sample_submission.tif --catalogue data/catalogue_labels.tif
```
If the rebuild check stops the build, supply the recorded R0 recipe
(distance definition/dot source) — do not hand-edit around it.

## 3. Upload (you, from your account; ONE file per slot — the NaN-outside one)
Order and form notes (≤140 chars) once ids/hashes exist:
1. `<id prunele3>.tif` — "parent h33-h33-2-b2; prune<=3px+refill count-held 37654; predicted +0.000..+0.010 MODEL"
2. `<id prunele1>.tif` — "parent h33-h33-2-b2; prune<=1px count-held (dist-2 ring restored); predicted -0.005..+0.005 MODEL"
3. `<id prunele3nr>.tif` (only if 1–2 ambiguous) — "parent h33-h33-2-b2; prune<=3px no refill control; predicted -0.005..+0.005 MODEL"

Format receipt: recorded per file by `src.build_prune` (validate pass/fail in
ledger status). Paste each live receipt into `ledger/raw_paste.txt` and fill
`receipt_score`/`receipt_date`; treat |Δ| < 0.01 as no evidence.
