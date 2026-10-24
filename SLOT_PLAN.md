# Slot Plan — GEMSDOE90 (`<= 1 page`)

**Parent R0:** `h33-h33-2-b2` (`GEMSDOE32`; **37,654** unit-mass dots; claimed `0.2778` DTI = `CLAIM`, not a `RECEIPT`). Exact rebuild verified (`c55bafc4…` zeros / `baeae321…` NaN). **Rule:** upload primary NaN `.tif` first (`-zeros.tif` only if scorer rejects NaNs); treat live `|Δ| < 0.010` vs R0 as **no evidence**; agent never submits.

## Next 3 Slots (Conditional Decision Tree; 39 `BUILT` in-repo, 0 `RECEIPT`s)

1. **Slot 1 — `releases/h33-h33-2-b2-MASSadd5pctq50-20261023-4ef8cf75.tif`** (`MASS`, `+5%` = `+1,883` -> `39,537` dots, `5.00%` diff; `MODEL` **+0.007 DTI**, bracket `-0.004..+0.025`). Sha256 `4ef8cf75…` (`-zeros` `217c42d3…`). Tests whether `H19-5` mid-strand kernel gaps are under-covered on live truth before any destructive edit.
2. **Slot 2 (branched on Slot 1 live receipt vs R0):**
   - **Add branch (`Δ >= +0.010`):** **`releases/h33-h33-2-b2-MASSadd10pctq50-20261023-29a6f1cc.tif`** (`41,419` dots, `10.00%` diff; `MODEL` **+0.013 DTI**; sha256 `29a6f1cc…`).
   - **Drop branch (`Δ <= -0.010`):** **`releases/h33-h33-2-b2-MASSshadowcont20pct-20261023-66d961ba.tif`** (`30,123` dots, `20.00%` diff; `MODEL` **+0.009 DTI**; sha256 `66d961ba…`; 857/857 `>=1 km` strands preserved at 6 px).
   - **Null-add branch (`|Δ| < 0.010`):** **`releases/h33-h33-2-b2-PRUNEanisoA5L1q50-20261024-c41fc4aa.tif`** (`PRUNE`, `A=5, L=1.0 px`, `37,654` dots held, `12.67%` diff; `MODEL` **+0.008 DTI**, `-0.005..+0.017`; sha256 `c41fc4aa…`, `-zeros` `4d91c5de…`). Replaces northern-strip FIFO-refilled `PRUNEanisoA5L1` (`IR90-41`).
3. **Slot 3 (branched on Slot 2 receipt):**
   - **Add continues (`Slot 2 >= Slot 1 + 0.010`):** `MASSadd20pctq50` (`278df996…`) or placement control `MASSadd10pctBlocknext` (`16b3df25…`).
   - **Drop continues (`Slot 2 >= R0 + 0.010` on shadowcont20):** `MASSshadowcont30pct` (`885f6fee…`; `26,358` dots; `MODEL` **+0.011 DTI**), else un-protected `MASSshadow20pct` (`0c70426a…`).
   - **PRUNE follow-up:** if `A5/L1q50 >= R0 + 0.010`, test tip-preserving **`releases/h33-h33-2-b2-PRUNEanisoA5L0p5q50-20261024-b7f9d99f.tif`** (`7.08%` diff; `MODEL` **+0.005 DTI**; sha256 `b7f9d99f…`); if `|Δ| < 0.010`, test wider along-strike **`releases/h33-h33-2-b2-PRUNEanisoA5L2q50-20261024-d54c00e6.tif`** (`19.46%` diff; `MODEL` **+0.006 DTI**; sha256 `d54c00e6…`), isotropic 3px-clean fallback `PRUNEcollar3p4Gapmax` (`e69532d5…`; `MODEL` **+0.002 DTI**), or `RELIEFr2p12p5pct` (`3288894c…`).

## Session `2026-10-24` (`arena/73f4c306`): `AXIS=PRUNE` `q50` Marginal-Kernel Refill Cards (`IR90-41` Fix)

All 9 prior FIFO-refilled `BUILT` `PRUNE` files (`PRUNE3p5px..5p5px`, `PRUNEanisoA4L2..A6L2`, `PRUNEanisoA5L1p5..L0p5`) used global `fifo_bfs_visit_rank(h19)`, dumping **100% of their 1,333–6,130 refills into `y <= 101..264`** (`87%–97%` of dense 5 km blocks starved, `addition_evenness_gate=False`, `97.9%–99.5%` within `3 px` of retained dots, and `min d_cat = 2.236 px`; `IR90-41`). All 9 are **HELD from slots**. The 3 new `20261024` `q50` files hold `37,654` dots, enforce `d_cat >= 3.0 px` on every added dot, pass `addition_evenness_gate=True` (`0/848` dense blocks starved across `y in [0, 3699]`), cut median replacement distance from `845–917 px` to `10.3–17.3 px`, and raise off-catalogue `H19-5` refill credit `2.12x–2.30x` (`evidence/aniso_q50_refill_receipt.json`):

