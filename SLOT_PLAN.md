# SLOT PLAN — receipts first; concurrent 2026-10-24 families HELD (updated 2026-10-24)

**R0:** `h33-h33-2-b2`, 37,654 dots; 0.2778 is **CLAIM**, not a receipt. Human supplies dated `TOP_PUBLIC`, weekly quota, 2026-12-03 confirmation, and adjudicates sibling-repo entity scope before any slot ([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Never repeat a hash or `(parent,axis,value)`. Live `|Δ|<0.010` = **no evidence**.

## Next 3 slots (NaN primary; one file/slot)

1. **`…MASSadd5pctq50-20261023-c4e6144c.tif`**, pred **+0.008**. `Δ≥+0.010` → add pays; `Δ≤−0.010` → close adds; null → no evidence.
2. Positive: **`…MASSadd10pctq50-20261023-5edc84de.tif`** (+0.014). Negative: **`…MASSshadowcont20pct-20261023-66d961ba.tif`** (+0.009). Null: **`…PRUNEanisoA5L1-20261023-cd2c60ce.tif`** (+0.005).
3. One conditional arm: add20 q50 **`…f94efff4.tif`** (+0.022) after two rising add receipts; placement control **`…MASSadd10pctBlocknext-20261023-89d16c16.tif`** (+0.004) after a flat add; continuity **`…MASSshadowcont40pct-20261023-92be4121.tif`** (+0.013) after a positive continuity receipt; or **`…PRUNEanisoA5L0p5-20261023-91ff3771.tif`** (+0.003) after positive A5/L1. Null never licenses a same-axis dose guess.

## Built but HELD / human-adjudicated — do not spend slots 1–3 here

| Family | Files / doses | Exact reading | Decision |
|---|---|---|---|
| PRUNE frontier collar | `PRUNEcollar3p4Gapmax-…-e69532d5` | +0.002 MODEL (−0.008…+0.013); FIFO 0.57 vs max-marginal 1.30 credit/refill dot; hide/recover PROXY structurally blind (IR90-37/38/39/40). | Fallback only; the refill measurement, not a new dose. |
| CONCENTRATION 15 km / 5 km strain | `b15kmstruct10/15/20`, `CONCstrain10/15/Away10` | Upward moves lose support credit and SGMC PROXY; R0 CV already exceeds brief band (IR90-25/26/30/32/34). | HOLD; `Away10` is a direction falsifier only. |
| SPACING local respacing | `resp5/10/15pctW15` (`f8bada0c`, `fdb1bde9`, `08f1daec`) | 0.000 / −0.001 / −0.002 MODEL; support credit −87/−284/−496; 15 px window cannot reach far gaps (IR90-35/36). | HOLD; receipt `evidence/spacing_build_receipt.json`. |
| SPACING kernel-gap equalization (this branch) | `gap5/10/20pct` (`2c8dd61d`, `51b7375e`, `7426cb1f`) | +0.001 / +0.001 / −0.001 MODEL; net credit +376/+283/−239; fixed count **and every 5 km block count** unchanged; catalogue PROXY Δ=0 (n=16,560), SGMC PROXY −0.0019/−0.0031/−0.0080. All model-grid bounds inside `|0.010|` (IR90-43). | HOLD; saturation/sign-control instrument. Receipt `evidence/spacing_kernel_gap_build_receipt.json`. |
| RELIEF basin↔piedmont | `p2b12p5pct`, `p2b15pct`, `b2p10pct` | +0.003 / +0.004 / −0.002 MODEL; previously unbuilt directions (IR90-41/42); PROXYs REPORT ONLY. | Human adjudicates after slots 1–3; not pre-emptive. Receipt `evidence/relief_s2_build_receipt.json`. |

Predictions were frozen before REPORT ONLY PROXYs. Leakage canary stayed <0.90 (0.5703 local-respacing/RELIEF; kernel-gap re-used 0.574747 because it introduced no new placement feature). PROXY is never a gate or score.

## Calendar to deadline (human confirms 2026-12-03)

- **Wk 1–2 (Oct 24–Nov 5):** run the conditional slot order; do not slot held CONCENTRATION/SPACING/frontier-PRUNE files.
- **Wk 3–4 (Nov 6–19):** combine only axes with receipts `Δ≥+0.010`; reserve one parent-vs-composite slot. If none clears +0.010, test one falsifier and stop building.
- **Wk 5–6 (Nov 20–Dec 3):** confirm the leader, choose ONE blind final plus `-zeros` fallback, revalidate both. Private chunks and expert-expanded labels can reverse a public-only read ([clarification](https://community.drivendata.org/t/where-do-you-draw-the-line/11536)).

## Better axes proposed — NOT built

- **TIP_CONDITIONAL_COLLAR:** 3 px collar except an along-strike tip cone. Mechanism: new geometry of existing systems; confounder: catalogue-mask endpoints; falsifier: paired Δ≤−0.010 vs 3.4 px rung.
- **REFILL_POLICY_PAIR:** pair sibling `PRUNEcollar3p0-FIFO` with `PRUNEcollar3p4Gapmax`. Mechanism: 2.3× refill credit; confounder: H19-5 non-fault support; falsifier: |Δ|<0.010 in both.
- **RELIEF_DONOR_MATCH:** same basin recipient at one matched dose funded from range (`r2b10`, exists) vs piedmont (new `p2b10`). Mechanism: donor quality; confounder: tercile composition; falsifier: paired Δ≤−0.010 or no evidence.
- **TIP_FLOOR / DISPERSION_CONTROL:** protect short tips, or test high→low 15 km prior. Confounders: drainage/lithologic tips, geodetic station density; falsifier: paired Δ≤−0.010 against shadowcont20 / held upward ladder.

**Reproduce:** `scripts/restore_data.py` → `scripts/restore_releases.py` (18 older pairs) → `scripts/build_prune_collar_gapmax.py --build`/`--verify`, `scripts/build_spacing_variants.py --build`/`--verify`, `scripts/build_relief_s2_variants.py --build`/`--verify`, `scripts/build_spacing_kernel_gap.py --build --rebuild-reserved`/`--verify`. Re-read every TIFF, run `src.validate`, match SHA-256 to the ledger. Agent never logs in, scrapes scores, or submits.
