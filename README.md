# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically in a clean sandbox (`c55bafc4…` zeros / `baeae321…` NaN), 26/26 input pins re-verified by sha256.
- Best receipt: **none on file**. Best CLAIM: 0.2778 (R0, owner-reported, no submission-page receipt in `ledger/submissions.csv`).
- TOP_PUBLIC: ____ (human fills from the leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Built and unscored (9 candidates, all count-held or nested from R0, none submitted):
  · MASS shadow ladder 10/20/30 % — 33,889 / 30,123 / 26,358 dots, predicted +0.005 / +0.009 / +0.012 (MODEL)
  · PRUNE isotropic collar 3.5 / 4.5 / 5.5 px — 37,654 dots, predicted +0.002 / +0.000 / −0.003 (MODEL)
  · PRUNE strike-aligned collar across 4 / 5 / 6 px, along held at 2 px — 37,654 dots, predicted +0.003 / +0.002 / +0.000 (MODEL)
- Next 3 slots (human decides; one mechanism per slot): 1) `MASSshadow10pct` 2) `PRUNEanisoA4` 3) escalation on whichever receipt cleared +0.010, else hold — see `SLOT_PLAN.md`.
- Reproducibility: `scripts/restore_data.py` → `scripts/restore_releases.py` → `scripts/build_mass_shadow.py --build` / `scripts/build_aniso_prune_variants.py --build`; every candidate re-emits to its recorded SHA-256.
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
