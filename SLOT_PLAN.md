# SLOT PLAN — R0 axis SNAP (cross-strike), 2026-10-23

**Agent-selected session axis: SNAP.** Parent R0 = `h33-h33-2-b2`, 37,654 unit dots, rebuilt byte-identically in this sandbox (`c55bafc4…` / `baeae321…`, d2.8 ranking 0 px difference). Its `0.2778` is a **CLAIM**, not a receipt. Three arms are **BUILT** locally under ignored `releases/`; nothing was submitted and no score was produced. `TOP_PUBLIC`, dated leaderboard target, weekly quota used/left and the deadline cutoff remain unknown; the human must supply them.

## Why SNAP and not the rest of the menu

This session measured two facts that bound every remaining axis:

1. **The H19-5 support is exhausted.** Only 61,481 footprint pixels are outside R0 and ≥3 px from the catalogue, and 87 % of those sit exactly 1.0 px from an R0 dot. Any count-preserving edit that "refills" therefore buys near-duplicate coverage, and any mass *added* through MASS is a duplicate as well. Under the DTI algebra the largest term is `0.8·|G|` (≈0.85 of the denominator at any G consistent with the catalogue density), so a useless dot costs ≈9.7e-7 and a duplicate — which adds no `T` — costs the same. Adding 10 % mass to a saturated support is a ≈−0.004 bet; removing 10 % of unique dots is a ≈−0.024 bet.
2. **Position, not mass, is the only lever left inside the menu.** GeoDAWN Area 2 was flown at 400 m line spacing 150–200 m above terrain (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7), i.e. a cross-strike position error of order the 300 m kernel radius, and the kernel credit is linear in distance. A 2 px cross-strike correction changes `T` without changing mass — the only menu edit with that property.

## The three arms (all `CAP = 2 px`, identical shared collar step)

| Order | Candidate file | Dose | Dots moved / mean disp. | Prediction (MODEL, never a score) | What its receipt changes |
|---|---|---|---|---|---|
| 1 | `h33-h33-2-b2-SNAPXk4p0-20261023-3dd81141.tif` | strict (ε = 4× field IQR/100) | 12,134 · 32.2 % · 2.00 px | **+0.004**, plausible −0.006…+0.010 | If Δ ≥ +0.010 the two-source gradient consensus has real positional skill and the dose should be pushed; if Δ ≤ −0.010, aligning to TMI/gravity edges is worse than the field's own ridges and the whole SNAP family closes. |
| 2 | `h33-h33-2-b2-SNAPXk0p25-20261023-7ac0b578.tif` | permissive (ε = 0.25×) | 22,876 · 60.8 % · 2.00 px | **+0.001**, plausible −0.010…+0.014 | Pair this with slot 1: permissive ≫ strict falsifies the confidence story (weak edge gains are not worse), i.e. the consensus is close to noise and only the *number* of moved dots matters. |
| 3 | `h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` (already built, `evidence/build_receipt.json`) | catalogue collar 2→3.5 px | 2,702 · 14.4 % changed | **+0.002**, plausible −0.010…+0.010 | The one arm whose mechanism was already paid for by the lineage: pruning ≤2 px scored +0.007 (CLAIM). Tests whether the collar optimum sits just past 3 px. Hold this slot until the SNAP pair is read. |

