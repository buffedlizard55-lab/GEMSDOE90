# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN)
- Best receipt: none on file. Best CLAIM: 0.2778 (R0, owner-reported, no receipt in ledger/submissions.csv)
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Session axis (2026-10-23c, agent-selected MASS — high dose + control): 3 new pairs BUILT, not submitted —
  `MASSshadow40pct` 22,592 dots (pred +0.014), `MASSshadow48pct` 19,580 (pred +0.015), `MASSrandom40pct` 22,592 (credit-blind control, pred +0.013). All MODEL, not scores. Receipt: `evidence/mass_high_dose_receipt.json`
- Rejected before submission (recorded as probes): FIFO-order drops 10/20/40 % and shadow 50 % — region-isolated under Hard Constraint #5 (largest emptied 5 km-block cluster 162 / 316 / 632 / 17). Rasters and rows removed; see IR90-07/IR90-10
- Finding: `shadow40` keeps 0 of R0's 838 strands ≥ 1 km (mean spacing 3.74 → 6.19 px); `rand40` keeps 136. The ranking attacks densely sampled stretches, not just redundant mass — this competes with the predicted sign
- Also built, unsubmitted: `MASSshadow10/20/30pct` (2026-10-23b) and `PRUNE3p5/4p5/5p5px` (2026-10-23a)
- Reproducibility (2026-10-23c): 26/26 pins re-verified; R0 rebuilt byte-identically; all 3 new pairs re-emitted byte-identically to their recorded SHA-256. Re-run: `.venv/bin/python scripts/restore_data.py && .venv/bin/python scripts/build_mass_shadow.py --build && .venv/bin/python scripts/build_mass_high_dose.py --build && .venv/bin/python scripts/build_mass_high_dose.py --verify` (see docs/SUBMIT.md for the exact command list)
- Next 3 slots: 1) `MASSshadow40pct` 2) `MASSshadow48pct` if slot 1 ≥ +0.010 else `MASSshadow20pct` 3) `MASSrandom40pct` — see SLOT_PLAN.md
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
