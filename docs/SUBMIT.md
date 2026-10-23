# Human submission packet — strike-aligned PRUNE collar (2026-10-23)

**The agent does not submit and cannot see the leaderboard.** These GeoTIFFs are local and Git-ignored on
purpose: this repository is public and competition rasters must not be committed or released
(`IRREGULARITIES.md` #2). Only the human uploads, from their own account, one file per scored slot.

## Files, names and notes

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | Form note (< 140 chars) |
|---|---|---|---|
| A4 | `releases/h33-h33-2-b2-PRUNEanisoA4L2-20261023-0bf248e2.tif` | `...-0bf248e2-zeros.tif` | `h33-h33-2-b2; PRUNE strike-aligned collar across<=4px along<=2px, fixed-count refill; predicted +0.003 DTI MODEL` |
| A5 | `releases/h33-h33-2-b2-PRUNEanisoA5L2-20261023-15218061.tif` | `...-15218061-zeros.tif` | `h33-h33-2-b2; PRUNE strike-aligned collar across<=5px along<=2px, fixed-count refill; predicted +0.002 DTI MODEL` |
| A6 | `releases/h33-h33-2-b2-PRUNEanisoA6L2-20261023-72dcdbd3.tif` | `...-72dcdbd3-zeros.tif` | `h33-h33-2-b2; PRUNE strike-aligned collar across<=6px along<=2px, fixed-count refill; predicted +0.000 DTI MODEL` |

Upload **one encoding per slot**; the `-zeros` twin is the fallback for a portal that rejects NaN outside the
footprint, not a second experiment. Same dots inside the footprint, byte-different only outside.

## Format receipt (re-read from disk after writing)

| File | dots | catalogue mass | CRS / shape / transform | dtype / bands | inside footprint | outside footprint | gate |
|---|---|---|---|---|---|---|---|
| A4 NaN | 37,654 | 0.0 | EPSG:32611, matches `sample_submission.tif` | float32, 1 band | finite, ∈ [0,1] | NaN | **PASS** |
| A4 zeros | 37,654 | 0.0 | idem | idem | idem | 0 | **PASS** |
| A5 NaN / zeros | 37,654 | 0.0 | idem | idem | idem | NaN / 0 | **PASS** |
| A6 NaN / zeros | 37,654 | 0.0 | idem | idem | idem | NaN / 0 | **PASS** |

Independent re-check command (exit 0 = pass):

```
.venv/bin/python -m src.validate releases/<file>.tif .cache/gems_data/sample_submission.tif \
    --catalogue .cache/gems_data/existing_faults.tif [--zeros-outside]
```

Full hashes, parent-diff statistics, collar diagnostics and the refill-redundancy numbers are in
`evidence/build_aniso_receipt.json`; the exact-R0 proof is `evidence/r0_rebuild_receipt.json`;
mechanism cards are in `docs/MECHANISM_CARDS.md` and `ledger/mechanism_cards.json`.

## Before uploading, the human must supply

1. `TOP_PUBLIC` **with a date**, read from the leaderboard on the day (never from this repository).
2. Weekly slots used / remaining for the entity, and confirmation of the `2026-12-03` deadline and cutoff.
3. Submission-page **receipts** (score + date) for R0 and for any candidate — until then R0's 0.2778 is a
   **CLAIM** and every prediction here is a **MODEL**.
4. Confirmation that the chosen sha256 has not been submitted before (at least 8 historical slots were repeats).
5. A decision on data-use terms before any of these rasters leave the private workspace.

The previous session's isotropic files (`...PRUNE3p5px...`, `4p5px`, `5p5px`) are still available locally; they
are untouched and unscored. `SLOT_PLAN.md` explains why the anisotropic rungs now come first.
