# SLOT PLAN — receipts first; new SPACING ladder HELD (2026-10-24)

**R0:** `h33-h33-2-b2`, 37,654 dots; 0.2778 is **CLAIM**, not a receipt. Human supplies dated `TOP_PUBLIC`, quota, 2026-12-03 confirmation, and adjudicates sibling-repo entity scope before any slot ([rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). Never repeat a hash or `(parent,axis,value)`. Live `|Δ|<0.010` = **no evidence**.

## Next 3 slots (NaN primary, one file/slot)

1. **`…MASSadd5pctq50-20261023-c4e6144c.tif`**, pred **+0.008**. `Δ≥+0.010` → add dose pays; `Δ≤−0.010` → close adds; null → no evidence.
2. Positive branch: **`…MASSadd10pctq50-20261023-5edc84de.tif`** (+0.014). Negative branch: **`…MASSshadowcont20pct-20261023-66d961ba.tif`** (+0.009). Null branch: **`…PRUNEanisoA5L1-20261023-cd2c60ce.tif`** (+0.005).
3. Exactly one conditional arm: add20 q50 **`…f94efff4.tif`** (+0.022) after two rising add receipts; placement control **`…MASSadd10pctBlocknext-20261023-89d16c16.tif`** (+0.004) after a flat add; continuity **`…MASSshadowcont40pct-20261023-92be4121.tif`** (+0.013) after a positive continuity receipt; or **`…PRUNEanisoA5L0p5-20261023-91ff3771.tif`** (+0.003) after positive A5/L1. Null never licenses a same-axis dose guess.

## This session: SPACING kernel-gap equalization — BUILT, HELD

Agent-selected `AXIS=SPACING`: fixed-count, 5 km block-local moves from lowest exclusive to highest marginal R=3 px H19-5 credit. Count and every 5 km block count unchanged; CV 0.9011/0.6353/0.5103 at 5/10/15 km, before=after. Added dots `d_cat≥3 px`; untouched parent dots retain R0's 2.236 px floor (IR90-41).

| Candidate | Moved / diff | Net credit | MODEL Δ | Catalogue PROXY Δ, n=16,560 | SGMC PROXY Δ |
|---|---:|---:|---:|---:|---:|
| `…SPACINGgap5pct-20261024-2c8dd61d` | 1,883 / 10.00% | +376.3 | **+0.001** (−0.002…+0.008) | 0, CI [0,0] | −0.0019 |
| `…SPACINGgap10pct-20261024-51b7375e` | 3,765 / 20.00% | +282.8 | **+0.001** (−0.002…+0.007) | 0, CI [0,0] | −0.0031 |
| `…SPACINGgap20pct-20261024-7426cb1f` | 7,531 / 40.00% | −238.9 | **−0.001** (−0.006…+0.002) | 0, CI [0,0] | −0.0080 |

Predictions frozen before PROXYs. R0 PROXY 0.005692 catalogue / 0.095386 SGMC; leakage canary not re-run (no new placement feature; prior max symmetric AUC 0.574747). **HOLD all three:** every point prediction and the entire model grid are inside `|0.010|`, and SGMC is negative at every dose. Receipt `evidence/spacing_kernel_gap_build_receipt.json`; PROXY is never a gate/score.

## Calendar to deadline (human confirms 2026-12-03)

- **Wk 1–2 (Oct 24–Nov 5):** obtain R0 receipt if possible; run the conditional slots. Do not slot held CONCENTRATION/SPACING.
- **Wk 3–4 (Nov 6–19):** combine only axes with receipts `Δ≥+0.010`; reserve one slot for parent-vs-composite. If none clears +0.010, test one falsifier and stop building.
- **Wk 5–6 (Nov 20–Dec 3):** confirm the leader, choose ONE blind final plus `-zeros` fallback, and re-run the format gate on both. Private chunks and expert-expanded labels can reverse a public-only read ([clarification](https://community.drivendata.org/t/where-do-you-draw-the-line/11536)).

## Better axes proposed — NOT built

- **TIP_FLOOR:** protect short tips/relay cones, not only ≥10-dot strands. Mechanism: real newly mapped continuations; confounder: drainage/lithologic tips; falsifier: paired Δ≤−0.010 vs shadowcont20.
- **DISPERSION_CONTROL:** fixed-count high→low 15 km prior. Mechanism: R0 CV already exceeds 0.51–0.59 and upward moves lose credit; confounder: geodetic station density; falsifier: Δ≤−0.010 vs held upward ladder.
- **PHASE2_TRACE:** ≥1 km strike-consistent traces + geologist evidence. Mechanism: expert-expanded labels reward reviewable traces; confounder: unfaulted lineaments; falsifier: >20% traces rejected in geological review. Not a weekly slot unless human opts in.

**Reproduce:** `scripts/restore_data.py` → `scripts/restore_releases.py` (18 older pairs) → `scripts/build_spacing_kernel_gap.py --build --rebuild-reserved` → `--verify`. Re-read every TIFF, run `src.validate`, match SHA-256 to the ledger. Agent never logs in, scrapes scores, or submits.
