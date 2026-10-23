# Human submission packet — fixed-count A5 along-strike PRUNE (2026-10-23)

**Agent never submits.** Human uploads from the registered account, ONE file per scored slot. NaN-outside is primary; `-zeros.tif` is only a fallback encoding of the same experiment. R0's 0.2778 remains **CLAIM** until a portal receipt is entered.

| Candidate | Primary file in `releases/` | Fallback | Form note (<=140 chars) |
|---|---|---|---|
| **A5/L1 — first choice** | `h33-h33-2-b2-PRUNEanisoA5L1-20261023-cd2c60ce.tif` | `h33-h33-2-b2-PRUNEanisoA5L1-20261023-cd2c60ce-zeros.tif` | `h33-h33-2-b2; PRUNE A5/L1, fixed-count refill; pred +0.005 DTI MODEL` |
| A5/L1.5 | `h33-h33-2-b2-PRUNEanisoA5L1p5-20261023-9486c7e6.tif` | `h33-h33-2-b2-PRUNEanisoA5L1p5-20261023-9486c7e6-zeros.tif` | `h33-h33-2-b2; PRUNE A5/L1.5, fixed-count refill; pred +0.004 DTI MODEL` |
| A5/L0.5 | `h33-h33-2-b2-PRUNEanisoA5L0p5-20261023-91ff3771.tif` | `h33-h33-2-b2-PRUNEanisoA5L0p5-20261023-91ff3771-zeros.tif` | `h33-h33-2-b2; PRUNE A5/L0.5, fixed-count refill; pred +0.003 DTI MODEL` |

**Format receipt:** `evidence/aniso_along_refill_receipt.json` (full SHA-256, parent diffs, PROXY CIs, and `self_check`). Every pair is float32, one band, EPSG:32611, sample shape/transform, finite [0,1] inside, NaN/0 outside as named, 37,654 dots, zero catalogue mass, `d_cat>2 px`, re-read from disk and byte-re-emitted. Ledger rows are BUILT and unscored.

Restore and independently check (competition rasters stay Git-ignored):

```bash
.venv/bin/python scripts/restore_data.py
.venv/bin/python scripts/build_aniso_prune_along.py --build   # re-emit if absent
.venv/bin/python scripts/build_aniso_prune_along.py --verify
.venv/bin/python -m src.validate releases/<file>.tif .cache/gems_data/sample_submission.tif \
  --catalogue .cache/gems_data/existing_faults.tif            # add --zeros-outside for fallback
```

**Do not upload:** `PRUNEanisoA4L2nr`, `PRUNEanisoA5L2nr`, or `PRUNEanisoA6L2nr` (IR90-22 WITHDRAWN: delete-only violated the fixed-count PRUNE recipe); any FIFO-ranked MASS rung marked WITHDRAWN; both encodings in separate slots.

Before upload, human supplies: dated `TOP_PUBLIC`; slots used/remaining and total; deadline confirmation; R0 and candidate submission-page scores/dates; hash-repeat check; data-use review; geological review of retained mapped-tip continuations and refill ridges. After upload, copy the receipt score/date into `ledger/submissions.csv`—a local PROXY or MODEL is never a score.
