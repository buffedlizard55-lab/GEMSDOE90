# Mechanism cards

One card per built variant, written for a structural geologist. Every prediction is **MODEL**, not a
score. Parent for both sessions: R0 `h33-h33-2-b2` (37,654 unit-mass dots, claimed live 0.2778 =
**CLAIM**, no receipt in `ledger/`). The agent has never submitted a file.

---

## Session 2026-10-23b — AXIS = MASS (shadow-drop ladder)

**Shared mechanism.** The brief's algebra is `DTI = T / (0.2T + 0.2(S − M) + 0.8|G|)`, where `T` is
kernel credit, `S` the emitted mass, `M = Σ p·max_g k` and `|G|` the truth pixel count. Because `T`
is a *max* over dots inside the 300 m kernel, a dot whose disk is already covered by closer
neighbours still pays its full `0.2` share of `S − M` while supplying almost no new `T`. Deleting
such a dot strictly lowers the denominator; the only risk is the credit it uniquely supplied.

That risk is measured exactly, without truth, as **exclusive credit** `E_j`: the credit dot `j`
supplies at pixels where every other kept dot supplies less (`src/mass.py`, exact under A1/A2 for the
triangular 300 m kernel). Three doses delete 10 / 20 / 30 % of R0 in ascending `E_j`, recomputed after
each deletion. The doses are nested, so each larger file is a strict superset of the previous
deletion set. **No additions, no moves, no collar change** — a pure mass edit.

