# SLOT PLAN — Weekly allocation & `AXIS=CONCENTRATION` (session 2026-10-23e, GEMSDOE90)

**Incumbent R0:** `h33-h33-2-b2` (37,654 unit-mass dots, rebuilt byte-identically this session: zeros `c55bafc4…` / NaN `baeae321…`, 26/26 pins SHA-256 verified). `0.2778` is **CLAIM** until a portal receipt is logged. `TOP_PUBLIC` (with date) and weekly/total quota used are **blank — the human supplies them before any upload**. Quota is ONE entity at 3 scored submissions/rolling week + ONE blind final (rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf; metric/spec: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). Any public-chunk live `|Δ| < 0.010` DTI is **no evidence**. Deadline `2026-12-03` UNVERIFIED — human confirms.

> **ENTITY-SCOPE ALERT (IR90-21).** Read-only audit 2026-10-23 of sibling repos `buffedlizard55-lab/GEMSDOE84–97` shows the SAME seven axes built the same day (catalogue-density CONC in GEMSDOE89, H19-5 CONC in GEMSDOE87, self-density CONC in GEMSDOE88/91; PRUNE/SNAP/SPACING/RELIEF likewise), all essentially receipt-free. If those repos are ONE DrivenData entity, the 3-scored-slots/week quota is already exceeded and slot allocation — not more builds — is the bottleneck. **The human must adjudicate entity scope before spending any slot.** This session therefore made its CONCENTRATION prior a LABEL-AGNOSTIC geodetic strain-rate invariant (band 4 `geod_2ndinv`), near-orthogonal to R0 density (rank r=+0.11) and relief-neutral (r=−0.046), so the value is genuinely new and orthogonal to every sibling value and to the RELIEF/PRUNE/MASS axes (IR90-21…23; receipt `evidence/concentration_build_receipt.json`).

## This session built (3 fixed-count 37,654-dot candidates; 5 km blocks; complementary top/bottom-50% strain pools; greedy R=3 px marginal-credit drop/add; added d_cat≥3 px)

| id | move | CV 15 km | corr(density,strain) | predicted Δ (`MODEL`) | region shift (reported) |
|---|---|---|---|---|---|
| `h33-h33-2-b2-CONCstrain10-20261023-aa60138c` | 10% low→high strain (3,765d; 20.0% diff) | 0.510→0.568 | 0.110→0.256 | **+0.004** (−0.010…+0.015) | max 0.049 pp |
| `h33-h33-2-b2-CONCstrain15-20261023-d3db2957` | 15% low→high strain (5,648d; 30.0% diff) | 0.510→0.622 | 0.110→0.313 | **+0.001** (−0.013…+0.013) | max 0.072 pp |
| `h33-h33-2-b2-CONCstrainAway10-20261023-bd514054` | 10% high→low strain (3,765d; 20.0% diff, SIGN CONTROL) | 0.510→0.558 | 0.110→−0.037 | **−0.004** (−0.016…+0.008) | max 0.051 pp |

`strainAway10` is a matched-dose sign control at similar CV (0.558 vs 0.568) but opposite strain alignment — it isolates strain *direction* from raw concentration. Mechanism: new faults nucleate/slip where the crust actively deforms. Non-fault confounder: GPS/InSAR station-spacing artefacts, groundwater/geothermal/volcanic transients, ductile shear. Headwind (IR90-23): all three LOSE net H19-5-support credit, and the SGMC bedrock control favours the AWAY arm, so predictions stay in the no-evidence band.

## Next 3 slots in order (one entity; upload NaN `.tif` primary only, never both twins)

| Slot | Candidate | Predicted Δ (`MODEL`) | Decision rule from the live receipt |
|---|---|---|---|
| 1 | `…CONCstrain10-…-aa60138c.tif` (10% toward high strain) | **+0.004** (−0.010…+0.015) | `Δ ≥ +0.010`: strain prior looks real → Slot 2 confirms with the sign control. `Δ ≤ −0.010`: reject toward-strain; pivot Slot 2 to `RELIEFr2p12p5pct`. `|Δ|<0.010`: still run Slot 2 (direction may matter even if 10% is too small). |
| 2 | `…CONCstrainAway10-…-bd514054.tif` (10% away, matched-dose sign control) | **−0.004** (−0.016…+0.008) | If `away10 ≥ strain10` on paired receipts, the strain prior is **falsified** (concentration level, not strain, drove any Slot-1 change). If `away10 ≤ strain10 − 0.010`, the strain direction is confirmed. |
| 3 | Conditional: `…CONCstrain15-…-d3db2957.tif` (dose top) **OR** `…RELIEFr2p12p5pct-…-5e64d01f.tif` (orthogonal) | **+0.001** / **+0.004** | Upload `strain15` only if Slot 1 `Δ ≥ +0.010` (measures dose slope; CV 0.622 above the reported best band). If strain is null/negative, upload `RELIEFr2p12p5pct` to test the physiographic axis instead. |

