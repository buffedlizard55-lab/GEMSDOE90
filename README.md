# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN), 26/26 input pins verified by SHA-256 (`evidence/r0_rebuild_receipt.json`).
- Best receipt: **none on file** (human supplies R0 portal receipt). Best CLAIM: 0.2778 (R0, owner-reported, no receipt in `ledger/submissions.csv`).
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- Built and unscored (15 candidates in gitignored `releases/`, none submitted): **RELIEF** landform-tercile reallocation (`RELIEFr2p12p5pct` +0.004, `RELIEFr2b10pct` +0.003, `RELIEFp2r15pct` -0.004; 37,654 dots; `evidence/relief_build_receipt.json`); **MASS** shadow ladder 10/20/30/40/48% + random-40% control (`evidence/mass_build_receipt.json`, `evidence/mass_high_dose_receipt.json`); **PRUNE** isotropic 3.5/4.5/5.5 px + strike-aligned A4/A5/A6 (`evidence/build_receipt.json`, `evidence/build_aniso_receipt.json`). All predictions are `MODEL`, not scores. Plus 3 WITHDRAWN FIFO-ranked MASS rungs (not candidates, see below).
- This session (2026-10-23c, agent-selected MASS): `MASSshadow40pct` pred +0.014, `MASSshadow48pct` +0.015, `MASSrandom40pct` +0.013 — receipt `evidence/mass_high_dose_receipt.json`.
- This session (2026-10-23d, agent-selected `RELIEF`): shifted 12.5% Range→Piedmont (4,707d), 10.0% Range→Basin (3,766d), and 15.0% Piedmont→Range counterpoint (5,648d) at fixed count on `H19-5` using `R=3 px` DTI marginal credit (`d_cat >= 3.0 px` on 100% of additions).
- Session 2026-10-23d (this branch, AXIS=MASS on the parent's FIFO ranking): three dose-ladder rungs (`drop5pct-tail`, `add5pct-next`, `add20pct-next`) were built from exact R0 and **withdrawn before submission** — the FIFO rank is geographic (SE-hole drop, northern-strip adds), violating Hard Constraint #5; see IR90-20 and `evidence/mass_dose_ladder_receipt.json`. Not slot candidates; rows kept WITHDRAWN as occupancy guards.
- Rejected before submission, probes recorded: FIFO-order drops 10/20/40 % (region-isolated: largest emptied 5 km-block cluster 162/316/632), FIFO 5 % tail drop and rank-head adds (IR90-20), and shadow 50 % (17-block = 425 km² hole) — IR90-15/IR90-17. Rasters and rows deleted or withheld; a build-time region-evenness gate now fails closed.
- Finding that contests the predicted sign: `shadow40` keeps **0** of R0's 838 strands ≥ 1 km (mean spacing 3.74 → 6.19 px); `rand40` keeps 136. The ranking eats densely sampled stretches, so the random control is in the slot plan.
- This session (2026-10-23 continuity, agent-selected `MASS`): `MASSshadowcont20pct` (`66d961ba`, pred +0.009), `MASSshadowcont30pct` (`885f6fee`, +0.011), `MASSshadowcont40pct` (`92be4121`, +0.013) — shadow ranking + strand protection (≤6 px articulation + 10-dot floor, `src/continuity.py`); all 857 R0 strands kept whole at 6 px at every dose for +2.7/+5.8/+7.4% exclusive credit vs shadow; receipt `evidence/mass_continuity_receipt.json`. Fresh sibling audit: all 7 axes already built, 0 receipts entity-wide; brief-literal CONCENTRATION-up already built and ≤0 on sibling SGMC MODELs (IR90-21).
- Next 3 slots (human decides; one mechanism per slot; `SLOT_PLAN.md`): `RELIEFr2p12p5pct` → `MASSshadowcont20pct` → conditional (`RELIEFr2b10pct` / `RELIEFp2r15pct` / `PRUNEanisoA4L2`). shadowcont-30/40 are next-week escalation rungs only. Do not slot any FIFO-ranked dose rung.
- Reproducibility: `scripts/restore_data.py` → `scripts/restore_releases.py` → `scripts/build_mass_shadow.py --build` → `scripts/build_mass_high_dose.py --build` → `scripts/build_aniso_prune_variants.py --build` → `scripts/build_relief_variants.py --verify` → `scripts/build_mass_continuity.py --verify`; every candidate re-emits to its recorded SHA-256. All 26 pinned inputs SHA-256 verified (`evidence/manifest_verification.json`); R0 rebuilt byte-identically (`evidence/r0_rebuild_receipt.json`). origin/main
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
