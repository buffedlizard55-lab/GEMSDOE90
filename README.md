# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically in a clean sandbox (`c55bafc4…` zeros / `baeae321…` NaN), 26/26 input pins re-verified by sha256.
- Best receipt: **none on file**. Best CLAIM: 0.2778 (R0, owner-reported, no submission-page receipt in `ledger/submissions.csv`).
- TOP_PUBLIC: ____ (human fills from the leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Built and unscored (12 candidates, none submitted): MASS shadow ladder 10/20/30 % (33,889 / 30,123 / 26,358 dots) and **40/48 %** (22,592 / 19,580) + **credit-blind random 40 %** control (22,592, seed 20261023); PRUNE isotropic collar 3.5 / 4.5 / 5.5 px and strike-aligned collar A4/A5/A6 (all count-held at 37,654). All predictions MODEL, not scores.
- This session (2026-10-23c, agent-selected MASS): `MASSshadow40pct` pred +0.014, `MASSshadow48pct` +0.015, `MASSrandom40pct` +0.013 — receipt `evidence/mass_high_dose_receipt.json`.
- Rejected before submission, probes recorded: FIFO-order drops 10/20/40 % (region-isolated: largest emptied 5 km-block cluster 162/316/632) and shadow 50 % (17-block = 425 km² hole) — IR90-15/IR90-17. Rasters and rows deleted; a build-time region-evenness gate now fails closed.
- Finding that contests the predicted sign: `shadow40` keeps **0** of R0's 838 strands ≥ 1 km (mean spacing 3.74 → 6.19 px); `rand40` keeps 136. The ranking eats densely sampled stretches, so the random control is in the slot plan.
- Next 3 slots (human decides; one mechanism per slot): 1) `MASSshadow20pct` 2) `MASSshadow40pct` 3) `MASSrandom40pct` — then `PRUNEanisoA4L2` or `MASSshadow48pct` on whichever receipt cleared +0.010; else hold. See `SLOT_PLAN.md`.
- Session 2026-10-23d (this branch, AXIS=MASS on the parent's FIFO ranking): three dose-ladder rungs (`drop5pct-tail`, `add5pct-next`, `add20pct-next`) were built from exact R0 and **withdrawn before submission** — the FIFO rank is geographic (SE-hole drop, northern-strip adds), violating Hard Constraint #5; see IR90-18 and `evidence/mass_dose_ladder_receipt.json`. Not slot candidates.
- Reproducibility: `scripts/restore_data.py` → `scripts/restore_releases.py` → `scripts/build_mass_shadow.py --build` → `scripts/build_mass_high_dose.py --build` → `scripts/build_aniso_prune_variants.py --build`; every candidate re-emits to its recorded SHA-256 (`--verify`).
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
