# GEMSDOE90

<!-- CURRENT STATE (edit only this block) -->
## CURRENT STATE
- Parent (incumbent): h33-h33-2-b2 (GEMSDOE32), 37,654 dots; exact two-encoding rebuild, 26/26 pins verified.
- Best receipt: none. Best CLAIM: 0.2778 (R0, owner-reported). TOP_PUBLIC: ____ (dated: ____).
- Slots left this week: __ / 3 · total used: __ · Deadline: 2026-12-03 (UNVERIFIED, human confirms).
- Built, unscored (12): MASS shadow 10/20/30%; isotropic PRUNE 3.5/4.5/5.5 px; anisotropic PRUNE A4/A5/A6; SNAP TMI-VG/gravity-VG/VG-mean. SNAP is LOCAL ONLY (inherited collar; IR90-15).
- Next 3 slots: 1) MASSshadow10pct 2) PRUNEanisoA4L2 3) escalate a ≥+0.010 winner, else hold. SNAP is not queued (sub-0.01 MODELs, negative SGMC PROXY deltas).
- Reproduce: `scripts/restore_data.py`; use each receipt's verifier. SNAP: `scripts/build_snap_vertical.py --restore` then `--verify`; six rasters passed disk/format/hash/count/spacing checks.
<!-- /CURRENT STATE -->

Layout: `src/` gated pipeline (manifest verify → exact R0 rebuild → build →
format gate), `tests/` synthetic unit tests, `ledger/` submission ledger,
`registry/` pinned-input manifest, `docs/` mechanism cards + submit checklist,
`releases/` built rasters (gitignored — this repo is PUBLIC; competition
rasters/data must never be committed, see IRREGULARITIES.md #2).
