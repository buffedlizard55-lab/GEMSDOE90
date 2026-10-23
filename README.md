# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically in both encodings (`c55bafc4…`, `baeae321…`)
- Best receipt: none on file. Best CLAIM: 0.2778 (R0, owner-reported, no receipt in ledger/submissions.csv)
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23, agent-selected SNAP): 3 vertical-gradient, gain-gated, 2.8 px-spacing variants BUILT locally; none submitted. All are LOCAL ONLY because R0's inherited sub-3 px collar remains (see IRREGULARITIES.md)
- Reproducibility: 26/26 pins verified; exact R0 and d2.8 ranking reproduced; six SNAP rasters passed disk/format/hash/count/spacing checks in `evidence/snap_build_receipt.json`. Restore: `.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/build_snap_vertical.py --restore && .venv/bin/python scripts/build_snap_vertical.py --verify`
- Next 3 slots (default HOLD; human must resolve collar and quota): 1) VG mean 2) TMI VG, only after ≥+0.010 for VG mean 3) gravity VG control, reserved — see SLOT_PLAN.md
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
