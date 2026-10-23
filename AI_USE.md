# AI use disclosure — 2026-10-23 (session 2026-10-23b, AXIS = MASS)

AI authored, in this session: `src/mass.py` (exclusive-credit ranking and its algebra),
`scripts/build_mass_shadow.py`, `tests/test_mass_shadow.py`, the three candidate rasters (local,
ignored), the mechanism cards, the slot plan, the submission packet, the ledger rows and the
`evidence/mass_build_receipt.json` / `evidence/manifest_verification.json` receipts. AI re-verified all
26 pinned input hashes, rebuilt R0 byte-identically (zeros `c55bafc4…`, NaN `baeae321…`), selected the
axis and the 10 / 20 / 30 % doses, and re-ran the format gate and the unit tests.

Prior sessions authored `src/`, `scripts/restore_data.py`, `scripts/build_r0_variants.py`, the PRUNE
candidates and their documentation; that work is retained unchanged.

Competition rasters remain under ignored `.cache/gems_data/` and local ignored `releases/`; they are not included in this public Git diff or any release. The owner-supplied mirror provenance and competition data-use terms have not been independently authenticated.

**What the human decided / must decide:** the brief supplied the objective, constraints, parent, quota
rules, deadline, metric algebra and the list of allowed axes. The human has not approved an axis or a
dose, and the agent chose MASS and its three doses after checking the five sibling ledgers for
`(AXIS, value)` collisions. A human must review the geology of the deleted dots, supply the leaderboard
and quota facts, supply R0's receipt, and choose whether and which file to submit.

**What the AI did not do:** query DrivenData or Dropbox, read the leaderboard, log in, submit, or claim
a score. R0's 0.2778 remains CLAIM. Every number labelled MODEL is a bracketed projection from the
brief's algebra, not a measurement.

**Data handling:** competition and external rasters stay under ignored `.cache/gems_data/`; built
rasters stay under ignored `releases/`. Neither is in this Git diff or any release. The input mirrors
are owner-supplied and not organizer-authenticated; the competition's data-use terms have not been
independently checked (IR90-02).

## Update 2026-10-23 (reproducibility pass, clean sandbox)

AI added `scripts/restore_releases.py`, which re-emits the three already-recorded PRUNE candidates from the pinned inputs and fails closed unless the bytes match the SHA-256 in `evidence/build_receipt.json` and `ledger/submissions.csv`; AI also added two ledger-consistency tests and this note. No new (AXIS, value) pair was created, no candidate was altered, and `scripts/build_r0_variants.py` was left byte-identical (SHA-256 `06f667c1…`, still pinned in both receipts) so the recorded generator hash stays valid. AI re-verified 26/26 input pins, rebuilt R0 byte-identically, reproduced the d2.8 ranking with 0 px difference, re-ran the format gate on all six files and the full test suite. AI did not contact DrivenData, submit, or claim any score.

## Update 2026-10-23 (reproducibility pass, clean sandbox)

AI added `scripts/restore_releases.py`, which re-emits the three already-recorded PRUNE candidates from the pinned inputs and fails closed unless the bytes match the SHA-256 in `evidence/build_receipt.json` and `ledger/submissions.csv`; AI also added two ledger-consistency tests and this note. No new (AXIS, value) pair was created, no candidate was altered, and `scripts/build_r0_variants.py` was left byte-identical (SHA-256 `06f667c1…`, still pinned in both receipts) so the recorded generator hash stays valid. AI re-verified 26/26 input pins, rebuilt R0 byte-identically, reproduced the d2.8 ranking with 0 px difference, re-ran the format gate on all six files and the full test suite. AI did not contact DrivenData, submit, or claim any score.

## Update 2026-10-23b (MASS shadow-dose session)

AI authored `src/mass.py`, `scripts/build_mass_shadow.py`, `tests/test_mass_shadow.py`, the three MASS candidates, `evidence/mass_build_receipt.json` and the MASS documentation. The three PRUNE candidates from the earlier session are unchanged and remain in `releases/` and in the ledger.

## Update 2026-10-23c (high-dose MASS session)

**AI wrote:** `scripts/build_mass_high_dose.py` (the 40 % / 48 % shadow arms and the seeded random 40 %
control, the 5 km-block region-evenness gate, the report-only strand/continuity and rejected-probe
analysis), `tests/test_mass_high_dose.py`, the `mass_high_dose` block of
`ledger/experiment_reservations.json`, `evidence/mass_high_dose_receipt.json`, the three ledger rows, and
the related text in `SLOT_PLAN.md`, `docs/SUBMIT.md`, `docs/MECHANISM_CARDS.md`, `IRREGULARITIES.md`
(IR90-07…10) and the `README.md` CURRENT STATE block. AI also made one line-level change to
`scripts/build_mass_shadow.py`: its ledger writer now replaces only its own row ids instead of dropping
every `axis=MASS` row, so a later MASS session's rows cannot be deleted by a rebuild. That changed the
recorded generator hash of that script, so it was re-run with `--verify`, which reproduced its three
pairs byte-identically and re-pinned the hash.

**AI decided (agent-selected axis, not assigned):** MASS. It chose to continue the in-repo shadow ladder
above 30 % because that ladder is the only mechanism in the ledger with a recorded positive prior, and to
spend the third arm on a credit-blind random control because no repository has one and the session rule
treats a sub-0.01 change as no evidence. It rejected two arms before any submission — FIFO-order drops
(region-isolated; IR90-07) and a 50 % shadow drop (IR90-10) — and deleted the one raster it had already
built for the first. It did **not** contact DrivenData, scrape anything, submit a file, or claim a score;
no `TOP_PUBLIC`, quota or deadline figure was invented.

**Human must decide/supply:** whether these arms are worth a slot, the dated `TOP_PUBLIC`, quota state,
deadline confirmation, submission receipts, and whether the final submission may repeat an already
scored file. Human should also review the competing prediction: the shadow ranking deletes all 838 of
R0's ≥ 1 km strands while the random control keeps 136.

