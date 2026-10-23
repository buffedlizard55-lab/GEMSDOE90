# Human submission packet — GEMSDOE90 high-dose MASS

**The agent does not submit.** These local GeoTIFFs are git-ignored so competition rasters stay out of
this public repository and out of any release. One candidate per scored slot; the `-zeros.tif` twin is a
fallback encoding of the *same* experiment, not a second slot.

Session 2026-10-23c · parent `h33-h33-2-b2` · axis MASS · all candidates are strict subsets of the
byte-identical rebuilt parent: **no additions, no moves, no collar change, zero catalogue mass**.

## Recommended files and form notes

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | Form note (< 140 chars) |
|---|---|---|---|
| `MASSshadow40pct` | `releases/h33-h33-2-b2-MASSshadow40pct-20261023-e2546fbe.tif` | `releases/h33-h33-2-b2-MASSshadow40pct-20261023-e2546fbe-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 40% -> 22592 dots; predicted +0.014 MODEL` |
| `MASSshadow48pct` | `releases/h33-h33-2-b2-MASSshadow48pct-20261023-88a2e8cc.tif` | `releases/h33-h33-2-b2-MASSshadow48pct-20261023-88a2e8cc-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 48% -> 19580 dots; predicted +0.015 MODEL` |
| `MASSrandom40pct` | `releases/h33-h33-2-b2-MASSrandom40pct-20261023-894b5b4a.tif` | `releases/h33-h33-2-b2-MASSrandom40pct-20261023-894b5b4a-zeros.tif` | `h33-h33-2-b2; MASS random-drop 40% -> 22592 dots; predicted +0.013 MODEL` |

Earlier sessions' files remain available locally and unsubmitted (same parent, same gate):
`MASSshadow10/20/30pct` (`e2e518d5` / `c4ce118b` / `9d64151a`) and `PRUNE3p5/4p5/5p5px`
(`8b96d891` / `be7a1217` / `a69816c7`) — see `evidence/mass_build_receipt.json` and
`evidence/build_receipt.json`. **Do not upload anything from the rejected FIFO-order probes** (nothing was
built); see IR90-07.

## Validation summary (re-read from disk after writing)

| Candidate | n_dots | Changed vs R0 | min d_catalogue | Catalogue mass | SHA-256 (NaN encoding) |
|---|---|---|---|---|---|
| `MASSshadow40pct` | 22,592 | 40.0011 % removed (15,062) | 2.236 px (inherited) | 0 | `e2546fbe5b3b…` |
| `MASSshadow48pct` | 19,580 | 48.0002 % removed (18,074) | 2.236 px (inherited) | 0 | `88a2e8cc2588…` |
| `MASSrandom40pct` | 22,592 | 40.0011 % removed (15,062) | 2.236 px (inherited) | 0 | `894b5b4abfdb…` |

Gate results per file: CRS EPSG:32611, shape/transform of `sample_submission.tif`, float32 single band,
all in-footprint values finite and in [0, 1], NaN outside (zeros outside for the twins), exact expected
mask after disk re-read, zero catalogue mass, subset-of-parent with no additions or moves, and the
region-evenness gate (no >100 km² contiguous emptied block). Full hashes, per-file gate booleans and
per-block removal statistics: `evidence/mass_high_dose_receipt.json`.

**Minimum catalogue distance is inherited from R0 (2.236 px, 1,611 dots at < 3 px, IR90-01).** These arms
only delete, so they create no new near-catalogue mass; changing the collar would be a second axis.
Brief §4's ≥ 3 px expectation is therefore not met by the inherited collar — if the human wants a collar-
clean file, use `PRUNE3p5px` instead (min distance 3.606 px).

No candidate has a live score. R0's 0.2778 remains **CLAIM**. A live change below 0.01 is no evidence.

## Regenerating the local rasters (do this first on a fresh clone)

`releases/*.tif` is git-ignored, so the files do **not** travel with the repo. Regenerate from the pinned
inputs and check the bytes against the recorded hashes:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py              # 26 pins, SHA-256 verified -> .cache/gems_data/
.venv/bin/python scripts/build_mass_shadow.py --build # 10/20/30 % -> e2e518d5 / c4ce118b / 9d64151a
.venv/bin/python scripts/build_mass_high_dose.py --build   # 40 / 48 / rand40 -> e2546fbe / 88a2e8cc / 894b5b4a
.venv/bin/python scripts/restore_releases.py          # PRUNE pairs
.venv/bin/python scripts/build_mass_high_dose.py --verify  # independent re-read + byte re-emit
.venv/bin/python scripts/build_r0_variants.py --verify
.venv/bin/python -m pytest -q                         # 41 tests
```

If a rebuild ever prints a SHA-256 that differs from the table above, stop: do not upload it. Every
`(MASS, value)` pair here is reserved in `ledger/experiment_reservations.json`; the build scripts fail
closed on a repeat.

## What the human must supply

1. Current `TOP_PUBLIC` with the date it was read, and the used/remaining weekly slots.
2. Confirmation of the 2026-12-03 deadline and the 3-scored-submissions rule from the competition page.
3. Submission-page receipts (score + date) for R0 and for each candidate, entered into the
   `receipt_score` / `date` columns of `ledger/submissions.csv`.
4. A decision on whether the final submission may repeat an already-scored file; that changes the week-6
   plan in `SLOT_PLAN.md`.
