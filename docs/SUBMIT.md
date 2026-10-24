# Human submission packet — 2026-10-23 sessions (MASS ladder incl. high doses + both PRUNE collars)

**The agent does not submit and cannot see the leaderboard.** Every GeoTIFF below is local and Git-ignored on
purpose: this repository is public and competition rasters must not be committed or released
(`IRREGULARITIES.md` IR90-02). Only the human uploads, from their own account, **one file per scored slot**.
The `-zeros.tif` twin is a fallback encoding of the *same* experiment, not a second slot.

Parent for everything here: `h33-h33-2-b2` (R0), 37,654 unit-mass dots, CLAIM 0.2778 with no receipt on file.
`SLOT_PLAN.md` gives the order and the decision rule; this file is the upload mechanics.

**Reproduction shortcut:** after `scripts/restore_data.py`, `.venv/bin/python scripts/restore_releases.py`
byte-reproduces the 18 core pairs present when this branch was cut (PRUNE, RELIEF, held CONCENTRATION, shadow /
high-dose MASS). Main's newer MASS-add, continuity and A5-refill candidates keep their own family builders or
verifiers — use those for the slotted files. Historical `--build` recipes for already-reserved `(AXIS, value)`
pairs may intentionally fail closed; never bypass a reservation guard to create a new submission.

## 0. WITHDRAWN — do not upload (session 2026-10-23d, FIFO-ranked MASS rungs)

`…-MASSdrop5pct-tail-20261023-ce48329b`, `…-MASSadd5pct-next-20261023-46f0886b`, `…-MASSadd20pct-next-20261023-63954e89`
(35,771 / 39,537 / 45,185 dots) passed every §6 format gate but are **withdrawn under Hard Constraint #5**
(IR90-20): the drop deletes an 81-block SE hole and both adds land in northern grid strips. Ledger status
`WITHDRAWN`; rasters are in `.cache/region_probes/` (out of `releases/`); their `-zeros` twins likewise.
Receipt (predictions kept as record only): `evidence/mass_dose_ladder_receipt.json`. Do not submit, do not
slot; a region-even replacement rung is proposed in `SLOT_PLAN.md`.

## 1. MASS shadow-dose ladder (session 2026-10-23b, nested)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin | Form note (< 140 chars) |
|---|---|---|---|
| 10 % → 33,889 dots | `releases/h33-h33-2-b2-MASSshadow10pct-20261023-e2e518d5.tif` | `…-e2e518d5-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 10% -> 33889 dots; predicted +0.005 MODEL` |
| 20 % → 30,123 dots | `releases/h33-h33-2-b2-MASSshadow20pct-20261023-c4ce118b.tif` | `…-c4ce118b-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 20% -> 30123 dots; predicted +0.009 MODEL` |
| 30 % → 26,358 dots | `releases/h33-h33-2-b2-MASSshadow30pct-20261023-9d64151a.tif` | `…-9d64151a-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 30% -> 26358 dots; predicted +0.012 MODEL` |

Each file is a strict subset of R0 — no additions, no moves, 10.00 / 20.00 / 30.00 % of R0 removed, zero
catalogue mass. In a fresh sandbox these rasters are absent because `releases/` is gitignored; the preferred
restore is `.venv/bin/python scripts/restore_releases.py` after `scripts/restore_data.py`, then confirm each
SHA-256 against `evidence/mass_build_receipt.json` before uploading. The historical
`scripts/build_mass_shadow.py --build` may now fail closed on the occupied `(MASS, value)` reservation.
Full checks and parent-diff statistics: `evidence/mass_build_receipt.json`; byte re-check with
`.venv/bin/python scripts/build_mass_shadow.py --verify`. These files inherit R0's 2.236 px collar exactly
(IR90-07): a MASS-only edit must not also move the collar.

