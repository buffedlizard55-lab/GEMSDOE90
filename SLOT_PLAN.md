# SLOT PLAN — integrated MASS-add / fixed-count PRUNE (2026-10-23)

**R0:** `h33-h33-2-b2`, 37,654 dots; 0.2778 is **CLAIM**, not a receipt. Human supplies dated `TOP_PUBLIC`, quota use, and confirms 2026-12-03. ONE entity, 3 scored slots/rolling week, ONE blind final ([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Live `|Δ|<0.010` is **no evidence**; private chunks can differ.

## Next 3 slots (NaN primary only; human decides)

| Order | Candidate(s), predicted Δ (`MODEL`) | Decision from receipt |
|---|---|---|
| **1** | `h33-h33-2-b2-MASSadd5pctq50-20261023-c4e6144c.tif` — **+0.008** | `Δ>=+0.010`: add sign pays; Slot 2 = q50-10. Otherwise close the add ladder for now; Slot 2 = orthogonal **A5/L1**. |
| **2** | If add pays: `…MASSadd10pctq50-20261023-5edc84de.tif` — **+0.014**. Otherwise: `…PRUNEanisoA5L1-20261023-cd2c60ce.tif` — **+0.005** | Two positive add receipts settle sign; Slot 3 = matched placement control **blocknext10**. A negative/flat q50-10 means dose is exhausted; do not take q50-20. If A5/L1 is used: `Δ>=+0.010` → Slot 3 **L0.5**; `Δ<=-0.010` → recorded **A5/L2**; null → `MASSshadow20pct`. |
| **3** | Add path: `…MASSadd10pctBlocknext-20261023-89d16c16.tif` — **+0.0044**. PRUNE path: `…PRUNEanisoA5L0p5-…-91ff3771.tif` / `…PRUNEanisoA5L2-…-15218061.tif` / `…MASSshadow20pct-…-c4ce118b.tif` | blocknext10 vs q50-10 isolates placement at matched dose/geography. L0.5 tests further continuation preservation only after a positive L1; A5/L2 tests the opposite direction after a negative L1. A null result never licenses a same-axis dose guess. |

## Weeks to deadline

- **Weeks 1–2 (Oct 23–Nov 5):** obtain R0's receipt if possible; execute the conditional order, then only the strongest orthogonal mechanism. No exact-hash or `(AXIS,value)` repeats.
- **Weeks 3–4 (Nov 6–Nov 19):** combine only axes with receipts `Δ>=+0.010`; reserve one slot for parent-vs-composite. q50-20 remains available only if the add slope rises.
- **Weeks 5–6 (Nov 20–Dec 3):** confirm the leader, select ONE blind final plus a `-zeros` fallback, and revalidate both. Account for private chunks and expert-expanded labels ([clarification](https://community.drivendata.org/t/where-do-you-draw-the-line/11536)).

**PRUNE receipt:** `evidence/aniso_along_refill_receipt.json`; all three candidates hold 37,654 dots and `d_cat>2 px`. Canary max AUC 0.5695; catalogue n=13,920 and SGMC n=62,122 are **PROXY / REPORT ONLY**, with 95% CIs, never gates or scores. Predictions were frozen first.

**Future axis, not built — `REFILL_RANK`:** use 5 km-block-stratified exact marginal-kernel refill at fixed collar/count. *Mechanism:* reduce ~98% redundant refill without regional holes. *Confounder:* H19-5 contacts/drainages and quotas are not truth. *Falsifier:* paired live `Δ<=-0.010` or region-evenness failure. `COLLAR_NOREFILL` is withdrawn (IR90-27); cross-strike SNAP is infeasible for 30 dots (IR90-26).
