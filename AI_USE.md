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

## Update 2026-10-23e (MASS add-direction session, branch `arena/c3061751-gemsdoe90`)

AI re-verified 26/26 pinned inputs and rebuilt R0 byte-identically, then authored `src/reach.py`,
`tests/test_reach.py`, `scripts/build_mass_infill.py`, the three `MASSadd*pctq50` candidates, the receipt
`evidence/mass_infill_receipt.json`, the cards `ledger/mechanism_cards_mass_infill.json`, the ledger rows, the
reservation block and the documentation edits. AI chose the axis (MASS) **and the direction (add)** after finding
that the deletion side is fully instrumented (10/20/30/40/48 % + random control) while every recorded add rung is
FIFO-ranked and region-isolated. AI set the adopted predictions (+0.008 / +0.014 / +0.022 MODEL) by discounting the
first-order model's raw output by 0.10 and documented why (the model assumes the truth set is an unbiased sample of
the H19-5 support; it is not). AI did not contact DrivenData or Dropbox, did not read the leaderboard, did not log
in, and did not submit. R0's 0.2778 remains a CLAIM.

**What the human must decide:** whether to spend a slot on the add direction before the drop direction has any
receipt; whether the block-quota evenness convention is acceptable as "not a patterned file"; and, if a slot is
spent, which dose. **What the human must supply:** `TOP_PUBLIC` with date, quota used/remaining, deadline
confirmation, R0's portal receipt, and a check that the chosen SHA-256 has never been uploaded.

## Session arena/5d47dcd0 (2026-10-23f, `AXIS=MASS`, add direction, placement contrast)

- **What AI wrote and executed:** re-verified 26/26 pinned inputs and rebuilt R0 byte-identically (`c55bafc4…` / `baeae321…`, 37,654 dots, d2.8 with 0-pixel difference); authored `src/mass_add.py`, `scripts/build_mass_add_variants.py`, `tests/test_mass_add.py`; built add rungs with a region-even per-5 km-block quota; ran the format gate on every raster from disk, the 82-test suite, and the SGMC PROXY; wrote `evidence/mass_add_receipt.json`, the ledger rows, reservations, mechanism cards, `SLOT_PLAN.md`, `docs/SUBMIT.md` §6, `docs/MECHANISM_CARDS.md`, `IRREGULARITIES.md` (IR90-24, IR90-25) and the `README.md` CURRENT STATE block only.
- **What AI rejected or withdrew:** `CONCENTRATION` at any dose (IR90-25, measured flat credit per block-density quintile, and R0's CV already above the brief's band); `MASSadd10pctGapmax` withdrawn before submission as a duplicate of main's `MASSadd10pctq50` (IR90-24) — the parallel session merged the same operator while this one was running. Rasters moved to `.cache/withdrawn/`; ledger row kept as an occupancy guard.
- **What the human decided / must decide:** the brief supplied the objective, parent, constraints and the axis menu; the agent chose the axis and values. The human must supply dated `TOP_PUBLIC`, quota state, deadline confirmation and portal receipts, review the added corridors geologically, and decide which single file to upload. The agent never contacted DrivenData, never read a leaderboard, never logged in and never submitted.
- **Not done:** no leakage canary re-run (no new feature entered placement); no bootstrap catalogue proxy (analytically zero for this axis — every addition is ≥ 3 px away with a 3 px kernel); no live receipt exists, so every Δ here is MODEL.

## Session 2026-10-23 (continuity-aware MASS, branch arena/0e9b3fd9-gemsdoe90)

**AI wrote/executed:** `src/continuity.py` (6 px link graph, articulation + 10-dot strand-floor eligibility, strand-survival instrument), `tests/test_continuity.py` (7 synthetic tests), `scripts/build_mass_continuity.py` (fail-closed reservation guard, exact-R0 rebuild, matched-count 20/30/40% builds, region-evenness + dual format gates, report-only catalogue hide-and-recover and SGMC PROXYs with bootstrap CIs, `--verify` byte-reproduction path), the three candidate pairs in ignored `releases/` (`66d961ba`, `885f6fee`, `92be4121`), `evidence/mass_continuity_receipt.json`, 26/26 pin verification via `scripts/restore_data.py`, three `BUILT` ledger rows, the `mass_continuity_20261023` reservations block, mechanism cards, submit packet §5, the merged Slot-2/3 conditional + session result in `SLOT_PLAN.md`, IR90-26/IR90-27, the README CURRENT STATE lines, and this disclosure.