## 1c. MASS add-direction infill (session 2026-10-23e, this branch)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin | Form note (< 140 chars) |
|---|---|---|---|
| +5 % → 39,537 dots | `releases/h33-h33-2-b2-MASSadd5pctq50-20261023-c4e6144c.tif` | `…-c4e6144c-zeros.tif` | `h33-h33-2-b2; MASS add 1883d (5%) kernel-mid-strand infill, 50px-block even quotas, d_cat>=3px; pred +0.008 DTI MODEL` |
| +10 % → 41,419 dots | `releases/h33-h33-2-b2-MASSadd10pctq50-20261023-5edc84de.tif` | `…-5edc84de-zeros.tif` | `h33-h33-2-b2; MASS add 3765d (10%) kernel-mid-strand infill, 50px-block even quotas, d_cat>=3px; pred +0.014 DTI MODEL` |
| +20 % → 45,185 dots | `releases/h33-h33-2-b2-MASSadd20pctq50-20261023-f94efff4.tif` | `…-f94efff4-zeros.tif` | `h33-h33-2-b2; MASS add 7531d (20%) kernel-mid-strand infill, 50px-block even quotas, d_cat>=3px; pred +0.022 DTI MODEL` |

Every parent dot is retained; no dot is moved; all values are 1.0; the 1,883 / 3,765 / 7,531 additions sit on
H19-5 support, are **>= 3 px** from the catalogue (median 2.3 px from an existing dot: this is mid-strand infill,
not reach into new ground), and are apportioned over 5 km blocks in proportion to the parent's own dot counts.
Zero catalogue mass. Rebuild with `.venv/bin/python scripts/build_mass_infill.py --build` after
`scripts/restore_data.py`; check with `--verify` (re-emits byte-identically). Receipt and gates:
`evidence/mass_infill_receipt.json`. Note these are **supersets** of R0, so they inherit R0's 2.236 px floor on
untouched dots (IR90-21) and they are the only candidates in this repo that add mass.

## 1b. MASS high-dose arms + credit-blind control (session 2026-10-23c)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin | Form note (< 140 chars) |
|---|---|---|---|
| 40 % → 22,592 dots | `releases/h33-h33-2-b2-MASSshadow40pct-20261023-e2546fbe.tif` | `…-e2546fbe-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 40% -> 22592 dots; predicted +0.014 MODEL` |
| 48 % → 19,580 dots | `releases/h33-h33-2-b2-MASSshadow48pct-20261023-88a2e8cc.tif` | `…-88a2e8cc-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 48% -> 19580 dots; predicted +0.015 MODEL` |
| random 40 % → 22,592 dots | `releases/h33-h33-2-b2-MASSrandom40pct-20261023-894b5b4a.tif` | `…-894b5b4a-zeros.tif` | `h33-h33-2-b2; MASS random-drop 40% -> 22592 dots; predicted +0.013 MODEL` |

Strict subsets of R0 again: 40.0011 / 48.0002 / 40.0011 % of dots removed, no additions, no moves, zero
catalogue mass, 2.236 px inherited collar (IR90-14). The random arm is `numpy default_rng(20261023)` and is
**spatially even by construction** (p05 removal share 0.25 per 5 km block). Preferred re-emission is
`.venv/bin/python scripts/restore_releases.py` after `scripts/restore_data.py`; confirm the SHA-256 against
`evidence/mass_high_dose_receipt.json` and re-check with `scripts/build_mass_high_dose.py --verify`. The
historical `--build` path may now fail closed on the occupied `(MASS, value)` reservation.

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

## 4. Landform-relief tercile reallocation (`AXIS=RELIEF`, session 2026-10-23d)

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (`-zeros.tif`) | SHA-256 (NaN / zeros) | Form note (`<=140` chars) |
|---|---|---|---|---|
| **12.5% Range→Piedmont** (4,707d; 25.001% diff) | `releases/h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f.tif` | `…-5e64d01f-zeros.tif` | `5e64d01f26b6687f…` / `c50e5a8b98b0f6c3…` | `h33-h33-2-b2; RELIEF 12.5% (4707d) range->piedmont; pred +0.004 DTI MODEL` |
| **10.0% Range→Basin** (3,766d; 20.003% diff) | `releases/h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17.tif` | `…-9e7b5e17-zeros.tif` | `9e7b5e17ad3b27dd…` / `870a92b2cfb98c78…` | `h33-h33-2-b2; RELIEF 10% (3766d) range->basin; pred +0.003 DTI MODEL` |
| **15.0% Piedmont→Range** (5,648d; 29.999% diff) | `releases/h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f.tif` | `…-ad95e30f-zeros.tif` | `ad95e30f857011f9…` / `66d1abb217ce9cfb…` | `h33-h33-2-b2; RELIEF 15% (5648d) piedmont->range; pred -0.004 DTI MODEL` |

