# SLOT PLAN — R0 MASS dose, three files (2026-10-23)

**Agent-selected session axis: MASS.** Parent R0 `h33-h33-2-b2`, 37,654 unit dots, live `0.2778` = **CLAIM**
(no receipt on file). R0 rebuilt byte-identically to both pinned encodings this session
(`evidence/build_receipt_mass.json`), inputs 26/26 SHA-256 verified.

**Why MASS, and why these three.** The brief's algebra is DTI = T/(0.2T + 0.2(S−M) + 0.8|G|). A dot farther
than 3 px from hidden truth adds nothing to T and a full 1.0 to (S−M); a dot whose kernel disc is already
claimed by a neighbour adds nothing to T *and* little to (S−M). Mass is therefore not a neutral knob, and the
two prior wins from *removing* dots (d1.5→d2.8 +0.012; prune≤2 px +0.007, both CLAIM) point the same way.
Each file makes one change from R0:

| # | File | Change vs R0 | n_dots | % changed | Prediction (MODEL, not a score) |
|---|---|---|---|---|---|
| 1 | `MASSuniq20-20261023-5138de0f` | collar d_cat≥3 px (1,611 dots, forced by constraint 4) + 7,531 least-unique-kernel-credit dots | 28,512 | 24.279% | **+0.005**, interval −0.010 to +0.012 |
| 2 | `MASSfifo20-20261023-1be8302f` | identical collar + 7,531 dots from the bottom of the parent FIFO-BFS rank | 28,512 | 24.279% | **+0.001**, interval −0.012 to +0.009 |
| 3 | `MASSuniq30-20261023-56c5f82f` | identical collar + 11,296 least-unique-credit dots | 24,747 | 34.278% | **+0.007**, interval −0.015 to +0.018 |

`uniq20` and `fifo20` have **the same count and the same collar**: slot 1 vs slot 2 isolates *which* dots to
drop, slot 1 vs slot 3 isolates *how many*. Measured on the parent's own H19-5 support: `uniq20` drops dots
of mean unique credit 1.00 (kept 2.29) and mean local support 1.14 px (kept 2.76), while `fifo20` drops mean
credit 2.04 vs 2.02 kept — i.e. the brief-literal FIFO tail is statistically indistinguishable from a random
20% cut. If a FIFO-style cut scores ≈0 that is evidence about its *selection*, not about mass.

**What each receipt would change.** Δ ≥ +0.010 for `uniq20`/`uniq30` ⇒ mass reduction is real and the uniq
rule is the keeper; next week push −40% and combine with CONCENTRATION. Δ ≤ −0.010 ⇒ the removed dots were
carrying T and mass reduction is closed for every rule. `fifo20` − `uniq20` ≥ +0.010 would mean the ordering
that fits the algebra is *worse* than an arbitrary one and the metric model is wrong. `|Δ| < 0.01` = no
evidence; do not promote on the proxy (see "Report-only" below).

**Order of upload (human, one file per scored slot):** 1) `MASSuniq20` 2) `MASSuniq30` 3) `MASSfifo20`.
Submit 1 and 2 only if two slots are free in the same rolling week; the pair is the informative comparison.
`-zeros.tif` twins are the zero-outside fallback, not a second experiment. **Nothing here has been
submitted and no score is claimed.**

## Report-only, and why the proxy is unusable here

Catalogue hide-and-recover PROXY returns exactly 0.000 for all three files and 0.0044 for R0: the kernel
radius is exactly 3 px and constraint 4 forbids dots within 3 px of the catalogue, so T on catalogue pixels is
identically zero. That is construction, not quality — this proxy cannot separate any compliant file
(`evidence/diagnostics_mass.json`). Leakage canary: max single-feature symmetric AUC 0.5696 (band 4), below the
0.90 stop threshold. SGMC control not run; not a gate.

## Calendar to the deadline (2026-12-03, supplied by the brief, not re-verified)

- **Wk of Oct 23:** at most 3 slots; use slots on `uniq20` + `uniq30` (and `fifo20` if a third is free).
- **Wk of Oct 30:** if Δ ≥ +0.010, build the next uniq dose (−40%) and the best combo axis; if |Δ| < 0.01,
  mass is flat below 30% and slots go to position/field work instead.
- **Wk of Nov 6–20:** combine the two best receipted axes only; one change at a time, count fixed.
- **Wk of Nov 27–Dec 3:** re-validate format of the chosen final file and its fallback twin; choose blind.

## Better axes proposed, not built this session

- **MASS_RANK_PRIOR:** rank the drop by exact expected DTI marginal loss under a calibrated truth prior
  (e.g. KDE of catalogue geometry + relief tercile) instead of unique credit. *Confounder:* the prior is
  itself built from the catalogue the parent already used. *Falsifier:* paired live Δ ≤ −0.010 vs `uniq20`.
- **COVERAGE_ADD:** the opposite dose — add dots only where a 3 px disc is empty and the field is strong.
  *Confounder:* each added dot costs 0.2/Den unless it lands on truth, so the arm needs precision > 0.4.
  *Falsifier:* live Δ ≤ −0.010 while `uniq20` is positive ⇒ coverage, not sparsity, is the binding constraint.
- **KERNEL_RADIUS audit:** re-space *retained* dots so no two sit < 1.5 px apart (a spacing, not mass, edit).
  *Confounder:* real parallel strands and step-overs. *Falsifier:* live Δ ≤ −0.010 at matched count.
