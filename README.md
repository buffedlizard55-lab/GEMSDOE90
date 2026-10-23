# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN; see `evidence/r0_rebuild_receipt.json`)
- Best receipt: none on file (human supplies R0 portal receipt). Best CLAIM: 0.2778 (R0, owner-reported, no receipt in `ledger/submissions.csv`)
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23, agent-selected RELIEF): 3 fixed-count (37,654-dot) variants BUILT locally in gitignored `releases/`, never submitted (`evidence/relief_build_receipt.json`, `docs/SUBMIT.md`); prior PRUNE 3.5/4.5/5.5 px candidates also retained and byte-restorable (`evidence/releases_restore_receipt.json`)
- Reproducibility: `.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/restore_releases.py && .venv/bin/python scripts/build_relief_variants.py --verify`
- Next 3 slots (conditional on human quota/receipts; see `SLOT_PLAN.md`): 1) `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f` (12.5% Range→Piedmont) 2) `h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17` (10.0% Range→Basin; or `PRUNE3p5px` to orthogonalize collar vs relief) 3) conditional counterpoint `h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f` (15.0% Piedmont→Range) if down-relief Δ ≤ -0.010, else combine winning axes
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