Previously recorded alternative orders (unchanged): MASS `MASSshadow20pct` → `MASSshadow40pct` → `MASSrandom40pct`; RELIEF `RELIEFr2p12p5pct` → orthogonal axis → conditional rung. **Never slot any FIFO-ranked dose rung** (IR90-20).

## Weeks to the deadline (`2026-12-03` UNVERIFIED — human confirms)

- **Weeks 1–2 (Oct 23 – Nov 5, ≤6 slots):** Confirm R0 live receipt if missing; run Slots 1–3 above. The bottleneck is live receipts, not more builds (~30+ built-but-unscored variants already exist across this repo and siblings). Do not repeat any `(AXIS, value)`.
- **Weeks 3–4 (Nov 6 – Nov 19, ≤6 slots):** Combine the two axes whose paired receipts cleared `Δ ≥ +0.010` (e.g. winning strain dose × winning RELIEF tercile or MASS thinning) on exact parent code.
- **Weeks 5–6 (Nov 20 – Dec 3, ≤6 slots + 1 blind final):** Confirm top composite; select ONE blind final `.tif` (accounting for private chunks + Phase 2 expert-expanded faults: https://community.drivendata.org/t/where-do-you-draw-the-line/11536) and its `-zeros.tif` fallback; re-run `scripts/restore_data.py`, `scripts/restore_releases.py`, and the `--verify` + `src/validate.py` format gate on both before upload.

## Report-only diagnostics (`PROXY` — never gates, never scores)

- **Leakage canary** (this session, 19 bands + strain prior, seed 20261023): max symmetric AUC = **0.5700** (`geod_2ndinv`), `auc_gt_0_90 = False`. Prior is a supplied geophysical band, no catalogue-derived feature.
- **Catalogue hide-and-recover** (`n_withheld = 13,920`, R0 0.0072): strain10 `−0.0003`, strain15 `−0.0004`, away10 `−0.0004`. Added dots at d_cat≥3 px earn ZERO credit on withheld catalogue → proxy measures only residual flank retention; historical live correlation −0.87…+0.54.
- **Off-catalogue SGMC control**: away10 `−0.0022` > strain10 `−0.0060` > strain15 `−0.0087` (SGMC sits in lower-strain exposed bedrock). Report only.

## Better axes proposed (mechanism / confounder / falsifier — NOT built)

- **STRAIN×RELIEF COMPOSITE.** Concentrate on the intersection of high strain AND basin/piedmont (both independently hint down-relief). *Confounder:* strain and relief are correlated at basin scale, so this partly double-counts. *Falsifier:* paired Δ ≤ −0.010 vs `strain10` or `RELIEFr2p12p5pct`.
- **CONTINUITY_AWARE_DOSE** / **KERNEL_ORACLE_DOSE** / **REDUNDANCY_BUDGET** (from prior sessions): preserve ≥1 km strands while thinning, or re-space survivors just outside the 3 px kernel, or drop dots whose kernel is ≥90% covered. *Falsifier:* paired Δ ≤ −0.010 vs `shadow40`/`shadow48`.
- **CROSS_STRIKE_RIDGE_SNAP** (≤2 px, high-pass `tc` + `det_elev_slope`, strictly orthogonal to local strike). *Confounder:* dipping lithologic contacts offset magnetic gradients downdip. *Falsifier:* paired Δ ≤ −0.010 vs R0. (Raw `tmi_hg`/`iso_grav_anom_slope` window-max is too smooth — IR90-19 — so high-pass only.)
- **TRACKB (Phase 2).** Strike-consistent traces ≥1 km from R0's top-ranked dots, as GeoJSON + raster with one evidence paragraph per trace for the expert label-expansion round. Not a weekly-slot candidate unless the human decides.

## Confounds stated, not hidden

- **Both the strain ladder and every sibling concentration share one parent and one 2026-10-23 build.** Only paired receipts compare; a positive Slot-1 receipt does not validate the control, and vice versa.
- **Regional mass shift is the axis, reported not tuned** (IR90-22); the prior is label-agnostic, so this is not label probing. Only region-*isolation* (emptied hole/strip) is gated; all three pass (largest 5 km emptied cluster 0–1 blocks, ≥90%-emptied fraction 0.0).
- **No prediction here is a score.** R0's 0.2778 is CLAIM, all Δ are MODEL, the canary/proxies are PROXY.