`SNAPXk1p0` (54.4 % moved) is the middle dose; it is the fallback if slot 1 is ambiguous **and** slot 2 is used. All arms share: zero catalogue mass, minimum catalogue distance 3.0 px (the parent's 1,611 sub-3 px dots are removed and the count refilled identically in every arm — hard constraint #4), 37,654 dots, ≥2.0 px separation, 45° half-angle about the local fault normal estimated from the 8 nearest parent dots.

**Encoding:** upload one file per slot — the NaN-outside primary, or its `-zeros` twin if the portal rejects NaN. Never both.

## Next 3 slots, in order, then the calendar

1. **Slot 1 — `SNAPXk4p0`.** Highest predicted value, lowest variance (fewest dots moved). Cost of being wrong: −0.006.
2. **Slot 2 — `SNAPXk0p25`** (if slot 1 ≥ +0.010) **or** `PRUNE3p5px` (if slot 1 ≤ −0.010). The permissive arm is only informative *after* the strict arm: alone it cannot separate "edge skill" from "more movement".
3. **Slot 3 — hold.** The entity already has six BUILT candidates in this repository and, per the ledger audit of the sibling repositories (GEMSDOE84–92), at least forty elsewhere, with **no receipt recorded anywhere**. A seventh candidate is worth less than a receipt for anything. Use slot 3 only if both SNAP receipts land inside ±0.010 — then it is the last probe of this family (`SNAPXk1p0`).

Calendar to the supplied deadline (`2026-12-03`, UNVERIFIED — confirm on the competition page; automated access to DrivenData is prohibited):

- **Weeks 1–2 (Oct 23 – Nov 5):** slots 1 and 2. Request the portal receipt text and date for every submission, including the historical R0 line (the R0 receipt needs *no* slot — copy it from submission history; a claimed 0.2778 with no receipt is the single weakest link in the project).
- **Weeks 3–4 (Nov 6 – Nov 19):** only if a SNAP receipt is ≥ +0.010, push the dose (stricter/permissive pair at 3 px is **not** allowed by the brief's ≤2 px rule, so instead combine: SNAP-strict applied to the best surviving PRUNE arm). If both are inside ±0.010, stop building menu variants and switch to field quality — the algebra says the remaining menu levers are all ≤1 % of the score.
- **Weeks 5–6 (Nov 20 – Dec 3):** choose the final file and a fallback blind from *receipted* files only; re-run `scripts/build_snap_variants.py --verify` (or `scripts/restore_releases.py`) and the format gate on both, then stop.

## Report-only diagnostics (never gates)

- **Block-density CV** (the brief's 0.51–0.59 hint): CV is scale-dependent and the hint states no block size. R0's dot-density CV is 1.870 at 1 km, 1.368 at 2 km, 0.899 at 5 km, 0.639 at 10 km, 0.441 at 20 km. R0 is already inside/near the hinted band at 10–20 km, so the hint gives **no direction** for a concentration edit at km scale, and it was not used to rank anything.
- **Catalogue hide-and-recover / SGMC control:** not run. No fold-clean instrument is validated for a positional edit, and the recorded live correlation of the hide-and-recover proxy is −0.87…+0.54 (n = 12–14), so it cannot gate a slot.
- **Leakage canary:** unchanged pinned inputs; previous run max symmetric AUC 0.5700 (`geod_2ndinv`), below the 0.90 stop threshold.
- **Structure-tensor check:** the arms are cross-strike *by construction*; mean displacement is 2.00 px in every arm because the smoothed consensus rises monotonically over 2 px for most dots. The arms therefore differ in **which** dots move (confidence), not in how far — read a "strict vs permissive" difference as a statement about the edge field's strong signals, not about distance.

## Better axes proposed only — NOT built this session

- **KERNEL_REDUNDANCY.** *Mechanism:* under max-aggregation a second dot inside the same 300 m kernel adds `0.2·(1−k)` to the denominator and nothing to `T`; remove only dots whose removal leaves `T` unchanged, refill elsewhere. *Confounder:* genuinely parallel strands and step-overs are close by construction. *Falsifier:* paired live Δ ≤ −0.010. (This is the only menu-adjacent edit that is *not* predicted negative by the algebra.)
- **ANNULUS_DENSITY.** *Mechanism:* "newly mapped geometry of existing systems" (https://community.drivendata.org/t/where-do-you-draw-the-line/11536) implies new truth sits in the 3–10 px collar around known traces; move fixed-count mass into that annulus (currently lift only 1.34× vs area). *Confounder:* mapping effort, not fault density, drives the catalogue; the mask removes the traces themselves. *Falsifier:* paired live Δ ≤ −0.010 or no CV change.
- **FIELD_REPLACEMENT, not an axis.** The only lever with >0.01 potential is a better field: the ledger's replacement lanes scored 0.00–0.19 against R0's 0.2778. No further micro-axis sweep should be funded before that is accepted or refuted by one receipted test.

## What the human must supply

Dated `TOP_PUBLIC`; confirmed deadline/cutoff and the 3-per-rolling-week quota state; the R0 portal receipt (no slot needed); one receipt per submitted arm; a data-use-terms decision for the owner-mirrored competition inputs before any raster is shared (IR90-02).
