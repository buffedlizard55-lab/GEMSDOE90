# Mechanism cards
# Mechanism cards


## Session 2026-10-23 (2): AXIS = PRUNE, value family = strike-aligned (anisotropic) collar

Parent R0 `h33-h33-2-b2`: 37,654 unit-mass dots, isotropic >2 px catalogue collar; 0.2778 is a **CLAIM**
(no submission-page receipt). These three files are **BUILT**, format-gated and unscored. Their predictions are
**MODEL**. Files live in ignored `releases/`; hashes and full statistics are in `evidence/build_aniso_receipt.json`.

Shared hypothesis, written for a structural geologist: the parent's collar treats positional error as
direction-free, but the two directions do different work. Across strike, a dot 2–3 px from a mapped trace is
usually flank mass: the known pixels there are masked anyway, so it earns penalty without new credit. Along
strike, a dot near a mapped trace is plausibly the continuation of that system — geometry the organiser says is
still scored as "new". A collar that widens only across strike should therefore buy the precision gain of a
3 px uniform collar while keeping the along-strike credit a uniform 3 px collar would throw away.

Mechanism: local strike from a structure tensor of the catalogue mask (major eigenvector = across strike, since a
thin trace's gradients run across it); each dot is projected onto that frame at its nearest catalogue pixel and
removed if `(along/2)² + (across/A)² ≤ 1`. Where the tensor is incoherent (< 0.3), no along-strike exemption is
granted and the collar falls back to isotropic A. The count is held at 37,654 by refilling from the pinned
H19-5 support in the lineage's recovered FIFO-BFS thinning order, outside the collar.

| Variant | Removed / refilled | % of R0 changed | Along-strike dots kept that an isotropic collar of the same radius deletes | Predicted live change (MODEL) | Non-fault confounder | Falsifier |
|---|---|---|---|---|---|---|
| A4 (`…0bf248e2`) | 2,632 | 13.98 % | 1,193 | **+0.003** (−0.010 to +0.010) | A parallel strand or a step-over a few pixels across strike from a mapped trace is a real fault, not flank noise; steeply dipping strands surface offset from their mapped trace. | Paired same-week Δ ≤ −0.010 rejects the across-strike-only collar at this dose; \|Δ\| < 0.010 is no evidence. |
| A5 (`…15218061`) | 3,663 | 19.46 % | 1,974 | **+0.002** (−0.010 to +0.010) | Same, plus: the refill pool shrinks and its replacement pixels get worse as the collar widens. | As above; a monotone decline over A4→A6 rejects the dose-response the mechanism implies. |
| A6 (`…72dcdbd3`) | 4,625 | 24.57 % | 2,176 | **+0.000** (−0.010 to +0.010) | Same; a 600 m across-strike halo is beyond survey positional error, so genuine adjacent truth starts to be deleted. | Paired same-week Δ ≥ +0.010 would falsify the predicted flattening and support a still wider collar. |

Prediction decomposition (why the numbers are small and nearly flat): positive collar term scales with removed
dots (+0.004…+0.008), negative refill term scales with refills (−0.001…−0.005). The refill is the weak link:
98.7–99.5 % of refill dots land within 3 px of a retained dot (median 1.00 px), i.e. they mostly add the
0.2·(S−M) penalty and very little fresh kernel credit, and the replacement is non-local (median 845–888 px from
the dot it replaces). This dilution is inherited from the parent lineage's refill policy and is **not** part of
the collar geometry under test — see `IRREGULARITIES.md` IR90-12. Removed dots sit at median 2.8–3.2 px across
strike and 0.5 px along strike, so the edit is a genuine flank edit.

Report-only diagnostics: leakage canary max symmetric AUC 0.5695 over 19 supplied bands (60,988 catalogue
positives + 250,000 seeded off-catalogue pixels) — no single feature above 0.90. Catalogue hide-and-recover and
SGMC control were not run; no fold-clean instrument is calibrated for a collar geometry, and none of these
numbers rank a file.

---

## Session 2026-10-23 (1): AXIS = PRUNE, isotropic collar rungs 3.5 / 4.5 / 5.5 px

---


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

## Report-only instruments

Neither session used a PROXY to rank or gate a candidate. The catalogue hide-and-recover holdout
correlated −0.87 to +0.54 with live scores (n = 12–14 files) in the ledger, so it cannot adjudicate a
±0.01 question. The leakage canary is not applicable to the MASS ladder: its ranking uses no feature
band and no label — only the parent's own dot coordinates.
