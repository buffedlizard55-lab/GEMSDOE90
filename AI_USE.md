# AI use disclosure — 2026-10-23

AI assistance authored the prior blocked pipeline now retained under `src/` and the current reproducibility code (`scripts/restore_data.py`, `scripts/build_r0_variants.py`), unit tests, experiment metadata, mechanism cards, ledger rows derived from the historical owner raw-paste ledger, and planning/submission documentation. AI also performed pinned-file integrity checks, exact R0 rebuild validation, and deterministic PRUNE builds described in `evidence/build_receipt.json`. The earlier pipeline's missing-input blocker is superseded by the complete pinned-manifest workflow; the old `src.build_prune` inputs are not used for these built candidates.

The human's brief supplied the objective, constraints, parent, quota rules, deadline, metric algebra, and allowed experiment axes. The agent selected PRUNE and the unused 3.5 / 4.5 / 5.5 px values after checking the available sibling ledgers; these are not human-approved slot choices. The agent did not contact DrivenData, submit a file, or claim a score. A human must review geology, provide current leaderboard/slot information and any portal receipts, and choose whether to submit.

Competition rasters remain under ignored `.cache/gems_data/` and local ignored `releases/`; they are not included in this public Git diff or any release. The owner-supplied mirror provenance and competition data-use terms have not been independently authenticated.

## Update 2026-10-23 (reproducibility pass, clean sandbox)

AI added `scripts/restore_releases.py`, which re-emits the three already-recorded PRUNE candidates from the pinned inputs and fails closed unless the bytes match the SHA-256 in `evidence/build_receipt.json` and `ledger/submissions.csv`; AI also added two ledger-consistency tests and this note. No new (AXIS, value) pair was created, no candidate was altered, and `scripts/build_r0_variants.py` was left byte-identical (SHA-256 `06f667c1…`, still pinned in both receipts) so the recorded generator hash stays valid. AI re-verified 26/26 input pins, rebuilt R0 byte-identically, reproduced the d2.8 ranking with 0 px difference, re-ran the format gate on all six files and the full test suite. AI did not contact DrivenData, submit, or claim any score.

## Update 2026-10-23 (session 2 — MASS axis, agent-selected)

AI verified all 26 manifest pins, rebuilt R0 byte-identically to both pinned encodings, reproduced the documented
H19-5 FIFO-BFS d2.8 ranking with 0 px difference, and authored `scripts/build_mass_variants.py`,
`scripts/mass_diagnostics.py`, `scripts/write_mass_ledger.py`, two new functions in `src/dti.py` (exact
distance-transform DTI for binary files) plus their tests, the three MASS mechanism cards, the ledger rows and the
rewritten `SLOT_PLAN.md` / `docs/SUBMIT.md` / README CURRENT STATE block.

**What the human decided vs what AI decided.** The human's brief supplied the objective, constraints, parent,
quota, deadline, metric algebra and the axis menu, and explicitly delegated axis choice to the agent. AI selected
MASS, the three files (uniq20, uniq30, fifo20), the collar policy, the ranking rules and the predicted intervals.
Those are not human-approved slot choices.

**AI did not**: contact DrivenData or dropbox.com, fetch any competition page, authenticate anything, submit a
file, or claim any score. Every number in the ledger for the three new files is a MODEL projection. Competition
rasters remain outside Git (`.cache/gems_data/`, ignored `releases/`); the owner-supplied mirror provenance and
the competition data-use terms are still unauthenticated (IR90-02).
