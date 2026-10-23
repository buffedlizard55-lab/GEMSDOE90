# AI use disclosure — 2026-10-23

AI assistance authored the prior blocked pipeline now retained under `src/` and the current reproducibility code (`scripts/restore_data.py`, `scripts/build_r0_variants.py`), unit tests, experiment metadata, mechanism cards, ledger rows derived from the historical owner raw-paste ledger, and planning/submission documentation. AI also performed pinned-file integrity checks, exact R0 rebuild validation, and deterministic PRUNE builds described in `evidence/build_receipt.json`. The earlier pipeline's missing-input blocker is superseded by the complete pinned-manifest workflow; the old `src.build_prune` inputs are not used for these built candidates.

The human's brief supplied the objective, constraints, parent, quota rules, deadline, metric algebra, and allowed experiment axes. The agent selected PRUNE and the unused 3.5 / 4.5 / 5.5 px values after checking the available sibling ledgers; these are not human-approved slot choices. The agent did not contact DrivenData, submit a file, or claim a score. A human must review geology, provide current leaderboard/slot information and any portal receipts, and choose whether to submit.

Competition rasters remain under ignored `.cache/gems_data/` and local ignored `releases/`; they are not included in this public Git diff or any release. The owner-supplied mirror provenance and competition data-use terms have not been independently authenticated.

## Update 2026-10-23 (reproducibility pass, clean sandbox)

AI added `scripts/restore_releases.py`, which re-emits the three already-recorded PRUNE candidates from the pinned inputs and fails closed unless the bytes match the SHA-256 in `evidence/build_receipt.json` and `ledger/submissions.csv`; AI also added two ledger-consistency tests and this note. No new (AXIS, value) pair was created, no candidate was altered, and `scripts/build_r0_variants.py` was left byte-identical (SHA-256 `06f667c1…`, still pinned in both receipts) so the recorded generator hash stays valid. AI re-verified 26/26 input pins, rebuilt R0 byte-identically, reproduced the d2.8 ranking with 0 px difference, re-ran the format gate on all six files and the full test suite. AI did not contact DrivenData, submit, or claim any score.

## Update 2026-10-23 (SNAP cross-strike session)

AI selected the session axis (SNAP), designed the edit, wrote `scripts/build_snap_variants.py`, its unit/consistency tests (`tests/test_snap_variants.py`), and the three arms; AI also audited the SNAP values already recorded in the sibling repositories GEMSDOE78–101 with read-only `gh api` calls (ledger contents only, no leaderboard access, no submission), re-verified all 26 pins, rebuilt R0 byte-identically, and re-emitted all six candidate pairs to their recorded hashes.

**What the AI decided:** the axis (SNAP over MASS / CONCENTRATION / PRUNE / RELIEF / SPACING, all of which are already built in sibling ledgers with many values), the cross-strike-only search (45° half-disc about a PCA normal from the 8 nearest parent dots), the two-source consensus edge field (`tmi_hg` + `iso_grav_anom_hg`, named in the GeoTIFF band descriptions and rank-normalised then smoothed at σ = 1.2 px), the 2 px cap, the 2 px minimum spacing constraint, and the confidence ladder (ε ×0.25 / ×1 / ×4) that distinguishes the three arms. Predictions are MODEL and deliberately small (+0.001…+0.004).

**What the human must decide:** whether to spend slots at all, which arm to submit, and whether the owner-mirrored competition inputs may be used/shared under the terms (IR90-02). The AI did not contact DrivenData or dropbox, did not submit, did not claim any score, and did not use labels or public-test endpoints.

**Honesty note:** the edge field is a *relative* rank consensus, not a fault probability; mean displacement is 2.00 px in all three arms (the smoothed consensus rises monotonically over 2 px for most dots), so the ladder tests *which* dots move, not how far. The AI's own measurement showed the H19-5 support is exhausted, which bounds every remaining menu axis to about ±0.01 of live score; that finding is recorded in SLOT_PLAN.md rather than hidden.
