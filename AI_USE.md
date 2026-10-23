# AI use disclosure — 2026-10-23 (session 2026-10-23b, AXIS = MASS)

AI authored, in this session: `src/mass.py` (exclusive-credit ranking and its algebra),
`scripts/build_mass_shadow.py`, `tests/test_mass_shadow.py`, the three candidate rasters (local,
ignored), the mechanism cards, the slot plan, the submission packet, the ledger rows and the
`evidence/mass_build_receipt.json` / `evidence/manifest_verification.json` receipts. AI re-verified all
26 pinned input hashes, rebuilt R0 byte-identically (zeros `c55bafc4…`, NaN `baeae321…`), selected the
axis and the 10 / 20 / 30 % doses, and re-ran the format gate and the unit tests.

Prior sessions authored `src/`, `scripts/restore_data.py`, `scripts/build_r0_variants.py`, the PRUNE
candidates and their documentation; that work is retained unchanged.

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
