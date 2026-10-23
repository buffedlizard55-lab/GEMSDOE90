# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN)
- Best receipt: none on file. Best CLAIM: 0.2778 (R0, owner-reported, no receipt in ledger/submissions.csv)
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23b, agent-selected MASS): 3 nested shadow-drop doses BUILT — 10% (33,889 dots), 20% (30,123), 30% (26,358); predicted +0.005 / +0.009 / +0.012 DTI (MODEL). Not submitted; rasters gitignored (docs/SUBMIT.md)
- Also built, unsubmitted (2026-10-23a): PRUNE collar 3.5 / 4.5 / 5.5 px, count-held at 37,654 dots
- Reproducibility (2026-10-23, clean sandbox): 26/26 pins re-verified, R0 rebuilt byte-identically, d2.8 ranking reproduced with 0 px difference, PRUNE pairs re-emitted to their recorded hashes (`evidence/releases_restore_receipt.json`). Re-run: `.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/restore_releases.py && .venv/bin/python scripts/build_mass_shadow.py --build`
- Next 3 slots: 1) MASSshadow10pct 2) MASSshadow20pct 3) MASSshadow30pct — stop the ladder early if slot 1 is ≤ −0.005; see SLOT_PLAN.md
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
