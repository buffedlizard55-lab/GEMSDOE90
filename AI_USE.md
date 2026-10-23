# AI use disclosure — 2026-10-23

AI assistance authored the session's reproducibility code (`scripts/restore_data.py`, `scripts/build_r0_variants.py`), unit tests, experiment metadata, mechanism cards, ledger rows derived from the supplied owner raw-paste ledger, and planning/submission documentation. AI also performed the pinned-file integrity checks and the deterministic PRUNE builds described in `evidence/build_receipt.json`.

The human's brief supplied the objective, constraints, parent, quota rules, deadline, metric algebra, and allowed experiment axes. The agent selected PRUNE and the unused 3.5 / 4.5 / 5.5 px values after checking the available sibling ledgers; these are not human-approved slot choices. The agent did not contact DrivenData, submit a file, or claim a score. A human must review geology, provide current leaderboard/slot information and any portal receipts, and choose whether to submit.

Competition rasters remain under ignored `.cache/gems_data/` and local ignored `releases/`; they are not included in this public Git diff or any release. The owner-supplied mirror provenance and competition data-use terms have not been independently authenticated.
