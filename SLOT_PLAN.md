# SLOT PLAN — integrated MASS-add / continuity / PRUNE; 15 km CONCENTRATION held (2026-10-23)

**R0:** `h33-h33-2-b2` / `GEMSDOE32`, 37,654 dots; 0.2778 is **CLAIM**, not a receipt. Human supplies dated `TOP_PUBLIC`, quota use, and confirms 2026-12-03. ONE entity, 3 scored slots/rolling week, ONE blind final ([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Live `|Δ|<0.010` is **no evidence**; private chunks can differ. Never repeat an exact hash or a `(parent, axis, value)` pair.

## Next 3 slots (NaN primary only; human decides)

| Order | Candidate(s), predicted Δ (`MODEL`) | Decision from receipt |
|---|---|---|
| **1** | `…MASSadd5pctq50-20261023-c4e6144c.tif` — **+0.008** | `Δ>=+0.010`: add sign pays; Slot 2 = q50-10. `Δ<=-0.010`: close adds for now; Slot 2 = continuity-aware drop **shadowcont20**. `|Δ|<0.010`: no evidence; Slot 2 = orthogonal fixed-count **A5/L1**. |
| **2** | Add branch: `…MASSadd10pctq50-20261023-5edc84de.tif` — **+0.014**. Negative-add branch: `…MASSshadowcont20pct-20261023-66d961ba.tif` — **+0.009**. Null-add branch: `…PRUNEanisoA5L1-20261023-cd2c60ce.tif` — **+0.005** | Add: rising `Δ` licenses q50-20; flat but positive favors matched-placement blocknext10; negative closes the ladder. Continuity: `Δ>=+0.010` → shadowcont40; `Δ<=-0.010` → shadow20 to separate dose from protection. PRUNE: `Δ>=+0.010` → L0.5; `Δ<=-0.010` → recorded A5/L2; null → shadowcont20. |
| **3** | Add: `…MASSadd20pctq50-20261023-f94efff4.tif` — **+0.022**, or matched-dose `…MASSadd10pctBlocknext-20261023-89d16c16.tif` — **+0.0044**. Continuity: `…MASSshadowcont40pct-20261023-92be4121.tif` — **+0.013** / `…MASSshadow20pct-20261023-c4ce118b.tif` — **+0.009**. PRUNE: `…PRUNEanisoA5L0p5-20261023-91ff3771.tif` — **+0.003** / recorded **A5/L2** / shadowcont20 | Take exactly one conditional arm. q50-20 requires two positive add receipts and a rising slope; blocknext10 isolates placement at matched dose/geography. L0.5 follows only a positive L1; A5/L2 follows only a negative L1. A null result never licenses a same-axis dose guess. |

Retained but not slotted first: **A5/L1.5** (+0.004), `RELIEFr2p12p5pct` (+0.004), `PRUNEanisoA4L2` (+0.003), `MASSshadowcont30pct` (+0.011), `MASSshadow40pct` (+0.014), `MASSrandom40pct` (+0.013). They remain valid single-axis candidates; do not spend a slot on any WITHDRAWN FIFO/gapmax/no-refill row or on infeasible SNAP.

## This session: 15 km structural-prior CONCENTRATION — BUILT but HELD (no slot)

| Candidate (2026-10-23) | Moved / diff | 15 km CV | MODEL Δ | SGMC PROXY Δ | Decision |
|---|---:|---:|---:|---:|---|
| `h33-h33-2-b2-CONCENTRATIONb15kmstruct10pct-20261023-8deb8269` | 3,765 / 19.998% | 0.5103 → 0.5990 | **+0.002** | **-0.006381** | HOLD; lowest-dose instrument only. |
| `h33-h33-2-b2-CONCENTRATIONb15kmstruct15pct-20261023-fdba3c0a` | 5,648 / 29.999% | → 0.6949 | **-0.002** | **-0.009540** | HOLD. |
| `h33-h33-2-b2-CONCENTRATIONb15kmstruct20pct-20261023-bc411adb` | 7,531 / 40.001% | → 0.7769 | **-0.006** | **-0.014211** | HOLD; highest risk. |

A concurrent build on the old base, merged after main recorded IR90-25/26. The prior is new and string-distinct (absolute-value rank mean of pinned bands `tmi_hg`, `geod_2ndinv`, `geod_shearrate`, `iso_grav_anom_hg`, 150 px = 15 km blocks, lowest/highest 35% tails), and R0's CV at that block size is `0.510346`, coincidentally inside the brief's quoted band. But the exact support-credit ledger is negative (10%: -4,009.4 lost / +3,036.1 gained; 20%: -10,320.1 / +4,811.5), main independently measured ~0.98 lost vs ~0.54 gained per moved dot, and sibling upward-concentration MODELs are non-positive. **HOLD all three from the next slots.** They remain occupancy/dose-response guards; revisit only after a live receipt changes the evidence state or a downward-dispersion control is justified.

Report-only diagnostics (`PROXY`, never gates/scores): catalogue hide/recover `n=13,920`, R0 `0.007191`; deltas +1e-06 / +2.4e-05 / +1.1e-05 with 95% CIs spanning 0. SGMC `n=62,122`, R0 `0.095386`; deltas above with CIs excluding 0. Leakage canary max symmetric AUC `0.574747` (<0.90). Predictions were frozen before proxies. Exact hashes, parent diffs and validator output: `evidence/concentration_build_receipt.json`.

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms)

- **Weeks 1–2 (Oct 23–Nov 5):** obtain R0's receipt if possible; execute the conditional order, then only the strongest orthogonal mechanism.
- **Weeks 3–4 (Nov 6–Nov 19):** combine only axes with receipts `Δ>=+0.010`; reserve one slot for parent-vs-composite. q50-20 remains available only if the add slope rises.
- **Weeks 5–6 (Nov 20–Dec 3):** confirm the leader, select ONE blind final plus a `-zeros` fallback, and revalidate both. Account for private chunks and expert-expanded labels ([clarification](https://community.drivendata.org/t/where-do-you-draw-the-line/11536)).

## Better axes proposed (not built)

- **TIP_FLOOR:** protect fragments by strand length and tip-cone membership, not dot count. *Falsifier:* paired Δ<=-0.010 vs shadowcont40.
- **KERNEL_ORACLE_DOSE:** re-space survivors to a ~6 px anti-cluster instead of deleting. *Falsifier:* paired Δ<=-0.010 vs shadow48.
- **REFILL_RANK:** 5 km-stratified exact marginal-kernel refill at fixed collar/count. *Falsifier:* region-evenness failure or paired Δ<=-0.010.
- **DISPERSION_CONTROL:** down-concentration (high→low prior) at 15 km, the only sibling CONCENTRATION direction reading positive. *Falsifier:* paired Δ<=-0.010; do not build until the held upward ladder is superseded by a receipt.
- **WITHDRAWN / DO NOT UPLOAD:** FIFO-ranked MASS, duplicate `MASSadd10pctGapmax`, delete-only `L2nr` PRUNE, and SNAP (IR90-20/24/28/29).

**Reproduce before any upload:** `.venv/bin/python scripts/restore_data.py` → `.venv/bin/python scripts/restore_releases.py` (18 core pairs recorded at branch start) → main's `build_mass_infill.py` / `build_mass_add_variants.py` / `build_mass_continuity.py` / `build_aniso_prune_along.py` family builders or verifiers for the slotted candidates → `.venv/bin/python scripts/build_concentration_variants.py --verify` for the held files. Re-read every TIFF from disk, run the format gate, and match SHA-256 to `ledger/submissions.csv` before the human uploads from their own account.

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
