# AI use disclosure — 2026-10-23

AI assistance authored the prior blocked pipeline now retained under `src/` and the current reproducibility code (`scripts/restore_data.py`, `scripts/build_r0_variants.py`), unit tests, experiment metadata, mechanism cards, ledger rows derived from the historical owner raw-paste ledger, and planning/submission documentation. AI also performed pinned-file integrity checks, exact R0 rebuild validation, and deterministic PRUNE builds described in `evidence/build_receipt.json`. The earlier pipeline's missing-input blocker is superseded by the complete pinned-manifest workflow; the old `src.build_prune` inputs are not used for these built candidates.

The human's brief supplied the objective, constraints, parent, quota rules, deadline, metric algebra, and allowed experiment axes. The agent selected PRUNE and the unused 3.5 / 4.5 / 5.5 px values after checking the available sibling ledgers; these are not human-approved slot choices. The agent did not contact DrivenData, submit a file, or claim a score. A human must review geology, provide current leaderboard/slot information and any portal receipts, and choose whether to submit.

Competition rasters remain under ignored `.cache/gems_data/` and local ignored `releases/`; they are not included in this public Git diff or any release. The owner-supplied mirror provenance and competition data-use terms have not been independently authenticated.

## Session 2026-10-23 (2) — strike-aligned PRUNE collar

AI wrote `scripts/aniso_prune.py`, `scripts/build_aniso_prune_variants.py`, `tests/test_aniso_prune.py`, the
mechanism cards, the ledger/reservation rows, the slot plan and this disclosure. It restored and sha256-verified
all 26 pinned inputs, rebuilt R0 byte-identically, ran the format gate and the report-only leakage canary, and
built three unscored candidates. The agent selected the axis (PRUNE) and the value family (anisotropic collar)
itself, after reading the sibling ledgers to avoid rebuilding an existing (axis, value); no human approved that
choice in advance. It did not contact DrivenData or any leaderboard, did not submit, and holds no score: R0's
0.2778 remains a CLAIM and every predicted change is a MODEL. Competition rasters stay in ignored
`.cache/gems_data/` and `releases/`; nothing competition-derived is in this commit or any release. The human
still owns the slot decision, the receipt, the data-use review and the live target.
