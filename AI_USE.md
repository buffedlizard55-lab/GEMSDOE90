# AI use disclosure — 2026-10-23

AI assistance authored the prior blocked pipeline now retained under `src/` and the current reproducibility code (`scripts/restore_data.py`, `scripts/build_r0_variants.py`), unit tests, experiment metadata, mechanism cards, ledger rows derived from the historical owner raw-paste ledger, and planning/submission documentation. AI also performed pinned-file integrity checks, exact R0 rebuild validation, and deterministic PRUNE builds described in `evidence/build_receipt.json`. The earlier pipeline's missing-input blocker is superseded by the complete pinned-manifest workflow; the old `src.build_prune` inputs are not used for these built candidates.

The human's brief supplied the objective, constraints, parent, quota rules, deadline, metric algebra, and allowed experiment axes. The agent selected PRUNE and the unused 3.5 / 4.5 / 5.5 px values after checking the available sibling ledgers; these are not human-approved slot choices. The agent did not contact DrivenData, submit a file, or claim a score. A human must review geology, provide current leaderboard/slot information and any portal receipts, and choose whether to submit.

Competition rasters remain under ignored `.cache/gems_data/` and local ignored `releases/`; they are not included in this public Git diff or any release. The owner-supplied mirror provenance and competition data-use terms have not been independently authenticated.

## Update 2026-10-23 (reproducibility pass, clean sandbox)

AI added `scripts/restore_releases.py`, which re-emits the three already-recorded PRUNE candidates from the pinned inputs and fails closed unless the bytes match the SHA-256 in `evidence/build_receipt.json` and `ledger/submissions.csv`; AI also added two ledger-consistency tests and this note. No new (AXIS, value) pair was created, no candidate was altered, and `scripts/build_r0_variants.py` was left byte-identical (SHA-256 `06f667c1…`, still pinned in both receipts) so the recorded generator hash stays valid. AI re-verified 26/26 input pins, rebuilt R0 byte-identically, reproduced the d2.8 ranking with 0 px difference, re-ran the format gate on all six files and the full test suite. AI did not contact DrivenData, submit, or claim any score.

## Update 2026-10-23 (SNAP vertical-gradient session)

AI selected SNAP after auditing the local and six sibling ledgers, authored `src/snap.py` and `scripts/build_snap_vertical.py`, built three exact-distinct gain-gated variants, added synthetic and receipt-consistency tests, and wrote their mechanism cards, ledger rows and submission/slot documentation. AI used only manifest-pinned inputs, verified all 26 SHA-256 pins and exact R0, used seed 20261023 only for the report-only canary sample, and computed the SGMC report under the repository's stated DTI assumptions. AI did not contact DrivenData, submit, scrape a leaderboard, or claim a score.

The human's brief supplied the axis rules and constraints. The human has not approved these slot choices. AI marked all three outputs LOCAL ONLY because the inherited R0 collar fails the general ≥3 px rule; a human must decide eligibility, review the structural-geology confounders, and supply current leaderboard/quota/deployment controls and any receipts. Competition rasters remain ignored and are not part of the Git diff.