**AI decided (agent-selected axis under the human's explicit delegation):** AXIS=MASS, value family = continuity-aware shadow drop. The human's brief said "pick your own session; do not prompt me over choosing an Axis." AI first re-audited sibling ledgers read-only via `gh api` (GEMSDOE84–92): all seven axes built, zero receipts, brief-literal CONCENTRATION-up built at four block sizes and read ≤ 0 on GEMSDOE86's SGMC MODEL at every dose. AI therefore built this repo's own previously-proposed-but-unbuilt CONTINUITY_AWARE_DOSE rung instead of re-cutting an occupied (AXIS, value) family, at doses matched to the recorded shadow ladder so each new file has a matched-count twin. AI also chose the 6 px (kernel-diameter) link over the earlier proposal's 5 px sketch, and recorded both instruments (IR90-27).

**Human must decide/supply:** dated TOP_PUBLIC, quota state, deadline confirmation, portal receipts (R0 first), geological map review of strand survivors vs deleted fragments at a stated link distance, and the merged Slot-1–3 order in `SLOT_PLAN.md` (main's add-direction ladder now leads; shadowcont-20 is the first drop-direction probe). AI did not contact DrivenData or Dropbox, did not scrape or log in, did not submit, and claims no score: R0's 0.2778 remains CLAIM and every predicted change (+0.009/+0.011/+0.013) is MODEL. Competition rasters remain only in ignored `.cache/gems_data/` and `releases/`; none is in this Git diff.
## Session 2026-10-23 (final current branch; agent-selected PRUNE after feasibility stops)

AI restored and SHA-256-verified all 26 pinned inputs, rebuilt R0 byte-identically, audited local and GitHub sibling ledgers for occupied `(AXIS,value)` pairs, and initially selected SNAP. AI withdrew SNAP before raster emission after a deterministic geometry check found 30 inherited dots with no legal >=3 px destination within 2 px (IR90-28). AI then built three delete-only anisotropic PRUNE probes, but withdrew them before submission after re-reading the brief's fixed-count refill requirement (IR90-29).

For the final three candidates AI authored `scripts/build_aniso_prune_along.py` and `tests/test_aniso_along.py`, generated six local Git-ignored rasters, froze MODEL predictions before running REPORT ONLY proxies, updated the ledger/reservations/mechanism cards, and wrote the slot plan and submission packet. The final files use A5 across strike, L=1.5/1.0/0.5 along strike, exact fixed-count H19-5 FIFO refill, and R0's >2 px baseline on every final dot. AI also retained the withdrawn probe generator, receipt, tests, and occupancy rows so the decision is auditable; those files are explicitly not candidates. AI did not contact DrivenData or Dropbox, read a leaderboard, log in, submit, or claim a score.

**Human decided/supplied:** the brief, R0, constraints, and quota rule. **Human must still supply/decide:** dated TOP_PUBLIC, slots used/remaining and total, official deadline confirmation, portal receipts, data-use review, geological review of retained continuations/refill ridges, whether any candidate is uploaded, and the ONE blind final. All predictions are MODEL; catalogue and SGMC diagnostics are PROXY; no local number is a live score.

## Session arena/5d4e4978 (2026-10-23e, agent-selected `AXIS=CONCENTRATION`)

**AI wrote and executed:** `src/concentration.py`, `scripts/build_concentration_variants.py`,
`tests/test_concentration.py`, the three local gitignored candidate rasters and their `-zeros` twins,
`evidence/concentration_build_receipt.json`, the concentration rows in `ledger/submissions.csv`, the
`concentration_reservations_20261023` block in `ledger/experiment_reservations.json`, the concentration
mechanism-card block, and the matching sections of `SLOT_PLAN.md`, `README.md` (CURRENT STATE only),
`docs/SUBMIT.md`, `docs/MECHANISM_CARDS.md`, `IRREGULARITIES.md` (IR90-30/31 after merge) and this disclosure.
AI also extended `scripts/restore_releases.py` to reproduce the 18 core candidate pairs recorded when this branch was cut (including the three concentration pairs) without triggering the duplicate-build guards; main's later candidates retain their own family builders.

**AI decided (not human-assigned):** selected CONCENTRATION after a read-only `gh api` audit of 79 public
`buffedlizard55-lab/GEMSDOE*` default branches (9 ledgers, 33 occupied concentration values) and selected
15 km blocks because the byte-identical R0 has density CV `0.5103`, inside the brief's reported `0.51–0.59`
band. AI chose the 10/15/20% dose ladder, the four-band pinned structural prior, the lowest/highest 35%
tails and the region-evenness gate. AI verified all 26 SHA-256 input pins, rebuilt R0 byte-identically
(`c55bafc4…` / `baeae321…`), re-read and validated all six output files from disk, reproduced their bytes
with `--verify`, and ran the report-only canary, catalogue hide/recover and SGMC controls as `PROXY` only.

**AI did not:** contact DrivenData or Dropbox, read the leaderboard, log in, submit, invent a live score, or
use hidden/public test truth. R0's `0.2778` remains a CLAIM; every predicted change is MODEL. Competition
rasters and data remain in ignored `.cache/gems_data/` and `releases/`, never in the public Git diff or a release.

**Human must decide/supply:** dated `TOP_PUBLIC`, weekly slot count, official deadline confirmation, R0 and
candidate submission receipts, data-use/terms review, geological review of the moved corridors, whether
the inherited 2.236 px parent collar is acceptable (IR90-31), and which single file (if any) to upload.

**Post-merge decision:** main advanced past the branch base and recorded IR90-25/26: R0 support credit is
nearly uniform, a fixed-count CONCENTRATION move loses ~0.98 and gains ~0.54 credit per dot, sibling
upward-concentration MODELs are non-positive, and the entity has zero receipts. This session's three
files remain BUILT occupancy/dose-response guards but are HELD from the next three slots; the integrated
MASS-add / continuity / PRUNE slot order in `SLOT_PLAN.md` is retained.

## Session arena/388fea70 (2026-10-23 CONC-strain, AXIS=CONCENTRATION, GEMSDOE90) — HELD after merge

- **What AI wrote and executed:** After a fresh-sandbox reset, AI re-installed the pinned venv, restored and SHA-256-verified all 26 manifest inputs, and rebuilt R0 byte-identically (zeros `c55bafc4…`, NaN `baeae321…`). It authored three fixed-count 37,654-dot CONCENTRATION variants on a label-agnostic geodetic strain-rate prior (band 4 `geod_2ndinv`, 5 km blocks, complementary 50% pools): `CONCstrain10`, `CONCstrain15`, and a matched-dose sign control `CONCstrainAway10`. It re-read every written raster from disk, ran a byte-reproduction `--verify` pass and the full test suite, and ran report-only diagnostics (leakage canary max symmetric AUC 0.570; catalogue hide-and-recover; SGMC control).
- **Merge-aware status:** a parallel session (main PR #20) had built a 15 km structural CONCENTRATION ladder using the SAME four filenames. AI renamed its own files to `src/concentration_strain5km.py`, `scripts/build_concentration_strain5km.py`, `tests/test_concentration_strain5km.py`, `evidence/concentration_strain5km_build_receipt.json` so both designs coexist, resolved all shared-file conflicts by union, and re-verified. Consistent with main IR90-25/26/30 (fixed-count concentration loses net support credit; parallel variants HELD from slots), these three files are kept as distinct `(parent,axis,value)` BUILT occupancy guards and HELD from slots; the away arm is a falsifier instrument only. IR90-32/33/34.
- **What AI did NOT do:** contact DrivenData or Dropbox, read the leaderboard, scrape scores, log in, submit any file, or invent any score/quota/target. R0's 0.2778 is CLAIM; every Δ is MODEL; canary/proxies are PROXY. Competition rasters stay in ignored `.cache/gems_data/` and `releases/`; the four *_strain5km source files are the only new tracked code.
- **Human must decide/supply:** adjudicate whether sibling repos GEMSDOE84–97 are ONE entity (quota risk, IR90-26/30/32), confirm deadline and slot count, supply dated TOP_PUBLIC and portal receipts, decide whether the strain5km occupancy guards add value or should be dropped as a near-duplicate, and choose which single file (if any) to upload from their registered account.

## Session arena/81d9c38f-gemsdoe90 (2026-10-24, agent-selected `AXIS=PRUNE`, one variant)

- **AI wrote and executed:** `src/collar.py` (exclusive max-plus credit, region-even quotas, capacity
  rebalance, max-marginal refill, two-scenario prediction), `scripts/build_prune_collar_gapmax.py`
  (`--build` / `--verify`), `tests/test_collar.py` (7 synthetic tests), the local gitignored raster pair
  `releases/h33-h33-2-b2-PRUNEcollar3p4Gapmax-20261024-e69532d5.tif` / `…-e69532d5-zeros.tif`,
  `evidence/prune_collar_gapmax_receipt.json`, one `ledger/submissions.csv` row, the IR90-37/38/39/40 entries,
  the mechanism card, and the matching sections of `SLOT_PLAN.md`, `README.md` (CURRENT STATE only),
  `docs/SUBMIT.md` and this disclosure.
- **AI decided (not human-assigned):** selected PRUNE after a read-only `gh api` audit of sibling ledgers
  (GEMSDOE84–94) and a byte-identical R0 rebuild; measured that every free arrangement/dose knob has
  < 0.010 headroom (IR90-37) and therefore built **one** variant instead of three (IR90-40): the smallest
  unoccupied collar radius (3.4 px) with a max-marginal refill, because that isolates the one quantity the
  entity has measured live (the collar) and repairs the refill policy that was never measured (FIFO 0.57 vs
  max-marginal 1.30 support credit per dot). AI verified all 26 SHA-256 pins, rebuilt R0 byte-identically
  (`c55bafc4…` / `baeae321…`), re-read and validated both rasters from disk, reproduced their bytes with
  `--verify`, and ran the report-only canary and catalogue hide-and-recover instruments.
- **AI did not:** contact DrivenData or Dropbox, fetch a competition page, read or scrape the leaderboard,
  log in, submit, invent any score/quota/target, or use test truth of any kind. R0's `0.2778` is a CLAIM;
  the prediction is MODEL; both proxies are PROXY; the catalogue hide-and-recover value of 0.0 is a documented
  structural artefact (IR90-38), not evidence.
- **Human must decide/supply:** dated `TOP_PUBLIC`, slots used/remaining, official deadline confirmation,
  R0 and candidate portal receipts, data-use review, whether a 3.4 px collar step is worth a slot at all
  (IR90-39: the refill measurement is the session's result, not a new dose), and which single file — if any —
  to upload from their own registered account.
## Session arena/5d597521 (2026-10-24, agent-selected AXIS=SPACING, GEMSDOE90)

**AI wrote:** `src/spacing.py` (crowding rank, local respacing operator, spacing statistics),
`scripts/build_spacing_variants.py` (build/verify, ledger/reservation writers, report-only
diagnostics), `tests/test_spacing.py`, the three ledger rows, the `spacing` mechanism cards in
`ledger/mechanism_cards.json`, the `spacing_reservations_20261024` block, the receipt
`evidence/spacing_build_receipt.json`, and the matching sections of `docs/MECHANISM_CARDS.md`,
`docs/SUBMIT.md`, `SLOT_PLAN.md`, `IRREGULARITIES.md` (IR90-35/36) and this file. AI re-verified
26/26 pinned inputs by SHA-256, rebuilt R0 byte-identically (zeros `c55bafc4…` / NaN `baeae321…`),
audited sibling SPACING values read-only via `gh api` (GEMSDOE84-88/91/92), re-read every written
raster from disk, reproduced the bytes with `--verify`, and ran the full test suite.

**AI decided (agent-selected axis, not assigned):** SPACING, in a local kernel-scale form. The
brief's global trio (lattice / Poisson-disk / along-strike) and ring-2 micro-moves are already
built by siblings; MASS, CONCENTRATION, PRUNE and RELIEF ladders are complete in this repo; SNAP
is proven infeasible (IR90-28). AI set the doses (5/10/15%), the crowding rank, the 15 px window
and the 2.8 px separation floor, measured the exact support-credit balance (-87/-284/-496) before
freezing predictions (0.000 / -0.001 / -0.002 MODEL), and held all three files from slots because
the balance and both PROXYs say local arrangement is exhausted. AI did not contact DrivenData or
Dropbox, did not read the leaderboard, did not log in, and did not submit. R0's 0.2778 remains a
CLAIM; every predicted change is a MODEL; canary/hide-recover/SGMC numbers are PROXY.

**Human must decide/supply:** dated `TOP_PUBLIC`, quota used/remaining (one entity, 3/week),
deadline confirmation (2026-12-03 UNVERIFIED), R0's portal receipt and receipts for any uploaded
file, a geological review of whether crowded-dot clusters (possible step-overs/intersections) may
be respaced at all, whether the inherited 2.236 px floor is acceptable (IR90-36), and which single
file (if any) to upload from their own registered account. The agent's recommendation is to keep
the SPACING files held and run the MASS-add / continuity / PRUNE order in `SLOT_PLAN.md` first.
## Session arena/b5ea0544 (2026-10-24 RELIEF basin<->piedmont, AXIS=RELIEF, GEMSDOE90)

- **What AI wrote and executed:** AI chose the AXIS itself (RELIEF) after reading the ledger, reservations and
  SLOT_PLAN, and ran a read-only `gh api` audit of every reachable sibling ledger (GEMSDOE84-89, 91, 92; 93-101
  have no ledger): 27 RELIEF rows covered range->piedmont, range->basin, piedmont->range and basin->range, with
  ZERO basin->piedmont or piedmont->basin pairs under any naming (IR90-41). AI re-installed the pinned venv,
  restored and SHA-256-verified all 26 manifest inputs (70.6 s), rebuilt R0 byte-identically
  (`c55bafc4…` zeros / `baeae321…` NaN), restored the 18 core release pairs with matching hashes, and authored
  `scripts/build_relief_s2_variants.py` plus `tests/test_relief_s2.py` using the unchanged pinned
  `src/relief.py` operator. It built three fixed-count 37,654-dot files — `RELIEFp2b12p5pct` (pred +0.003
  MODEL), `RELIEFp2b15pct` (+0.004), and direction control `RELIEFb2p10pct` (−0.002) — re-read every raster
  from disk, passed the `src.validate` format gate on all six, ran a byte-reproduction `--verify`, the donor
  5 km region-evenness gate and the full test suite (120 passed), and ran the report-only leakage canary
  (max symmetric AUC 0.5703), catalogue hide/recover and SGMC controls as PROXY only. Predictions were frozen
  in the builder before any proxy ran.
- **What AI did NOT do:** contact DrivenData or Dropbox, read the leaderboard, scrape scores, log in, submit
  any file, use test truth, or invent any score/quota/target. R0's 0.2778 remains a CLAIM; every predicted
  change is MODEL; canary/proxies are PROXY, never gates or scores. Competition rasters stay in ignored
  `.cache/gems_data/` and `releases/`; only code, JSON receipts and Markdown are in the Git diff.
- **Human must decide/supply:** dated TOP_PUBLIC, weekly slot count and total used, deadline confirmation,
  R0 and any candidate portal receipts, data-use/terms review, geological review of the moved corridors,
  whether the inherited 2.236 px collar on untouched dots is acceptable (IR90-42), entity-scope/quota
  adjudication across sibling repos (IR90-08/26/35), and which single file (if any) to upload from their
  registered account.

## Session 2026-10-24 (`arena/96081fbe`, lane H1 learned surface)

AI wrote `docs/HYPOTHESES_20261024.md` (5 ranked hypotheses before implementation), `src/holdout.py`,
`src/features90.py`, `src/emission90.py`, `scripts/run_lane90.py`, `scripts/build_site90.py`,
`tests/test_holdout90.py`, the generated site (`docs/index.html` + `docs/downloads/`), and the
`evidence/lane90_*` receipts/run card; it selected hypothesis H1 itself, restored and SHA-256-verified
all 26 pinned inputs, ran the leakage canary and the 5-fold 25 km-block hide-and-recover evaluation,
built and format-gated the candidate, and appended the ledger/docs rows. AI decided the 40,000-dot
budget (declining to extrapolate the holdout budget sweep to 60k, reasoning recorded in
`evidence/lane90_final_receipt.json`) and the density-baseline treatment of the dot-overlap
uniqueness rule (IR90-43, all raw numbers published). At the owner's explicit request the team's own
prediction TIF is committed under `docs/downloads/` for one-click download (IR90-44); competition
input rasters remain in ignored `.cache/gems_data/` and candidate rasters in ignored `releases/`.
AI did not contact DrivenData/Dropbox, read the leaderboard, log in, submit, or claim a score:
0.2778 remains a CLAIM, all new numbers are HOLDOUT-DTI. Human owns slot selection, upload, receipts,
dated TOP_PUBLIC/quota, deadline confirmation, and data-use review.