At the same 3,765 removals the parent's *stored* FIFO-BFS thinning order destroys 53 % more
exclusive credit than this order does, so the existing `MASS -10 %` style candidates are a different
and mechanically worse experiment (`evidence/mass_build_receipt.json`).

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| `MASSshadow10pct` → 33,889 dots | Deletes the 3,765 dots with least exclusive credit (mean E 4.44 of an isolated dot's 9.42); keeps 93.5 % of R0's total exclusive credit. | Exclusive credit is truth-free: a low-E dot can still be the only dot over a truth pixel in its exclusive lens; contacts, drainage margins and topographic lineaments inside the H19-5 support look identical. | **+0.005** (first-order bracket +0.001 to +0.025; ladder-slope estimate +0.004) | Same-week paired receipt vs R0 with Δ ≤ −0.005. \|Δ\| < 0.010 is no evidence under the session rule. |
| `MASSshadow20pct` → 30,123 dots | Deletes 7,531 dots (mean E 5.00); keeps 85.3 % of exclusive credit. Tests whether the mass term still dominates the credit loss at twice the dose. | As above; the second dose starts reaching dots on sparser strands, where exclusive credit is higher because neighbours are farther. | **+0.009** (+0.001 to +0.048; ladder +0.008) | A Δ at least as good as dose 1 but not better (i.e. flat) means the mass term is already saturating; a decline means credit loss dominates. |
| `MASSshadow30pct` → 26,358 dots | Deletes 11,296 dots (mean E 5.59); keeps 75.3 % of exclusive credit. Deliberately past the likely turnover to locate it in one week. | As above, plus: at 30 % the file starts to look like a different sampling design (sparser), so a drop could reflect lost trace continuity rather than mass. | **+0.012** (0.000 to +0.071; ladder +0.012) | Δ ≤ 0 while dose 2 was ≥ +0.010 locates the turnover between 20 and 30 %; Δ ≤ −0.005 at any dose ends this direction. |

The predictions are bracketed, not fitted: `c` (the deleted dots' own credit to truth) and `|G|` are
unobservable without labels, so the brackets span `c ∈ [0.15, 0.45]` and `|G| ∈ [20k, 100k]`. The
adopted number for each dose is the ladder-slope estimate — the claimed chain 121k px → 37.6k dots
bought +0.0856 for 83,477 dots removed (+0.00102/dot) → +0.0038 / +0.0077 / +0.0116 — plus 0.001,
because per-dot credit loss is smaller here than in uniform coarsening.

**Collar note.** Brief §4 asks for ≥ 3 px from the catalogue. R0's own minimum is 2.236 px (1,611
dots, IR90-01). These variants inherit that collar unchanged, because moving it would be a second
axis, and they add no mass at all (see IRREGULARITIES IR90-07).

---

## Session 2026-10-23a — AXIS = PRUNE (previous, unchanged)

Parent R0 rebuilt byte-identically from the pinned h27-4 solo-d2.8 parent
(`evidence/r0_rebuild_receipt.json`). Shared hypothesis: the >2 px catalogue collar may be too
narrow. Known pixels are masked pixel-exactly, yet new-fault truth may lie adjacent to known traces,
so a broader collar can remove true new-fault credit as well as false-positive mass. Each variant
removes parent dots at or inside a larger Euclidean-distance threshold and refills to exactly 37,654
from the H19-5 support outside the threshold. Refill priority is the rebuilt FIFO-BFS visitation
order — an algorithmic tie-break, **not** a geological probability.

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| PRUNE 3.5 px | Extending the collar just beyond the 300 m kernel radius removes redundant near-catalogue mass while retaining most of the incumbent's high-priority ridge set. 2,702 removed/refilled. | New mapped splays, parallel strands or geometry extensions within 350 m of known traces; refill lineaments may be contacts or drainage margins. | +0.002 (−0.010 to +0.010) | Paired Δ ≤ −0.010. |
| PRUNE 4.5 px | A wider uncertainty halo further cuts false-positive mass but sacrifices more near-catalogue truth. 4,848 removed/refilled. | As above, plus broadened collar more likely to delete newly mapped faults. | +0.000 (−0.010 to +0.010) | Paired Δ ≤ −0.010. |
| PRUNE 5.5 px | A 550 m halo is likely beyond useful positional uncertainty, so lost adjacent new-fault credit may exceed any false-positive saving. 6,130 removed/refilled. | Possibly real displacement of mapped geometry from its true trace. | −0.003 (−0.010 to +0.010) | Paired Δ ≥ +0.010. |

Full inputs, hashes, parent diffs and format receipts: `evidence/build_receipt.json`.

---

## Session 2026-10-23c — AXIS = MASS (high dose + credit-blind control)

**Shared mechanism.** `DTI = T / (0.2T + 0.2(S − M) + 0.8|G|)`. The mass term is paid per dot; `T` is a
*max* over dots inside the 300 m kernel. A dot whose disk is covered by closer neighbours pays its full
`0.2` share and supplies almost no `T`, so deleting it lowers the denominator. Exclusive credit `E_j`
(exact, truth-free, `src/mass.py`) is the cheapest available ordering. These arms continue the
10/20/30 % ladder to 40 % and 48 %, and add the control the ladder never had: the same 40 % dose with a
seeded uniform random subset, which is blind to credit but keeps R0's spatial distribution in expectation.

**Two dose/ordering choices were probed and rejected before submission**, and both probes are recorded in
the receipt. (1) The parent's *stored* 8-connected FIFO-BFS order — the ordering the sibling `MASS ±10 %`
doses use — deletes one south-east corner: at 10 % of R0 it already empties 162 contiguous 5 km blocks,
at 40 % it empties 632 (41 % of all blocks holding ≥ 20 dots). That is a region-isolated file under Hard
Constraint #5 and confounds dose with geography. (2) A 50 % shadow drop is the deepest dose, and there the
greedy starts emptying whole contiguous regions too (largest emptied cluster 17 blocks = 425 km²). The
deep arm therefore stops at **48 %**, the largest shadow dose whose every candidate passes the
region-evenness gate.

**Structural finding that competes with the predicted sign.** At 5 px linking R0 carries 838 strands of
≥ 10 dots (≥ 1 km). `shadow40` keeps **none** of them and pushes mean dot spacing from 3.74 px to
6.19 px, so every surviving dot is farther than the kernel radius from its nearest neighbour. `rand40`
keeps 136 of those strands at 4.70 px spacing. The exclusive-credit greedy preferentially deletes densely
sampled stretches — the parts of a trace that are best observed — and keeps isolated singletons. If new
faults are line-like, that can cost more `T` than the mass saving is worth.

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| `MASSshadow40pct` → 22,592 dots | Deletes 15,062 dots (mean E 6.15 of an isolated dot's 9.42), 36.2 % of R0's total exclusive credit, in ascending-E order recomputed after each deletion. | Low-E dots can still be the only dot over a genuine new strand shadowed by a mapped one; contacts, drainage margins and topographic lineaments behave identically. Deletes 401 of R0's 1,611 sub-3 px collar dots as a side effect. | **+0.014** (bracket +0.004 to +0.025); competing prediction: could fall *below* `rand40` because it destroys all 838 long strands | Paired Δ ≤ −0.005 vs R0 ends the direction. `rand40` within 0.005 of this file ⇒ ranking adds nothing. \|Δ\| < 0.010 = no evidence. |
| `MASSshadow48pct` → 19,580 dots | Deletes 18,074 dots (mean E 6.61), 46.7 % of total exclusive credit. The deepest dose that keeps the file spatially even; locates the turnover. | As above, plus: at 48 % the file is a different sampling design (0.38 % of the footprint), so a drop may reflect lost trace continuity rather than mass. | **+0.015** (+0.002 to +0.030) | Δ ≤ 0 while 40 % was ≥ +0.010 puts the optimum between 30 % and 48 %. Δ ≤ −0.005 at any dose ends this direction. |
| `MASSrandom40pct` → 22,592 dots | Credit-blind control: 15,062 dots drawn uniformly at random, seed 20261023. At matched count it destroys 10.6 % more exclusive credit than `shadow40` (E 102,441 vs 92,598 of 255,848 total) but keeps 136 long strands. | Random deletion has no geological content at all; its score measures what *any* 40 % thinning does, which is exactly what makes it the control. | **+0.013** (+0.004 to +0.023) | If it beats `shadow40` by ≥ 0.005 the exclusive-credit ranking is wrong and must be abandoned; within 0.005 of it, ranking adds nothing and only dose matters. |

**Collar note.** Brief §4 asks for ≥ 3 px from the catalogue; R0's own minimum is 2.236 px (1,611 dots,
IR90-01). These arms only delete, so no new near-catalogue mass is created, but the inherited collar is
unchanged. Moving it is a second axis and was not done here.

**Reproduce.** `scripts/build_mass_high_dose.py --build` then `--verify`; receipt
`evidence/mass_high_dose_receipt.json`; ledger rows in `ledger/submissions.csv` (`status=BUILT`,
`receipt=N`, `receipt_score` empty — the agent never submits).

---

## Report-only instruments

Neither session used a PROXY to rank or gate a candidate. The catalogue hide-and-recover holdout
correlated −0.87 to +0.54 with live scores (n = 12–14 files) in the ledger, so it cannot adjudicate a
±0.01 question. The leakage canary is not applicable to the MASS ladder: its ranking uses no feature
band and no label — only the parent's own dot coordinates.
