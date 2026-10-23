# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN), 26/26 input pins verified by SHA-256 (`evidence/r0_rebuild_receipt.json`).
- Best receipt: **none on file** (human supplies R0 portal receipt). Best CLAIM: 0.2778 (R0, owner-reported, no receipt in `ledger/submissions.csv`).
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Built and unscored (15 local candidates in gitignored `releases/`, none submitted): **RELIEF** landform-tercile reallocation (`RELIEFr2p12p5pct` +0.004, `RELIEFr2b10pct` +0.003, `RELIEFp2r15pct` -0.004; 37,654 dots; `evidence/relief_build_receipt.json`); **MASS** shadow ladder 10/20/30/40/48% + random-40% control; **PRUNE** isotropic 3.5/4.5/5.5 px + strike-aligned A4/A5/A6. All predictions are `MODEL`, not scores.
- This session (2026-10-23d, agent-selected `RELIEF`): shifted 12.5% Range→Piedmont (4,707d), 10.0% Range→Basin (3,766d), and 15.0% Piedmont→Range counterpoint (5,648d) at fixed count on `H19-5` using `R=3 px` DTI marginal credit (`d_cat >= 3.0 px` on 100% of additions).
- Next 3 slots (one entity; human confirms quota/receipts first — see `SLOT_PLAN.md`): 1) `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f` (or `MASSshadow20pct` if testing count first) 2) orthogonal axis (`MASSshadow20pct` or `PRUNEanisoA4L2`) 3) conditional `RELIEFr2b10pct` (if down-relief Δ >= +0.010) or `RELIEFp2r15pct` (if down-relief Δ <= -0.010).
- Reproducibility: `.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/restore_releases.py && .venv/bin/python scripts/build_relief_variants.py --verify && .venv/bin/python -m pytest -q`.
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
