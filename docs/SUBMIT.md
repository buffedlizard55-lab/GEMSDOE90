# Human submission packet — 2026-10-23 sessions (MASS ladder incl. high doses + both PRUNE collars)

**The agent does not submit and cannot see the leaderboard.** Every GeoTIFF below is local and Git-ignored on
purpose: this repository is public and competition rasters must not be committed or released
(`IRREGULARITIES.md` IR90-02). Only the human uploads, from their own account, **one file per scored slot**.
The `-zeros.tif` twin is a fallback encoding of the *same* experiment, not a second slot.

Parent for everything here: `h33-h33-2-b2` (R0), 37,654 unit-mass dots, CLAIM 0.2778 with no receipt on file.
`SLOT_PLAN.md` gives the order and the decision rule; this file is the upload mechanics.

## 1. MASS shadow-dose ladder (session 2026-10-23b, nested)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin | Form note (< 140 chars) |
|---|---|---|---|
| 10 % → 33,889 dots | `releases/h33-h33-2-b2-MASSshadow10pct-20261023-e2e518d5.tif` | `…-e2e518d5-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 10% -> 33889 dots; predicted +0.005 MODEL` |
| 20 % → 30,123 dots | `releases/h33-h33-2-b2-MASSshadow20pct-20261023-c4ce118b.tif` | `…-c4ce118b-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 20% -> 30123 dots; predicted +0.009 MODEL` |
| 30 % → 26,358 dots | `releases/h33-h33-2-b2-MASSshadow30pct-20261023-9d64151a.tif` | `…-9d64151a-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 30% -> 26358 dots; predicted +0.012 MODEL` |

Each file is a strict subset of R0 — no additions, no moves, 10.00 / 20.00 / 30.00 % of R0 removed, zero
catalogue mass. **These three rasters are not present in this sandbox** (they were built in the MASS session and
`releases/` is gitignored): re-emit them with `.venv/bin/python scripts/build_mass_shadow.py --build` after
`scripts/restore_data.py`, and confirm the SHA-256 against `evidence/mass_build_receipt.json` before uploading. SHA-256, checks and parent-diff statistics: `evidence/mass_build_receipt.json`; re-run with
`.venv/bin/python scripts/build_mass_shadow.py --verify`. These files inherit R0's 2.236 px collar exactly
(IR90-07): a MASS-only edit must not also move the collar.

## 1b. MASS high-dose arms + credit-blind control (session 2026-10-23c)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin | Form note (< 140 chars) |
|---|---|---|---|
| 40 % → 22,592 dots | `releases/h33-h33-2-b2-MASSshadow40pct-20261023-e2546fbe.tif` | `…-e2546fbe-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 40% -> 22592 dots; predicted +0.014 MODEL` |
| 48 % → 19,580 dots | `releases/h33-h33-2-b2-MASSshadow48pct-20261023-88a2e8cc.tif` | `…-88a2e8cc-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 48% -> 19580 dots; predicted +0.015 MODEL` |
| random 40 % → 22,592 dots | `releases/h33-h33-2-b2-MASSrandom40pct-20261023-894b5b4a.tif` | `…-894b5b4a-zeros.tif` | `h33-h33-2-b2; MASS random-drop 40% -> 22592 dots; predicted +0.013 MODEL` |

Strict subsets of R0 again: 40.0011 / 48.0002 / 40.0011 % of dots removed, no additions, no moves, zero
catalogue mass, 2.236 px inherited collar (IR90-14). The random arm is `numpy default_rng(20261023)` and is
**spatially even by construction** (p05 removal share 0.25 per 5 km block). Re-emit with
`.venv/bin/python scripts/build_mass_high_dose.py --build` after `scripts/restore_data.py`, confirm the
SHA-256 against `evidence/mass_high_dose_receipt.json`, and re-check with `--verify`.

**Do not upload** any FIFO-order drop (none was built: the probe is region-isolated, IR90-15) or a 50 %
shadow drop (region-isolated at depth, IR90-17). The 48 % arm is the deepest spatially uniform dose.

## 2. Strike-aligned PRUNE collar (session 2026-10-23, new value family)

| Candidate | Preferred file | Fallback twin | Form note (< 140 chars) |
|---|---|---|---|
| A4 (4 px across / 2 px along) | `releases/h33-h33-2-b2-PRUNEanisoA4L2-20261023-0bf248e2.tif` | `…-0bf248e2-zeros.tif` | `h33-h33-2-b2; PRUNE strike-aligned collar across<=4px along<=2px, fixed-count refill; predicted +0.003 DTI MODEL` |
| A5 | `releases/h33-h33-2-b2-PRUNEanisoA5L2-20261023-15218061.tif` | `…-15218061-zeros.tif` | `h33-h33-2-b2; PRUNE strike-aligned collar across<=5px along<=2px, fixed-count refill; predicted +0.002 DTI MODEL` |
| A6 | `releases/h33-h33-2-b2-PRUNEanisoA6L2-20261023-72dcdbd3.tif` | `…-72dcdbd3-zeros.tif` | `h33-h33-2-b2; PRUNE strike-aligned collar across<=6px along<=2px, fixed-count refill; predicted +0.000 DTI MODEL` |

Count held at 37,654 dots; 13.98 / 19.46 / 24.57 % of R0 changed; zero catalogue mass; every dot outside its
declared collar; minimum Euclidean catalogue distance 2.24 px (the parent's own floor, IR90-14). Detected dots
sit at a median 2.8–3.2 px **across** strike. Full hashes, collar diagnostics and refill-redundancy numbers:
`evidence/build_aniso_receipt.json`; re-run with
`.venv/bin/python scripts/build_aniso_prune_variants.py --verify`.

## 3. Isotropic PRUNE collar (session 2026-10-23a, still available)

`…-PRUNE3p5px-…-8b96d891`, `…-PRUNE4p5px-…-be7a1217`, `…-PRUNE5p5px-…-a69816c7`, each count-held at 37,654
dots. Receipt: `evidence/build_receipt.json`. These are the comparator for the along-strike-exemption question,
not the first choice for a slot.

## Format gate (every file, re-read from disk after writing)

| Property | Value |
|---|---|
| CRS / shape / transform | EPSG:32611, identical to `sample_submission.tif` |
| dtype / bands | float32, 1 band |
| inside footprint | finite, values in [0, 1] |
| outside footprint | NaN (primary) or 0 (`-zeros` fallback) |
| catalogue mass | **0.0** on every file |
| ledger | no sha256 repeated |

Min catalogue distance is inherited from R0 (2.236 px) on every MASS arm and on the aniso collar; the
isotropic PRUNE files are the only ones whose minimum is ≥ 3 px. Independent re-check (exit 0 = pass):

```
.venv/bin/python -m src.validate releases/<file>.tif .cache/gems_data/sample_submission.tif \
    --catalogue .cache/gems_data/existing_faults.tif [--zeros-outside]
```

## Before uploading, the human must supply

1. `TOP_PUBLIC` **with a date**, read from the leaderboard on the day (never from this repository).
2. Weekly slots used / remaining for the entity, and confirmation of the `2026-12-03` deadline and cutoff.
3. Submission-page **receipts** (score + date) for R0 and for each candidate — until then R0's 0.2778 is a
   **CLAIM** and every prediction here is a **MODEL**.
4. Confirmation that the chosen sha256 has never been submitted (at least 8 historical slots were exact repeats).
5. A decision on data-use terms before any of these rasters leave the private workspace, and a check that
   `releases/` was restored from pinned inputs (`scripts/restore_data.py`, `scripts/restore_releases.py`) rather
   than assumed to exist (IR90-10).
