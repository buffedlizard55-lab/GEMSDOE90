# GEMSDOE90 — GEMS Prize (DrivenData #306) ONE-entity harness

## CURRENT STATE (edit only this block per brief §7)
- **Parent R0:** `h33-h33-2-b2` (GEMSDOE32) — 37,654 unit-mass dots, none within 2px of catalogue, rebuilt 2026-10-23 sha256 `01bbbb5bbd1ff605e05f922f573767bf040716eaca70a99fdca17380b565f075` (claim 0.2778 = CLAIM, receipt pending). Validator: PASS (EPSG:32611, 2500×2068, 100m, NaN outside).
- **Best receipt:** *none yet* — parent 0.2778 is CLAIM (owner-reported, no receipt). Best built variant not yet scored live; predicted deltas MODEL only (see below).
- **TOP_PUBLIC:** ____ (human fills from leaderboard with date per brief §1) — no target other than leaderboard.
- **Slots left this week:** __ /3 (human fills) — deadline 2026-12-03 confirm on competition page; 1 final blind file.
- **Next 3 slots (from SLOT_PLAN.md):**
  1. MASS M-10/M+10 (test ranking threshold; S=33888 vs 41419)
  2. CONCENTRATION follow-up 2000M 7PCT vs 5000M 12PCT based on live result of this session
  3. PRUNE 1px vs 3px buffer (refill to hold count)
- **This session AXIS:** CONCENTRATION — 3 variants built, validated, ledger updated (see releases/).
- **Last validator run:** 2026-10-23 all 4 rasters PASS (re-read from disk).

## What this repo does
Controlled edits from a named parent per brief v2: one change, predicted outcome, own result end-to-end. Reproducible raster generation from pinned inputs (registry/data_manifest.json), fixed seed 20261022, logged git SHA.

## Quickstart
```bash
pip install -r requirements.txt  # rasterio, numpy, scipy, shapely, scikit-learn
python src/make_parent.py        # rebuild R0, check sha256
python src/make_variants_concentration.py  # build 3 CONC variants
python src/validate.py releases/<id>.tif --parent  # MUST-pass gates
```

## Layout
- `registry/data_manifest.json` — pinned inputs with sha256
- `data/` — sample_submission.tif mirror + synthetic catalogue/footprint/score (UNVERIFIED-SYNTHETIC)
- `src/` — config, dti, ranking, validate, make_parent/variants
- `releases/` — `<parent>-<axis><value>-<yyyymmdd>-<sha8>.tif` (NaN outside) + `-zeros.tif` fallback
- `ledger/submissions.csv` — one row per variant; `ledger/raw_paste.txt` collapsed repeats
- `docs/SUBMIT.md` — file/name/note/format receipt for human upload
- `SLOT_PLAN.md` — next 3 slots + weeks to deadline
- `IRREGULARITIES.md` — only items that change a decision
- `AI_USE.md` — AI disclosure per rules

## Scores
Never call PROXY or MODEL a score. All external facts carry URL. Live score is private chunks + expert-expanded labels (Phase 2 rescore).

## Constraints
Never contact dropbox.com, never fetch drivendata.org pages (ToU ban), never scrape leaderboard or submit via code. Human submits from own account. Competition rasters not pushed to public releases.

See `docs/SUBMIT.md` for current upload candidate.
