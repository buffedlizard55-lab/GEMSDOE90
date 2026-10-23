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

## Update 2026-10-23b (MASS shadow-dose session)

AI authored `src/mass.py`, `scripts/build_mass_shadow.py`, `tests/test_mass_shadow.py`, the three MASS candidates, `evidence/mass_build_receipt.json` and the MASS documentation. The three PRUNE candidates from the earlier session are unchanged and remain in `releases/` and in the ledger.

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

## Update 2026-10-23c (high-dose MASS session, GEMSDOE90)

**AI wrote:** `scripts/build_mass_high_dose.py` (40 % / 48 % shadow arms and the seeded random 40 % control,
the 5 km-block region-evenness gate, the report-only strand-continuity and rejected-probe analysis),
`tests/test_mass_high_dose.py`, the `mass_high_dose` block of `ledger/experiment_reservations.json`,
`evidence/mass_high_dose_receipt.json`, three ledger rows, and the matching text in `SLOT_PLAN.md`,
`docs/SUBMIT.md`, `docs/MECHANISM_CARDS.md`, `IRREGULARITIES.md` (IR90-15…17) and the `README.md`
CURRENT STATE block. AI also changed one line of `scripts/build_mass_shadow.py` so its ledger writer replaces
only its own row ids instead of dropping every `axis=MASS` row (a later MASS session's rows can no longer be
deleted by a rebuild); that script was then re-run with `--verify`, which reproduced its three pairs
byte-identically and re-pinned its generator hash.

**AI decided (agent-selected axis, not assigned):** MASS. It continued the in-repo shadow ladder above 30 %
because that ladder is the only mechanism in the ledger with a recorded positive prior, and spent the third
arm on a credit-blind random control because no indexed repository has one and the session rule treats a
sub-0.01 change as no evidence. It rejected two arms before any submission — FIFO-order drops
(region-isolated, IR90-15) and a 50 % shadow drop (IR90-17) — and deleted the one raster it had already built
for the first. It did not contact DrivenData, scrape anything, submit a file, or claim a score; no
`TOP_PUBLIC`, quota or deadline figure was invented.

**Human must decide/supply:** the dated `TOP_PUBLIC`, quota state, deadline confirmation, submission-page
receipts, whether the final submission may repeat an already-scored file, and a review of the competing
prediction — the shadow ranking deletes all 838 of R0's ≥ 1 km strands while the random control keeps 136.

## Session arena/307b04fc (2026-10-23d, AXIS=MASS dose ladder on the parent's FIFO ranking)

AI authored `scripts/build_mass_variants.py`, the three MASS rungs (`drop5pct-tail`, `add5pct-next`, `add20pct-next`) and their mechanism cards, `ledger/mechanism_cards_mass.json`, `evidence/mass_dose_ladder_receipt.json`, and this session's ledger rows, reservation audit and doc sections. AI selected AXIS=MASS and the rung values after auditing sibling ledgers GEMSDOE84-101; the canonical ±10 %/−20 %/swap pairs were already built elsewhere. AI verified the 26 pinned inputs, rebuilt R0 byte-identically, ran the report-only catalogue hide-and-recover and SGMC control PROXYs (seed 20261023), and cited the earlier leakage canary on identical inputs. After merging origin/main, AI measured the variants against the region-evenness gate (Hard Constraint #5) and **withdrew all three** (IR90-20): the parent's FIFO ranking deletes an 81-block SE hole at the 5 % drop and adds only into northern strips. Rasters were moved out of `releases/`; ledger rows were kept as WITHDRAWN occupancy guards; the predictions in them are a record of what was expected, not a promotion. AI also deleted its duplicate `scripts/regen_prune_rasters.py` in favour of main's `scripts/restore_releases.py`. AI did not contact DrivenData, submit a file, or claim a score. The human decides slot order (SLOT_PLAN.md defers to the merged shadow/random + aniso-PRUNE plan) and supplies TOP_PUBLIC, quota state, deadline confirmation and receipts.
## Update 2026-10-23d (`AXIS=RELIEF` session, GEMSDOE90)