Count held at **37,654 unit-mass dots** on `H19-5`; zero catalogue mass; **100% of newly added dots enforce `d_cat >= 3.0 px` strictly** (untouched R0 dots inherit R0's `2.236 px` floor without confounding `RELIEF` with `PRUNE`; IR90-18). Full hashes, parent-diff stats, and report-only `PROXY` diagnostics: `evidence/relief_build_receipt.json`. Re-emit and verify via `.venv/bin/python scripts/restore_releases.py && .venv/bin/python scripts/build_relief_variants.py --verify`.

## 5a. Continuity-aware MASS drops (`AXIS=MASS`, session 2026-10-23 continuity)

Deletion-only strict subsets of R0 at the shadow ladder's exact counts, ranking identical to §§1–1b plus strand protection (≤ 6 px link graph; ≥ 10-dot strands may not be split; `src/continuity.py`). All 857 R0 strands survive whole at 6 px at every dose; credit price vs shadow +2.7% / +5.8% / +7.4%. Zero catalogue mass; inherited 2.236 px collar floor unchanged (no additions). Full hashes, parent-diff, region-gate and report-only `PROXY` stats: `evidence/mass_continuity_receipt.json`. Re-emit and verify via `.venv/bin/python scripts/build_mass_continuity.py --verify` (after `scripts/restore_data.py`).

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (`-zeros.tif`) | SHA-256 (NaN / zeros) | Form note (`<=140` chars) |
|---|---|---|---|---|
| **shadowcont-drop 20%** (→ 30,123d; 20.0005% diff) | `releases/h33-h33-2-b2-MASSshadowcont20pct-20261023-66d961ba.tif` | `…-66d961ba-zeros.tif` | `66d961ba325f3830…` / `038844cd73608598…` | `h33-h33-2-b2; MASS shadowcont-drop 20% -> 30123 dots, all >=1km strands kept; predicted +0.009 MODEL` |
| **shadowcont-drop 30%** (→ 26,358d; 29.9995% diff) | `releases/h33-h33-2-b2-MASSshadowcont30pct-20261023-885f6fee.tif` | `…-885f6fee-zeros.tif` | `885f6feed41a50b1…` / `c2b21dd19c0b698a…` | `h33-h33-2-b2; MASS shadowcont-drop 30% -> 26358 dots, all >=1km strands kept; predicted +0.011 MODEL` |
| **shadowcont-drop 40%** (→ 22,592d; 40.0011% diff) | `releases/h33-h33-2-b2-MASSshadowcont40pct-20261023-92be4121.tif` | `…-92be4121-zeros.tif` | `92be4121610708eb…` / `dce335c5b91f4f41…` | `h33-h33-2-b2; MASS shadowcont-drop 40% -> 22592 dots, all >=1km strands kept; predicted +0.013 MODEL` |

Slot guidance is in `SLOT_PLAN.md` (merged order): the add-direction ladder leads the week; shadowcont-20 is the first drop-direction probe (Slot-2 branch if the add sign test is negative; a null add test goes to orthogonal A5/L1), shadowcont-40 is the Slot-3 escalation corner, and shadowcont-30 is held unless a mid-dose slope point is needed — never all three in one week pre-receipt. Upload **one** file per slot — NaN primary, `-zeros` only as encoding fallback.
## 5b. Fixed-count A5 along-strike PRUNE (current session)

| Candidate | Preferred file (NaN outside) | Fallback twin | Form note (`<=140` chars) |
|---|---|---|---|
| **A5/L1** | `releases/h33-h33-2-b2-PRUNEanisoA5L1-20261023-cd2c60ce.tif` | `…-cd2c60ce-zeros.tif` | `h33-h33-2-b2; PRUNE A5/L1, fixed-count refill; pred +0.005 DTI MODEL` |
| A5/L1.5 | `releases/h33-h33-2-b2-PRUNEanisoA5L1p5-20261023-9486c7e6.tif` | `…-9486c7e6-zeros.tif` | `h33-h33-2-b2; PRUNE A5/L1.5, fixed-count refill; pred +0.004 DTI MODEL` |
| A5/L0.5 | `releases/h33-h33-2-b2-PRUNEanisoA5L0p5-20261023-91ff3771.tif` | `…-91ff3771-zeros.tif` | `h33-h33-2-b2; PRUNE A5/L0.5, fixed-count refill; pred +0.003 DTI MODEL` |

All three hold **37,654 dots**, emit zero catalogue mass, and preserve R0's `d_cat>2 px` baseline on every final dot. Format receipt, full hashes, parent diffs, PROXY CIs and byte self-check: `evidence/aniso_along_refill_receipt.json`. Restore with `scripts/restore_data.py`; if absent, re-emit with `.venv/bin/python scripts/build_aniso_prune_along.py --build`; then run `--verify`. Upload one encoding only.

**WITHDRAWN — do not upload:** `PRUNEanisoA4L2nr`, `PRUNEanisoA5L2nr`, `PRUNEanisoA6L2nr`; delete-only probes violated the fixed-count PRUNE recipe (IR90-29).

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

## 6. MASS add — placement contrast, `blocknext` (session 2026-10-23f)

Two live files, add-only edits of exact R0, **0 dots removed**, region-even per-5 km-block quotas proportional to the
parent's own dot count (cap +50 %/block, zero where R0 has none), all on the H19-5 support and all at Euclidean
`d_cat >= 3.0 px`. They exist to answer one question the gapmax ladder cannot: **does the ranking matter at all?**
Same doses, same geography, same pool as `MASSadd10pctq50` / `MASSadd20pctq50` — the cells are chosen by the parent's
own FIFO-BFS rank instead of by kernel credit. Receipt: `evidence/mass_add_receipt.json`.

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (`-zeros.tif`) | Form note (`<= 140` chars) |
|---|---|---|---|
| **blocknext +10 %** (3,765 added; 41,419 dots) | `releases/h33-h33-2-b2-MASSadd10pctBlocknext-20261023-89d16c16.tif` | `…-89d16c16-zeros.tif` | `h33-h33-2-b2; MASS add 10% (3765d) blocknext; pred +0.004 DTI MODEL` |
| **blocknext +20 %** (7,531 added; 45,185 dots) | `releases/h33-h33-2-b2-MASSadd20pctBlocknext-20261023-260d987e.tif` | `…-260d987e-zeros.tif` | `h33-h33-2-b2; MASS add 20% (7531d) blocknext; pred +0.008 DTI MODEL` |

SHA-256 (NaN / zeros): `89d16c16bcd336f5…` / `6108f696a660ec28…`; `260d987e0a89a945…` / `d59ccf7744eca41e…`.
Format receipt: `src/validate.py` PASS on all four files, `n_dots` 41,419 / 45,185, `catalogue_mass` 0.0, min distance
of added dots exactly 3.0 px, 0 added dots below 3 px, inherited R0 collar untouched (1,611 dots at 2.236–3.0 px,
IR90-21 on main). Re-emit with `.venv/bin/python scripts/build_mass_add_variants.py --build --rebuild-reserved` after
`scripts/restore_data.py`, confirm the SHA-256, then re-check with `--verify`. Upload **one** encoding.

**WITHDRAWN — do not upload:** `MASSadd10pctGapmax` (`98408334…`). It is the same experiment as the already-merged
`MASSadd10pctq50` (`5edc84de…`): identical 62,556-px eligible pool, identical gapmax ranking, identical block quotas,
differing only in tie-breaks. Rasters are in `.cache/withdrawn/`; the ledger row is an occupancy guard (IR90-24).

## 7. HELD — 15 km structural-prior concentration (`AXIS=CONCENTRATION`, session 2026-10-23e)

Prior: equal absolute-percentile ranks of pinned `training_features.tif` bands 3 `tmi_hg`, 4 `geod_2ndinv`, 7 `geod_shearrate` and 18 `iso_grav_anom_hg`, averaged in 15 km blocks. Dots move from the lowest-prior 35% to the highest-prior 35% of blocks; count stays 37,654 on `H19-5`. No thermal wells/springs/vents or hidden/public truth enter the prior. Receipt: `evidence/concentration_build_receipt.json`.

| Candidate | Preferred file (NaN outside footprint) | Fallback twin | SHA-256 (NaN / zeros) | Form note (`<=140` chars) |
|---|---|---|---|---|
| **10%** (3,765d; 19.998% diff; CV 0.5103→0.5990; pred +0.002) | `releases/h33-h33-2-b2-CONCENTRATIONb15kmstruct10pct-20261023-8deb8269.tif` | `…-8deb8269-zeros.tif` | `8deb8269da2c7548…` / `c2c7e04bcad1927c…` | `h33-h33-2-b2; CONC 15km structural-prior move 10% low->high; 37654 dots; pred +0.002 MODEL` |
| **15%** (5,648d; 29.999% diff; CV 0.5103→0.6949; pred -0.002) | `releases/h33-h33-2-b2-CONCENTRATIONb15kmstruct15pct-20261023-fdba3c0a.tif` | `…-fdba3c0a-zeros.tif` | `fdba3c0a6bab3b1c…` / `307e5b1ca0099051…` | `h33-h33-2-b2; CONC 15km structural-prior move 15% low->high; 37654 dots; pred -0.002 MODEL` |
| **20%** (7,531d; 40.001% diff; CV 0.5103→0.7769; pred -0.006) | `releases/h33-h33-2-b2-CONCENTRATIONb15kmstruct20pct-20261023-bc411adb.tif` | `…-bc411adb-zeros.tif` | `bc411adbec7afbde…` / `bc74e6f67b4e545c…` | `h33-h33-2-b2; CONC 15km structural-prior move 20% low->high; 37654 dots; pred -0.006 MODEL` |

Zero catalogue mass; 100% of **newly added** dots are at `d_cat >= 3.0 px`; untouched R0 dots inherit the parent's `2.236 px` minimum rather than turning CONCENTRATION into a PRUNE hybrid (IR90-31). Region-evenness gate passed on every arm (no 15 km donor block loses ≥90%; largest emptied cluster 0). Re-emit/verify with `.venv/bin/python scripts/restore_releases.py && .venv/bin/python scripts/build_concentration_variants.py --verify`. Report-only `PROXY`: catalogue hide/recover n=13,920, Δ ≈ 0 (95% CIs span zero); SGMC Δ -0.0064 / -0.0095 / -0.0142; leakage canary max symmetric AUC 0.574747. None is a score or a gate.

**Post-merge slot decision:** HOLD. Main's IR90-25/26 credit-uniformity and sibling MODEL audit, plus this
session's negative support-credit balance and SGMC PROXY, outweigh the 15 km CV coincidence. Do not spend one
of the next three slots here; use the integrated order at the top of `SLOT_PLAN.md`. These files remain
reproducible occupancy/dose-response guards only.

## Strain-prior CONCENTRATION — 5 km band-4 strain, HELD from slots (session `arena/388fea70`)

Fixed-count (37,654) reallocation of R0 mass across 5 km blocks ranked by a LABEL-AGNOSTIC geodetic strain-rate
invariant (band 4 `geod_2ndinv` of pinned `training_features.tif`): near-orthogonal to R0 density (r=+0.11),
relief-neutral (r=−0.046), no test label/score. Complementary top/bottom-50% strain pools; greedy R=3 px
marginal-credit drop/add; 100% of added dots enforce d_cat≥3.0 px (untouched R0 dots inherit R0's 2.236 px floor,
IR90-07/18/33); zero catalogue mass; anti-isolation gate passed. `strainAway10` is a matched-dose SIGN CONTROL.
These source files were renamed `*_strain5km` to coexist with main PR #20's 15 km ladder, which owns the canonical
`concentration.py` / `build_concentration_variants.py` / `concentration_build_receipt.json` (IR90-32).
**Status: BUILT, HELD from slots** (IR90-25/26/30/34) — string-distinct occupancy guards, not next-slot candidates.
Full hashes/stats/PROXY diagnostics: `evidence/concentration_strain5km_build_receipt.json`.

| Candidate | Preferred file (NaN outside) | Fallback (`-zeros.tif`) | SHA-256 (NaN / zeros) | Form note (<=140) |
|---|---|---|---|---|
| 10% low→high strain | `releases/h33-h33-2-b2-CONCstrain10-20261023-aa60138c.tif` | `…-aa60138c-zeros.tif` | `aa60138c3e70317…` / `c1822125a6d8e4f0…` | `h33-h33-2-b2; CONC 10% (3765d) low->high strain; pred +0.004 DTI MODEL` |
| 15% low→high strain | `releases/h33-h33-2-b2-CONCstrain15-20261023-d3db2957.tif` | `…-d3db2957-zeros.tif` | `d3db2957a079732…` / `45029ddb0db0c24…` | `h33-h33-2-b2; CONC 15% (5648d) low->high strain; pred +0.001 DTI MODEL` |
| 10% high→low strain (SIGN CONTROL) | `releases/h33-h33-2-b2-CONCstrainAway10-20261023-bd514054.tif` | `…-bd514054-zeros.tif` | `bd5140546ebc481…` / `3d390e97da725d4…` | `h33-h33-2-b2; CONC 10% (3765d) high->low strain; pred -0.004 DTI MODEL` |

Rasters are NOT committed (public repo). Re-emit with `.venv/bin/python scripts/restore_data.py` then
`.venv/bin/python scripts/build_concentration_strain5km.py --build`; confirm each SHA-256 against
`evidence/concentration_strain5km_build_receipt.json` / its ledger row; re-check with
`.venv/bin/python scripts/build_concentration_strain5km.py --verify` and the `src.validate` format gate. The agent
does not submit. Even if verified, these are HELD — do not upload without adjudicating entity-scope/quota
(IR90-26/30/32) and the headwind (IR90-25/34).

## 8. Frontier collar 3.4 px with max-marginal refill — FALLBACK, not slot 1–3 (session 2026-10-24)

One file pair, `AXIS=PRUNE`, built from the byte-identical R0 (zeros `c55bafc4…` / NaN `baeae321…`):
2,702 dots removed from the 2.236–3.162 px catalogue shell, 2,702 re-placed at the maximum marginal R=3 px
kernel credit inside region-even 5 km quotas, count held at 37,654, **every final dot ≥ 3.606 px** from the
catalogue (the only candidate in this repo stricter than the `≥ 3 px` rule), zero catalogue mass.

| Candidate | Preferred file (NaN outside) | Fallback (`-zeros.tif`) | SHA-256 (NaN / zeros) | Form note (<=140) |
|---|---|---|---|---|
| collar 3.4 px + gapmax refill | `releases/h33-h33-2-b2-PRUNEcollar3p4Gapmax-20261024-e69532d5.tif` | `…-e69532d5-zeros.tif` | `e69532d5c25f101…` / `cc27b807a3c56c2…` | `h33-h33-2-b2; PRUNE collar 3.4px, fixed count, max-marginal refill; pred +0.002 DTI MODEL` |

Prediction `+0.002 DTI (MODEL; bracket −0.008…+0.013)`. The same receipt records the measurement this file exists
for: at the same collar and count the lineage's FIFO-BFS refill buys 0.57 support credit per dot, maximum-marginal
placement buys 1.30. **Do not slot it ahead of the MASS-add order** (SLOT_PLAN.md); it is the fallback for a live
receipt showing the collar gradient is still alive, or a `≥ 3 px`-compliance control.

Reproduce: `.venv/bin/python scripts/restore_data.py` → `.venv/bin/python scripts/build_prune_collar_gapmax.py --build`
(idempotent: a hash-identical ledger row is accepted, a different one stops the build) → `--verify` re-emits both encodings and
compares SHA-256 → `python -m src.validate <file> .cache/gems_data/sample_submission.tif --catalogue
.cache/gems_data/existing_faults.tif`. Receipt: `evidence/prune_collar_gapmax_receipt.json`.
The catalogue hide-and-recover PROXY reads 0.0 for this file **by construction** (its "truth" is the catalogue mask
itself) — IR90-36; never use it to veto a collar candidate.
