# SLOT PLAN — Promoted Independent Multi-Physics Discovery Candidate (`H90-1`) + Legacy `R0` Perturbation Ladder (2026-10-24)

**Official Competition Controls (verified live 2026-10-24 UTC):**
- **Deadline:** `2026-12-03T23:59:00Z` ([DrivenData Competition #306](https://www.drivendata.org/competitions/306/competition-doe-gems/)).
- **Public Leaderboard Top (`ORGANIZER-CONFIRMED`, 2026-10-24):** `#1 xiaofanhu = 0.4413`, `#2 cfld__ = 0.3916`, `#3 Batik Shirt Brothers = 0.3904` ([Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)).
- **Entity Best (`USER-REPORTED`, `ledger/submissions.csv`):** `R0` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, `GEMSDOE32`, `37,654` dots) = `0.2778`.
- **Quota Rule:** Maximum **3 submissions per rolling 7-day window** across one participating entity ([DOE/NLR Official Rules `96647.pdf`](https://docs.nlr.gov/docs/fy26osti/96647.pdf)).

## Promoted Independent Multi-Physics Candidate (`arena/783b0fc5-gemsdoe90`, `AXIS=DISCOVERY`)

Prior `GEMSDOE90` builds (`PRUNE`, `MASS`, `RELIEF`, `CONCENTRATION`, `SPACING`) edited only the frozen `H19-5`/`R0` dot support (`<0.010` measured headroom, `IR90-25/37`, and `>85%` 3-px overlap with `R0`). Lane H90 trained a genuinely independent, zero-input-submission multi-physics fault discovery model (`H90-1: CC-MPST-Submod300`) that passed **15 / 15 automated format, range `[0, 1]`, leakage-canary, registry-uniqueness, and paired spatial-block `HOLDOUT-DTI` promotion gates** (and is mutually orthogonal to concurrent Lane H1: `Spearman rho = 0.0279`, `mutual 3-px overlap = 0.4339 <= 0.70`, `forward 3-px overlap = 0.5101 <= 0.70`):

| Promoted Deliverable | Submission Name & Form Note (`92/140` chars) | SHA-256 (`.tif` / `.zip`) | `HOLDOUT-DTI` (`gems57-pooled-hide-v2`, `seeds=20+21`) | Uniqueness vs 20 Registry Rasters + Concurrent H1 | Gate Verdict |
|---|---|---|---|---|---|
| `docs/downloads/gemsdoe90-h90-cc-mpst-submod38k-20261024-d76ac964-zeros.tif` (`38,000` binary dots, `d_cat > 2.0 px`, `132,454 B`) | Name: `GEMSDOE90-H90-CC-MPST-D76AC964`<br>Note: `GEMSDOE90 H90 CC-MPST+Coulomb+Submod300 \| 38000 dots B>2 \| HOLDOUT-DTI all=0.1068 det=0.1059` | `.tif`: `637f067efc8b7822af9be58fff3f9c3a02bc41bd699e22c622ecf90bc7046e51`<br>`.zip`: `85fffcd6ba9c46a99b03d69ddf42b214a8eca1507f4840f47344979a2d75464d` | `mode=all`: **`0.10681 [0.09657, 0.11671]`** (`n=22,641`; paired `Δ` vs `fair-R0` `0.09096` = **`+0.01585 [0.00625, 0.02534]`**)<br>`mode=detached`: **`0.10586 [0.09294, 0.11802]`** (`n=22,619`) | Canary `max AUC = 0.6263 <= 0.90`; Surface `|ρ| = 0.1037 <= 0.90`; Dots `|ρ| = 0.0310 <= 0.90`; Mutual 3px `= 0.4339 <= 0.70`; Non-lattice fwd 3px `= 0.6612 <= 0.70`; **`64.08%` new dots `>300 m` outside `R0`** | **`PROMOTE`** (`evidence/h90_run_card.json`) |

## Concurrent Session 2026-10-24 addendum (lane H1, `arena/96081fbe`): NEW SURFACE candidate — human selector decides

`docs/downloads/gems90-h1learnedb-poisson40k-20261024T073540Z-04af0861-zeros.tif` (SHA-256 `04af0861…f81`;
NaN twin `…-nan.tif` `e340912f…`): 40,000 dots on a fold-clean learned fault-ness surface
(`docs/HYPOTHESES_20261024.md`) with Poisson `2.8 px` emission. It beat the fold-clean incumbent recipe in **all 5** 25 km holdout folds
(pooled HOLDOUT-DTI 0.1870 [0.1622, 0.2105] vs 0.1402; paired **+0.0468 [0.0176, 0.0762]**,
60,988 withheld positives). Cross-lane check vs `Lane H90` (`637f067e…`): `Spearman rho = 0.0279`, `mutual 3-px = 0.4339`, `forward 3-px = 0.5101` — the two independent discovery lanes share only ~43%–51% 300 m halos because `Lane H90` adds `TMI_up150` shallow hydrothermal demagnetization, odd-vs-even step polarity, nested out-of-quadrant 2D steerable worms, Anderson Mode-II Coulomb wing-crack cones & relay bridges, and exact CELF `R=300 m` submodular allocation. Human selector chooses how to sequence weekly slots across `Lane H90`, `Lane H1`, and the legacy `R0` ladder below; nothing here was submitted by any agent.

---

**Legacy `R0` Perturbation Context (2026-10-23/24):** `h33-h33-2-b2` / `GEMSDOE32`, 37,654 dots; 0.2778 is **CLAIM**, not a receipt. Live `|Δ|<0.010` is **no evidence**; private chunks can differ. Never repeat an exact hash or a `(parent, axis, value)` pair.

## Next 3 slots (NaN primary only; human decides)

| Order | Candidate(s), predicted Δ (`MODEL`) | Decision from receipt |
|---|---|---|
| **1** | `…MASSadd5pctq50-20261023-c4e6144c.tif` — **+0.008** | `Δ>=+0.010`: add sign pays; Slot 2 = q50-10. `Δ<=-0.010`: close adds for now; Slot 2 = continuity-aware drop **shadowcont20**. `|Δ|<0.010`: no evidence; Slot 2 = orthogonal fixed-count **A5/L1**. |
| **2** | Add branch: `…MASSadd10pctq50-20261023-5edc84de.tif` — **+0.014**. Negative-add branch: `…MASSshadowcont20pct-20261023-66d961ba.tif` — **+0.009**. Null-add branch: `…PRUNEanisoA5L1-20261023-cd2c60ce.tif` — **+0.005** | Add: rising `Δ` licenses q50-20; flat but positive favors matched-placement blocknext10; negative closes the ladder. Continuity: `Δ>=+0.010` → shadowcont40; `Δ<=-0.010` → shadow20 to separate dose from protection. PRUNE: `Δ>=+0.010` → L0.5; `Δ<=-0.010` → recorded A5/L2; null → shadowcont20. |
| **3** | Add: `…MASSadd20pctq50-20261023-f94efff4.tif` — **+0.022**, or matched-dose `…MASSadd10pctBlocknext-20261023-89d16c16.tif` — **+0.0044**. Continuity: `…MASSshadowcont40pct-20261023-92be4121.tif` — **+0.013** / `…MASSshadow20pct-20261023-c4ce118b.tif` — **+0.009**. PRUNE: `…PRUNEanisoA5L0p5-20261023-91ff3771.tif` — **+0.003** / recorded **A5/L2** / shadowcont20 | Take exactly one conditional arm. q50-20 requires two positive add receipts and a rising slope; blocknext10 isolates placement at matched dose/geography. L0.5 follows only a positive L1; A5/L2 follows only a negative L1. A null result never licenses a same-axis dose guess. |

## Session 2026-10-24 (agent-selected `AXIS=PRUNE`): ONE frontier collar rung — BUILT, fallback only

`releases/h33-h33-2-b2-PRUNEcollar3p4Gapmax-20261024-e69532d5.tif` (+ `-zeros`): 37,654 dots, 2,702 removed
(2.236–3.162 px shell) / 2,702 added, 14.35 % of R0 changed, **+0.002 MODEL (−0.008…+0.013)**, every final dot
≥ 3.606 px from the catalogue (the first repo candidate stricter than the `≥ 3 px` rule). **Do not spend slot 1–3
on it**: the slotted add ladder predicts more, and this file's new content is a *measurement*, not a dose —
at the same collar and count the lineage's FIFO refill buys 0.57 support credit per dot and max-marginal placement
buys 1.30 (2.3×, same receipt). It becomes the right slot only if a live receipt first shows the collar gradient is
still alive at 3 px, or as a format/`≥ 3 px` control. The session also measured that **every free arrangement knob
is below the 0.010 floor**: although 16.4 % of dot-level kernel credit is geometrically overlapped, every R0 dot is the argmax
somewhere (exclusive credit ≥ 0.943), so a measured greedy re-seat at 5/10/20 % nets only +0.0018/+0.0023/+0.0030
MODEL — spacing/reseat/lattice cannot reach the 0.010 floor (IR90-37).

Retained but not slotted first: **A5/L1.5** (+0.004), `RELIEFr2p12p5pct` (+0.004), `PRUNEanisoA4L2` (+0.003), `MASSshadowcont30pct` (+0.011), `MASSshadow40pct` (+0.014), `MASSrandom40pct` (+0.013). They remain valid single-axis candidates; do not spend a slot on any WITHDRAWN FIFO/gapmax/no-refill row or on infeasible SNAP.

## This session (2026-10-24, `arena/b5ea0544`, agent-selected **RELIEF**): basin<->piedmont directed pairs — BUILT, human decides slotting

Read-only `gh api` audit of 8 reachable sibling ledgers (27 RELIEF rows) found **zero** basin->piedmont or
piedmont->basin pairs under any naming; basin->range was already held by siblings (b2r12/b2r15), so it was not
rebuilt (IR90-41). Same pinned `src.relief.py` terciles/operator as the 2026-10-23 family; fixed 37,654 dots;
all additions d_cat>=3 px; zero catalogue mass; donor-tercile 5 km evenness gate passed (largest emptied
cluster 0-1 blocks); receipt `evidence/relief_s2_build_receipt.json`.

| Candidate (2026-10-24) | Shift / sym-diff | Tercile share after (B/P/R, %) | lost/gained support credit | MODEL Δ | SGMC PROXY Δ (report only) |
|---|---:|---:|---:|---:|---:|
| `…RELIEFp2b12p5pct-…-758fba08` | 4,707d piedmont->basin / 25.001% | 29.75 / 32.30 / 37.95 | 4,988.9 / 2,789.9 | **+0.003** [−0.010, +0.015] | −0.00567 [CI excludes 0] |
| `…RELIEFp2b15pct-…-66718c5c` | 5,648d piedmont->basin / 29.999% | 32.25 / 29.81 / 37.95 | 6,272.5 / 3,128.9 | **+0.004** [−0.012, +0.018] | −0.00677 [CI excludes 0] |
| `…RELIEFb2p10pct-…-aeb8f9a0` | 3,766d basin->piedmont / 20.003% | 7.25 / 54.81 / 37.95 | 5,242.7 / 3,470.9 | **−0.002** [−0.014, +0.012] | −0.00254 (least negative) |

R0 starts at 17.25% basin vs 28.23% of catalogue faults; `p2b12p5` lands at 29.75% basin, nearly matching the
catalogue prior. All three lose net H19-5 support credit (IR90-25 headwind), so signs are geomorphic-prior
MODELs, not measurements; SGMC is structurally biased against basin enrichment (9.3% of SGMC faults are T1),
treat its negative deltas as expected, not evidence. Catalogue hide/recover deltas are ~−3e-4 (CIs narrow but
the proxy is near-blind here: added dots carry zero catalogue credit by construction). Leakage canary max
symmetric AUC 0.5703 (<0.90). These are single-axis swap-ins for any RELIEF slot, not insertions ahead of the
human-controlled order above; `b2p10` is the matched direction control — a live `b2p10` >= +0.010 with null/
negative p2b arms falsifies the concealed-basin hypothesis.

## This session: 15 km structural-prior CONCENTRATION — BUILT but HELD (no slot)

| Candidate (2026-10-23) | Moved / diff | 15 km CV | MODEL Δ | SGMC PROXY Δ | Decision |
|---|---:|---:|---:|---:|---|
| `h33-h33-2-b2-CONCENTRATIONb15kmstruct10pct-20261023-8deb8269` | 3,765 / 19.998% | 0.5103 → 0.5990 | **+0.002** | **-0.006381** | HOLD; lowest-dose instrument only. |
| `h33-h33-2-b2-CONCENTRATIONb15kmstruct15pct-20261023-fdba3c0a` | 5,648 / 29.999% | → 0.6949 | **-0.002** | **-0.009540** | HOLD. |
| `h33-h33-2-b2-CONCENTRATIONb15kmstruct20pct-20261023-bc411adb` | 7,531 / 40.001% | → 0.7769 | **-0.006** | **-0.014211** | HOLD; highest risk. |

A concurrent build on the old base, merged after main recorded IR90-25/26. The prior is new and string-distinct (absolute-value rank mean of pinned bands `tmi_hg`, `geod_2ndinv`, `geod_shearrate`, `iso_grav_anom_hg`, 150 px = 15 km blocks, lowest/highest 35% tails), and R0's CV at that block size is `0.510346`, coincidentally inside the brief's quoted band. But the exact support-credit ledger is negative (10%: -4,009.4 lost / +3,036.1 gained; 20%: -10,320.1 / +4,811.5), main independently measured ~0.98 lost vs ~0.54 gained per moved dot, and sibling upward-concentration MODELs are non-positive. **HOLD all three from the next slots.** They remain occupancy/dose-response guards; revisit only after a live receipt changes the evidence state or a downward-dispersion control is justified.

Report-only diagnostics (`PROXY`, never gates/scores): catalogue hide/recover `n=13,920`, R0 `0.007191`; deltas +1e-06 / +2.4e-05 / +1.1e-05 with 95% CIs spanning 0. SGMC `n=62,122`, R0 `0.095386`; deltas above with CIs excluding 0. Leakage canary max symmetric AUC `0.574747` (<0.90). Predictions were frozen before proxies. Exact hashes, parent diffs and validator output: `evidence/concentration_build_receipt.json`.

## This session: SPACING local kernel-scale respacing — BUILT but HELD (no slot)

| Candidate (2026-10-24) | Relocated / diff | Mean displacement | Support-credit Δ | MODEL Δ | Decision |
|---|---:|---:|---:|---:|---|
| `h33-h33-2-b2-SPACINGresp5pctW15-20261024-f8bada0c` | 1,883 / 10.00% | 5.02 px | -87.1 | **0.000** (-0.008…+0.008) | HOLD; lowest-dose arrangement guard. |
| `h33-h33-2-b2-SPACINGresp10pctW15-20261024-fdb1bde9` | 3,765 / 20.00% | 3.96 px | -284.3 | **-0.001** (-0.009…+0.007) | HOLD. |
| `h33-h33-2-b2-SPACINGresp15pctW15-20261024-08f1daec` | 5,648 / 30.00% | 3.63 px | -495.7 | **-0.002** (-0.010…+0.006) | HOLD. |

Agent-selected axis after a fresh sibling audit: the brief's global SPACING trio (lattice /
Poisson-disk / along-strike) plus ring-2 micro-moves are already built in GEMSDOE86/88/91, so this
session respaced only the most kernel-crowded dots (summed disk overlap within 6 px) to the
max-marginal-credit support pixel within 15 px at the parent's 2.8 px separation, count fixed at
37,654, added d_cat>=3 px, zero catalogue mass. The exact support-credit balance is negative at
every dose (replacements within 1.5 km cannot reach the far uncovered support; IR90-25/35), both
report-only PROXYs sit at 1e-4 with opposite signs (hide-recover n=16,560: -0.000008/-0.000057/
-0.000144; SGMC n=62,122: +0.000221/+0.000413/+0.000373), and the leakage canary peaks at 0.570341
(< 0.90). **HOLD all three from the next slots**; they close the local-arrangement question so the
final choice need not spend on it. Receipt `evidence/spacing_build_receipt.json`; builder
`scripts/build_spacing_variants.py`.

## Better axes proposed this session (not built)

- **WINDOW_DOSE:** hold the dose at 10% and vary only the respacing window (15 px vs 60 px vs
  unbounded-within-block). *Mechanism:* separates "locality preserves geography" from "locality
  starves replacements" — this session's 60 px fallbacks (132-237 dots) hint the far support is
  where any arrangement gain lives. *Confounder:* a wider window becomes CONCENTRATION in
  disguise (block mix changes), so block quotas must be held as this session held geography.
  *Falsifier:* paired Δ <= -0.010 for the 60 px arm vs the 15 px arm at matched dose/count.
  Do not build until a live receipt exists (IR90-35).
- **FAR_GAP_SWAP:** crowding-ranked removals (as here) with *global* max-marginal-credit
  replacements on the 13,793 zero-credit support px, under per-5 km-block caps (no block gains
  > 50%). *Mechanism:* the only arrangement edit that can actually reach uncovered ridge; the
  fixed count keeps it an arrangement test, not a MASS add. *Confounder:* zero-credit support is
  the lineage's least-confident ground (cover, contacts, drainage), so proxy gains may not
  transfer — the same discount the q50 infill applies. *Falsifier:* paired Δ <= -0.010 vs
  `SPACINGresp10pctW15` at matched dose. Distinct from REFILL_RANK (no collar) and
  KERNEL_ORACLE_DOSE (no deletion-first step); do not build this session.

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms)

- **Weeks 1–2 (Oct 23–Nov 5):** obtain R0's receipt if possible; execute the conditional order, then only the strongest orthogonal mechanism.
- **Weeks 3–4 (Nov 6–Nov 19):** combine only axes with receipts `Δ>=+0.010`; reserve one slot for parent-vs-composite. q50-20 remains available only if the add slope rises.
- **Weeks 5–6 (Nov 20–Dec 3):** confirm the leader, select ONE blind final plus a `-zeros` fallback, and revalidate both. Account for private chunks and expert-expanded labels ([clarification](https://community.drivendata.org/t/where-do-you-draw-the-line/11536)).

## Better axes proposed (not built)

- **TIP_CONDITIONAL_COLLAR (highest priority):** keep the 3 px collar *except* in the along-strike cone beyond a
  catalogue trace's mapped endpoint (≤ 8 px beyond, ±30° of local strike), where the organiser's own definition of
  "new fault" most plausibly applies. Mechanism: new geometry of existing systems; confounder: mask-boundary
  artefacts create spurious endpoints in the fragmentary catalogue raster. Falsifier: paired Δ ≤ −0.010 vs the
  3.4 px rung; skip if endpoint extraction cannot be validated on the catalogue mask alone.
- **REFILL_POLICY_PAIR:** slot `PRUNEcollar3p0-FIFO` (sibling-built) and `PRUNEcollar3p4Gapmax` in the same week to
  convert the 2.3× refill measurement into a live paired receipt. Falsifier: |Δ| < 0.010 in both, which would say
  refill placement is irrelevant and retire the whole refill-repair line.
- **TIP_FLOOR:** protect fragments by strand length and tip-cone membership, not dot count. *Falsifier:* paired Δ<=-0.010 vs shadowcont40.
- **KERNEL_ORACLE_DOSE:** re-space survivors to a ~6 px anti-cluster instead of deleting. *Falsifier:* paired Δ<=-0.010 vs shadow48.
- **REFILL_RANK:** 5 km-stratified exact marginal-kernel refill at fixed collar/count. *Falsifier:* region-evenness failure or paired Δ<=-0.010.
- **DISPERSION_CONTROL:** down-concentration (high→low prior) at 15 km, the only sibling CONCENTRATION direction reading positive. *Falsifier:* paired Δ<=-0.010; do not build until the held upward ladder is superseded by a receipt.
- **RELIEF_DONOR_MATCH (2026-10-24 proposal):** same basin recipient at one matched 3,766-dot dose, funded once from range (`r2b10`, exists) and once from piedmont (a new `p2b10`), isolating donor quality at fixed recipient/dose with the pinned `src.relief.py` operator. *Mechanism:* piedmont is R0's largest tercile so minimum-loss drops there should cost less exclusive credit. *Confounder:* tercile composition shifts differ, so credit per drop, not geography alone, decides. *Falsifier:* paired live Δ<=-0.010 between the two donors, or any |Δ|<0.010 (no evidence).
- **WITHDRAWN / DO NOT UPLOAD:** FIFO-ranked MASS, duplicate `MASSadd10pctGapmax`, delete-only `L2nr` PRUNE, and SNAP (IR90-20/24/28/29).

**Reproduce before any upload:** `.venv/bin/python scripts/restore_data.py` → `.venv/bin/python scripts/restore_releases.py` (18 core pairs recorded at branch start) → main's `build_mass_infill.py` / `build_mass_add_variants.py` / `build_mass_continuity.py` / `build_aniso_prune_along.py` family builders or verifiers for the slotted candidates → `.venv/bin/python scripts/build_concentration_variants.py --verify` for the held files. For the held SPACING files: `.venv/bin/python scripts/build_spacing_variants.py --verify`. Re-read every TIFF from disk, run the format gate, and match SHA-256 to `ledger/submissions.csv` before the human uploads from their own account.

## Concurrent 5 km strain-prior CONCENTRATION — HELD, not slotted (session `arena/388fea70`)

A second concurrent CONCENTRATION session built three fixed-count 37,654-dot files on a label-agnostic
geodetic strain-rate prior (band 4 `geod_2ndinv`, 5 km blocks, complementary 50% pools, added d_cat≥3 px,
zero catalogue mass). It used the SAME canonical filenames as the 15 km ladder above, so its files were renamed
`*_strain5km` to coexist (IR90-32). Values and hashes are distinct from the 15 km ladder and from sibling
0.8/1/5 km values; kept as string-distinct BUILT occupancy guards under the strict dedup rule.

| Candidate (all HELD) | move | CV 15 km | corr(density,strain) | Δ (MODEL) |
|---|---|---|---|---|
| `CONCstrain10` | 10% low→high strain (20.0% diff) | 0.510→0.568 | 0.110→0.256 | +0.004 (−0.010…+0.015) |
| `CONCstrain15` | 15% low→high strain (30.0% diff) | 0.510→0.622 | 0.110→0.313 | +0.001 (−0.013…+0.013) |
| `CONCstrainAway10` | 10% high→low strain (SIGN CONTROL, 20.0% diff) | 0.510→0.558 | 0.110→−0.037 | −0.004 (−0.016…+0.008) |

**Decision: HOLD from the next slots, consistent with IR90-25/26/30.** A fixed-count move loses ~0.98 and gains
~0.54 support credit per dot (this session: net −370/−1629/−409 lost−gained), and the SGMC PROXY favours the
AWAY arm (−0.0022 vs −0.0060/−0.0087). The one genuinely novel item is the matched-dose **sign control**: if the
human ever spends slots here, pair `strain10` vs `strainAway10` (similar CV, opposite strain alignment) to test
strain DIRECTION — a live paired receipt, not any proxy, decides. Until entity-scope/quota is adjudicated
(IR90-26/30/32), the next three slots remain the integrated MASS-add / conditional continuity / fixed-count
PRUNE order above. Predictions are MODEL; proxies REPORT ONLY. Receipt
`evidence/concentration_strain5km_build_receipt.json`; builder `scripts/build_concentration_strain5km.py`.
