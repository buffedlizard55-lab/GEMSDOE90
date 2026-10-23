# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots, >2 px from the catalogue; rebuilt byte-identically this session (`zeros c55bafc4…`, `nan baeae321…`, see `evidence/r0_rebuild_receipt.json`), all 26 pinned inputs re-verified by sha256.
- Best receipt: **none on file**. Best CLAIM: 0.2778 (R0, owner-reported, no submission-page receipt in `ledger/submissions.csv`).
- TOP_PUBLIC: ____ (human fills from the leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23, agent-selected PRUNE, value family = strike-aligned collar): 3 fixed-count variants BUILT and format-gated, not submitted; rasters are gitignored (`docs/SUBMIT.md`).
- Next 3 slots (conditional on human quota/receipts): 1) aniso A4 (`…-0bf248e2`) 2) A6 if slot 1 ≥ +0.010, else the isotropic control `GEMSDOE87 PRUNE4` 3) hold for the final file + fallback — see `SLOT_PLAN.md`.
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
