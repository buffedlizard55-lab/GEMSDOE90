# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically this session (`c55bafc4…` zeros / `baeae321…` NaN), 26/26 input pins re-verified by SHA-256 (`evidence/manifest_verification.json`, `evidence/mass_add_receipt.json`).
- Best receipt: **none on file** (human supplies R0's portal receipt). Best CLAIM: 0.2778 (R0, owner-reported, no receipt).
- TOP_PUBLIC: ____ (human fills from leaderboard, with date: ____)
- Slots left this week: __ / 3 (one entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms)
- **This session (2026-10-23e, agent-selected `AXIS=MASS`, ADD direction)**: three region-even add rungs built from exact R0, all format-gated, zero catalogue mass, additions `d_cat >= 3.0 px`, quota-proportional to the parent's own 5 km block counts (p05 share 0.087–0.185, max 0.217). `evidence/mass_add_receipt.json`; re-emit with `scripts/build_mass_add_variants.py --build --rebuild-reserved`, re-check with `--verify`.
  - `MASSadd10pctGapmax` (+3,765 → 41,419 dots): **+0.0107 DTI MODEL** (bracket +0.0026…+0.0226) — best-predicted file this session.
  - `MASSadd10pctBlocknext` (+3,765 → 41,419 dots): **+0.0044 MODEL** (+0.0003…+0.0107) — the brief's literal "next-ranked" recipe, geography repaired.
  - `MASSadd20pctBlocknext` (+7,531 → 45,185 dots): **+0.0084 MODEL** (+0.0005…+0.0205) — dose slope.
- **Why ADD and not another round of thinning**: every valid MASS rung in the ledger is a deletion, and the FIFO add rungs were withdrawn (IR90-20). An addition cannot lower `T` (T is a max over dots), so its failure mode is bounded by the 0.2 mass penalty alone; the break-even credit is 0.056 and the measured marginal support credit per added dot is 0.46–1.01.
- **CONCENTRATION was investigated and deliberately not built** (IR90-22): with the `R=3 px` kernel, R0's dots are uniform in credit — mean marginal support credit on eligible pixels is 0.543–0.646 across every block-density quintile, and each dot's own exclusive credit is 0.980–0.997 in every quintile. A fixed-count density reallocation therefore loses ~0.98 and gains ~0.54 per moved dot at every dose, and R0's CV (0.901 at 5 km / 0.635 at 10 km) already sits above the brief's quoted best-file band 0.51–0.59.
- Still built and unscored (15 earlier candidates in gitignored `releases/`, none submitted): RELIEF ×3, MASS shadow 10/20/30/40/48 + random 40, PRUNE isotropic ×3 + aniso ×3. 3 WITHDRAWN FIFO rungs are not candidates (IR90-20).
- Next 3 slots (human decides; one mechanism per slot; full decision rules in `SLOT_PLAN.md`): `MASSadd10pctGapmax` → `MASSadd10pctBlocknext` → `MASSadd20pctBlocknext`, or R0's own receipt first if it is still missing.
- Reproducibility: `scripts/restore_data.py` → `scripts/build_mass_add_variants.py --build --rebuild-reserved` → `--verify`; the script re-emits every candidate to its recorded SHA-256 and rebuilds R0 byte-identically. All 74 unit tests pass; `src/validate.py` passes on all 6 new files.
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
