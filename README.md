# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN); all 26 pinned inputs SHA-256 verified (`evidence/r0_rebuild_receipt.json`).
- Best receipt: **none on file**. Best CLAIM: 0.2778 (R0, owner-reported, no receipt). TOP_PUBLIC: ____ (human supplies from leaderboard, with date: ____).
- Slots left this week: __ / 3 (ONE entity) · total used: __ · Deadline: 2026-12-03 (UNVERIFIED; human confirms).
- This session (2026-10-23, agent-selected final AXIS=PRUNE): three fixed-count A5 along-strike collars, all 37,654 dots, zero catalogue mass, and every final dot `d_cat>2 px`: **A5/L1** (`cd2c60ce`, 12.6733% diff, pred +0.005 MODEL), **A5/L1.5** (`9486c7e6`, 16.6251%, +0.004), **A5/L0.5** (`91ff3771`, 7.0803%, +0.003). Receipt: `evidence/aniso_along_refill_receipt.json`; six Git-ignored rasters in `releases/`, unscored.
- Report-only diagnostics (never gates/scores): leakage canary max symmetric AUC 0.5695; catalogue hide/recover n=13,920 and SGMC n=62,122 are PROXY with 95% CIs in the receipt. Predictions were frozen before proxies.
- Rejected before submission: SNAP cannot jointly hold count, cap moves at 2 px, and put every dot >=3 px from the catalogue (30 inherited dots have no legal destination; IR90-21). Three delete-only PRUNE probes were WITHDRAWN because the brief requires fixed-count refill (IR90-22); do not upload them.
- Next 3 slots (human decides): **A5/L1** → orthogonal **MASSshadow20pct** → conditional **A5/L0.5**, recorded **A5/L2**, or **RELIEFr2p12p5pct** per `SLOT_PLAN.md`. Live |Δ|<0.010 is no evidence.
- Reproduce: `scripts/restore_data.py` → `scripts/build_aniso_prune_along.py --build` (when rasters are absent) → `scripts/build_aniso_prune_along.py --verify`; 72 tests pass locally. Human supplies receipts, quota state, dated TOP_PUBLIC, deadline confirmation, and all upload decisions.
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
