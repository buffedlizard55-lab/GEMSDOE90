# SLOT PLAN — fixed-count A5 along-strike PRUNE (2026-10-23)

**R0:** `h33-h33-2-b2`, 37,654 dots; 0.2778 is **CLAIM**, not a receipt. Human must supply dated `TOP_PUBLIC`, rolling-week/total quota use, and confirm the 2026-12-03 deadline. ONE entity, 3 scored slots/rolling week, ONE blind final ([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Any public-chunk `|Δ|<0.010` is **no evidence**; private chunks can differ.

## Next 3 slots (upload NaN primary only; human decides)

| Order | File / predicted Δ (`MODEL`, not a score) | What its receipt changes |
|---|---|---|
| **1** | `h33-h33-2-b2-PRUNEanisoA5L1-20261023-cd2c60ce.tif` — **+0.005** | `Δ>=+0.010`: narrower along-strike preservation pays; Slot 3 = **L0.5**. `Δ<=-0.010`: reject that direction; Slot 3 = recorded **A5/L2** (`15218061`) to test the opposite direction. Otherwise no evidence; Slot 3 = RELIEF below. |
| **2** | `h33-h33-2-b2-MASSshadow20pct-20261023-c4ce118b.tif` — **+0.009** | Orthogonal count test. `Δ>=+0.010`: carry 20% shadow thinning into week-3/4 composites; `Δ<=-0.010`: stop shadow thinning and hold count; otherwise do not infer a mass effect. Restore/verify with `scripts/build_mass_shadow.py`. |
| **3** | Conditional: `…PRUNEanisoA5L0p5-…-91ff3771.tif` (**+0.003**), `…PRUNEanisoA5L2-…-15218061.tif` (**+0.002**), or `…RELIEFr2p12p5pct-…-5e64d01f.tif` (**+0.004**) | L0.5 tests a further continuation-preservation gain only after Slot 1 clears +0.010. A5/L2 tests whether narrower L was harmful after Slot 1 clears −0.010. If Slot 1 is inconclusive, use RELIEF as an orthogonal mechanism; do not spend a third slot guessing along the same ladder. |

## Weeks to deadline

- **Weeks 1–2 (Oct 23–Nov 5):** obtain R0 receipt if possible; run the ordered slots, then only the strongest remaining orthogonal candidate. No exact-hash or `(AXIS,value)` repeats.
- **Weeks 3–4 (Nov 6–Nov 19):** combine only the two axes with receipts `Δ>=+0.010`; hold one slot for the direct parent-vs-composite comparison.
- **Weeks 5–6 (Nov 20–Dec 3):** confirm the leader, choose ONE blind final and a `-zeros` fallback, and revalidate both from disk. Phase-2 expert-expanded labels favour geologically reviewable traces over public-chunk overfit.

**Diagnostics (REPORT ONLY):** canary max symmetric AUC 0.5695; catalogue hide/recover n=13,920 and SGMC n=62,122, with 95% CIs in `evidence/aniso_along_refill_receipt.json`. Their negative deltas do not gate candidates and are not live scores.

**Future axis, not built — `REFILL_RANK`:** replace geographic FIFO refill with 5 km-block-stratified exact marginal-kernel coverage at fixed collar/count. *Mechanism:* reduce the observed ~98% redundant refill without a regional hole. *Confounder:* H19-5 contacts/drainages and block quotas are not fault truth. *Falsifier:* paired live `Δ<=-0.010`, or a region-evenness failure before upload. SNAP is not proposed: IR90-21 proves its three hard constraints incompatible for 30 R0 dots.
