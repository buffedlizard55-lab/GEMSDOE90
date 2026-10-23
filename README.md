# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically this session from pinned inputs (evidence/build_receipt_mass.json, r0_rebuild_receipt.json)
- Best receipt: **none on file.** Best CLAIM: 0.2778 (R0, owner-reported, no receipt in ledger/submissions.csv)
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23, agent-selected **MASS**): 3 files BUILT, unsubmitted — `MASSuniq20` 28,512 dots (+0.005 MODEL), `MASSuniq30` 24,747 dots (+0.007), `MASSfifo20` 28,512 dots (+0.001); all share the forced d_cat>=3 px collar. Rasters are gitignored; regenerate with `scripts/build_mass_variants.py --build` (see docs/SUBMIT.md).
- Earlier session (PRUNE 3.5/4.5/5.5 px) built 3 files, also unsubmitted; their hashes are unchanged in ledger/submissions.csv.
- Next 3 slots: 1) MASSuniq20 2) MASSuniq30 3) MASSfifo20 — see SLOT_PLAN.md
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
