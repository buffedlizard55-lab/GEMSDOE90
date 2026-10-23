# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (see evidence/r0_rebuild_receipt.json)
- Best receipt: none on file. Best CLAIM: 0.2778 (R0, owner-reported, no receipt in ledger/submissions.csv)
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23, agent-selected PRUNE): 3 fixed-count variants BUILT locally, not submitted; rasters are gitignored (see docs/SUBMIT.md)
- Reproducibility (2026-10-23, clean sandbox): all 26 pins re-verified, R0 rebuilt byte-identically (`c55bafc4…`), d2.8 ranking reproduced with 0 px difference, and all 3 candidate pairs re-emitted byte-identically to their recorded SHA-256 — `evidence/releases_restore_receipt.json`. Re-run: `.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/restore_releases.py && .venv/bin/python scripts/build_r0_variants.py --verify`
- Audit hold: inherited PRUNE cutoffs differ from brief v2; human acceptance required (IR90-07). No new experiments this turn; 26 pins, R0, six rasters and 22 tests rechecked.
- Next 3 slots (conditional on human quota/receipts and legacy-cutoff acceptance): 1) PRUNE dcat<=3.5 px 2) PRUNE dcat<=4.5 px 3) PRUNE dcat<=5.5 px — see SLOT_PLAN.md
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