- **What AI wrote and executed:** Selected `AXIS=RELIEF` per the prompt instruction not to prompt the human over axis choice; audited the 19 `training_features.tif` bands; authored `src/relief.py`, `scripts/build_relief_variants.py`, and `tests/test_relief.py`; extended `scripts/restore_releases.py` and `tests/test_r0_variants.py` so both the prior `PRUNE` candidates and the 3 new fixed-count `RELIEF` candidates (`RELIEFr2p12p5pct`, `RELIEFr2b10pct`, `RELIEFp2r15pct`) are reproducibly verified; ran all 26 SHA-256 input checks, byte-identical R0 rebuild (`c55bafc4…` / `baeae321…`), `d2.8` and `d1.5` 0-pixel-diff thinning checks, disk re-read format validation (`src/validate.py`), report-only diagnostics (19-band + `relief_idx` leakage canary, 20×20 km spatial-block catalogue hide-and-recover `PROXY`, and off-catalogue SGMC `PROXY`), and updated `ledger/submissions.csv`, `ledger/experiment_reservations.json`, `ledger/mechanism_cards.json`, `evidence/relief_build_receipt.json`, `evidence/releases_restore_receipt.json`, `README.md` (`CURRENT STATE` block only), `SLOT_PLAN.md`, `docs/SUBMIT.md`, `docs/MECHANISM_CARDS.md`, and `IRREGULARITIES.md`.
- **What the human decided / must decide:** The human defined the competition brief, parent `h33-h33-2-b2`, constraints, and allowed axes. Before any upload, the human must verify competition data-use terms, confirm the official deadline and entity slot count, supply dated `TOP_PUBLIC` and portal score receipts (for R0 and any uploaded file), review removed/added fault corridors geologically, and choose which single file (if any) to upload from their registered account.

## Session arena/5d47dcd0 (2026-10-23e, `AXIS=MASS`, ADD direction)

- **What AI wrote and executed:** re-verified all 26 pinned inputs (`evidence/manifest_verification.json`) and rebuilt
  R0 byte-identically (`c55bafc4…` / `baeae321…`, 37,654 dots, d2.8 reproduced with 0-pixel difference); audited the
  ledger and the 7 axis families; selected `AXIS=MASS` in the never-built ADD direction; authored `src/mass_add.py`,
  `scripts/build_mass_add_variants.py`, `tests/test_mass_add.py`; built three add rungs (`MASSadd10pctGapmax`,
  `MASSadd10pctBlocknext`, `MASSadd20pctBlocknext`) with a region-even per-5 km-block quota; ran the format gate on all
  six rasters from disk, the 74-test suite, the analytic catalogue-proxy statement and the SGMC PROXY; wrote
  `evidence/mass_add_receipt.json`, the ledger rows, reservations, mechanism cards, `SLOT_PLAN.md`, `docs/SUBMIT.md`,
  `docs/MECHANISM_CARDS.md`, `IRREGULARITIES.md` (IR90-21, IR90-22) and the `README.md` CURRENT STATE block only.
- **Rejected before building:** `CONCENTRATION` at any dose (IR90-22) — measured mean marginal support credit is flat
  (0.543–0.646) across block-density quintiles while each dot's exclusive credit is 0.980–0.997, so a fixed-count
  density move loses ~0.98 and gains ~0.54 per dot, and R0's CV (0.901 at 5 km / 0.635 at 10 km) already exceeds the
  brief's quoted best-file band. Also rejected: any literal FIFO "next-ranked" placement (IR90-20).
- **What the human decided / must decide:** the brief supplied the objective, parent, constraints and the axis menu;
  the agent chose the axis and the three values (the brief forbids asking). The human must supply the dated
  `TOP_PUBLIC`, quota state, deadline confirmation and portal receipts; review the added corridors geologically;
  decide whether added off-collar mass may be submitted at all; and choose which single file to upload. The agent
  never contacted DrivenData, never read a leaderboard, never logged in and never submitted.
- **Not done:** no leakage canary re-run (no new feature entered placement); no bootstrap catalogue proxy (analytically
  zero for this axis); no live receipt exists, so every Δ here is MODEL, not a score.