| ID (`20261024`) | `(A, L)` / Turnover | Hypothesis & Mechanism (`S = 37,654`, `d_cat >= 3 px` on adds) | Non-Fault Mimic / Confounder | `MODEL` (not a score) & Falsifier |
| :--- | :--- | :--- | :--- | :--- |
| `…PRUNEanisoA5L0p5q50-20261024-b7f9d99f` | `5.0, 0.5 px` `1,333` (`7.08%`) | Strips `<=500 m` cross-strike scarp haloes while keeping tips `>50 m`; 5 km `q50` refill (`1,124/1,788` blocks) lifts refill `dT` `+655.7 -> +1,504.8` and flips outside-collar `H19-5` `ΔT` from `-237.5` to **`+432.8`**. | Parallel DEM slope steps / fan-head trenches `<500 m` of faults; volcanic/lithologic edges on outside-collar `H19-5`. | **`+0.005 DTI`** (`-0.007..+0.014`). Falsified if live `Δ <= -0.010` vs R0. |
| `…PRUNEanisoA5L1q50-20261024-c41fc4aa` | `5.0, 1.0 px` `2,386` (`12.67%`) | Balances `500 m` flank cleanup against `>100 m` tip retention; 5 km `q50` refill (`1,347/1,788` blocks, med dist `12.0 px`) lifts refill `dT` `+1,168.2 -> +2,646.9` (`2.27x`) and outside-collar `ΔT` `+222.9 -> +1,249.2`. | Same flank/contact mimics; if tip errors exceed `100 m`, `L=1` leaves some catalogue-tip haloes unpruned vs `L=2`. | **`+0.008 DTI`** (`-0.005..+0.017`). Falsified if live `Δ <= -0.010` vs R0. |
| `…PRUNEanisoA5L2q50-20261024-d54c00e6` | `5.0, 2.0 px` `3,663` (`19.46%`) | Holds R0's `200 m` along-strike collar with `500 m` cross-strike cleanup; 5 km `q50` refill (`1,476/1,788` blocks, med dist `10.3 px`) lifts refill `dT` `+1,730.3 -> +3,673.0` (`2.12x`) and outside-collar `ΔT` `+1,111.9 -> +2,441.1`. | En-echelon step-overs and real fault tips at `100–200 m` along strike are pruned under `L=2.0 px`. | **`+0.006 DTI`** (`-0.008..+0.016`). Falsified if live `Δ <= -0.010` vs R0. |

## Held / Withdrawn Summary, Calendar (`2026-12-03` UNVERIFIED), & Better Axes Proposed (Not Built)

- **HELD from slots:** all 9 FIFO-refilled `PRUNE` files (`IR90-41`), `CONCENTRATIONb15kmstruct10/15/20pct` (`IR90-30`), `CONCstrain10/15/Away10` (`IR90-32`/`IR90-34`), and `SPACINGresp5/10/15pctW15` (`IR90-35`). Fallback-only: isotropic `PRUNEcollar3p4Gapmax` (`IR90-39`).
- **WITHDRAWN (do not upload):** `MASSdrop5pct-tail`, `MASSadd5pct-next`, `MASSadd20pct-next` (`IR90-20`), `MASSadd10pctGapmax` (`IR90-24`), `PRUNEanisoA4/5/6L2nr` (`IR90-29`), and `SNAP` (`IR90-28`).
- **Calendar:** Weeks 1–2 (Oct 23–Nov 5): execute Slots 1–3 above and obtain receipts; Weeks 3–4 (Nov 6–Nov 19): combine only axes with live `Δ >= +0.010`; Weeks 5–6 (Nov 20–Dec 3): confirm leader and pick ONE blind final + `-zeros` fallback.
- **Better axes proposed (not built):**
  1. **`LOCAL_CORRIDOR_REFILL`:** Refill pruned collar dots within the same `<=1.5 km` fault-corridor neighborhood (`3.0 < d_cat <= 15.0 px`) by marginal kernel credit rather than 5 km footprint-wide quotas. *Falsifier:* paired live `|Δ| < 0.010` vs `PRUNEanisoA5L1q50` or local pool saturation.
  2. **`TIP_CONDITIONAL_COLLAR`:** Keep the `>=3 px` collar everywhere except in the `<=8 px`, `±30 deg` along-strike cone beyond mapped trace endpoints. *Falsifier:* paired live `Δ <= -0.010` vs `PRUNEanisoA5L0p5q50` or `PRUNEcollar3p4Gapmax`.
  3. **`CURVATURE_GATED_CONTINUITY`:** Weight `6 px` strand-articulation protection by local strike-angle bend (`<= 25 deg`) so sharp drainage/road kinks are not protected as fault strands. *Falsifier:* paired live `Δ <= -0.010` vs `MASSshadowcont20pct`.
