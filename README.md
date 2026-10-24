# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN), 26/26 input pins verified by SHA-256 (`evidence/r0_rebuild_receipt.json`, `evidence/concentration_build_receipt.json`).
- Best receipt: **none on file** (human supplies R0 portal receipt). Best CLAIM: 0.2778 (R0, owner-reported, no receipt in `ledger/submissions.csv`).
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____).
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms).
- Built and unscored (18 candidates in gitignored `releases/`, none submitted): **CONCENTRATION** 15 km strain/edge-prior moves 10/15/20% at fixed count (`8deb8269` +0.002, `fdba3c0a` -0.002, `bc411adb` -0.006; `evidence/concentration_build_receipt.json`); **RELIEF** 3 tercile reallocations; **MASS** shadow 10/20/30/40/48% + random-40% control; **PRUNE** isotropic 3.5/4.5/5.5 px + strike-aligned A4/A5/A6. All predictions are `MODEL`, not scores. Plus 3 WITHDRAWN FIFO-ranked MASS rungs (not candidates).
- This session (2026-10-23e, agent-selected `AXIS=CONCENTRATION`): prior = equal absolute-percentile ranks of pinned `tmi_hg`, `geod_2ndinv`, `geod_shearrate`, `iso_grav_anom_hg` averaged over 15 km blocks. R0's 15 km density CV 0.5103 moves to 0.5990 / 0.6949 / 0.7769 at 10 / 15 / 20% moved. Fixed count 37,654 on H19-5, all additions `d_cat>=3 px`, region-evenness gate PASS, zero catalogue mass.
- Report-only diagnostics for this session (`PROXY`, never gates/scores): leakage canary max symmetric AUC 0.574747; catalogue hide/recover n=13,920 with 95% CIs spanning zero; SGMC Δ -0.0064 / -0.0095 / -0.0142. No live receipt has validated any axis.
- Rejected before submission, probes recorded: FIFO-order drops/tail and rank-head adds (region-isolated or patterned, IR90-15/20), shadow 50% (17-block hole, IR90-17). Do not slot those rungs.
- Next 3 slots (human decides; one mechanism per slot): `MASSshadow20pct` (+0.009 MODEL) → `RELIEFr2p12p5pct` (+0.004) → `CONCENTRATIONb15kmstruct10pct` (+0.002); see `SLOT_PLAN.md` for restore commands and decision rules. Confirm quota, dated TOP_PUBLIC, R0 receipt and data-use terms before any upload.
- Reproducibility: `scripts/restore_data.py` → `scripts/restore_releases.py` (all 18 BUILT candidate pairs) → `scripts/build_concentration_variants.py --verify`; every candidate re-emits to its recorded SHA-256 without triggering experiment-reservation guards. Competition rasters remain ignored and out of Git/releases.
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
