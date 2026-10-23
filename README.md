# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically in this sandbox on 2026-10-23 (`c55bafc4…` zeros / `baeae321…` NaN), d2.8 ranking reproduced with 0 px difference
- Best receipt: none on file, in this repository or in the sibling repositories audited this session. Best CLAIM: 0.2778 (R0, owner-reported 2026-10-04, no receipt)
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23, agent-selected **SNAP**): 3 cross-strike arms BUILT locally, not submitted — `SNAPXk4p0` (32.2 % of dots moved, predicted +0.004), `SNAPXk1p0` (54.4 %, +0.003), `SNAPXk0p25` (60.8 %, +0.001); all 37,654 dots, mean displacement 2.00 px, min catalogue distance 3.0 px. Rasters are gitignored (see docs/SUBMIT.md)
- Why SNAP: measured this session — only 61,481 refill pixels exist and 87 % of them sit 1.0 px from an R0 dot, so the field support is exhausted; under the DTI algebra mass is nearly free but duplicates and removals are not, leaving cross-strike position as the only menu lever that can raise T at fixed mass
- Reproducibility: 26/26 pins re-verified, R0 rebuilt byte-identically, and all 6 candidate pairs (3 PRUNE + 3 SNAP) re-emitted to their recorded SHA-256 — `evidence/snap_build_receipt.json`, `evidence/releases_restore_receipt.json`. Re-run: `.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/restore_releases.py && .venv/bin/python scripts/build_snap_variants.py --verify && .venv/bin/python -m pytest -q` (33 tests)
- Next 3 slots (conditional on human quota/receipts): 1) SNAP strict `SNAPXk4p0` 2) SNAP permissive `SNAPXk0p25` if slot 1 ≥ +0.010, else PRUNE 3.5 px 3) hold the slot — six built candidates and zero receipts is the binding constraint, not candidate supply. See SLOT_PLAN.md
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
