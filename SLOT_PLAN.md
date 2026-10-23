# SLOT PLAN — strike-aligned PRUNE collar (session 2026-10-23, axis PRUNE)

**One line.** Parent R0 `h33-h33-2-b2` (37,654 unit dots, **CLAIM** 0.2778, no receipt on file) gets three
fixed-count variants whose only difference is the *shape* of the catalogue collar: the parent's 2 px Euclidean
collar is replaced by a strike-aligned ellipse that keeps 2 px along strike and widens **across** strike to
4 / 5 / 6 px. Built locally, format-gated, **not submitted**. `TOP_PUBLIC`, dated leaderboard target and weekly
quota remain unknown; a human must confirm them on the competition page before allocating a slot.

## Why this is the dose worth spending on

The only empirically positive step in the whole ledger is the parent's own collar: solo-d2.8 0.2708 → prune
≤2 px 0.2778 (**CLAIM**, owner-reported, no receipt). Every field-replacement lane scored 0.00–0.19. So the
collar is the one mechanism with a live gradient behind it, and the isotropic ladder above 2 px is already
built (GEMSDOE87 `PRUNE3/4`, GEMSDOE88 `p3px/p3.2/p3.7/p4.3`, GEMSDOE90 `3.5/4.5/5.5`) — none scored.
What has never been built is a collar that distinguishes the two directions of positional error. On a 400 m
line-spacing survey ([USGS GeoDAWN Area 2](https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7))
the error that matters is cross-strike; along strike a dot near a mapped trace is more plausibly the unmapped
continuation of that system, which the organiser states is scored
([where do you draw the line](https://community.drivendata.org/t/where-do-you-draw-the-line/11536)).

Built files (NaN primary, `-zeros` fallback), parent-diff vs R0:

| # | File (sha8) | Removed / refilled | % of R0 changed | Along-strike dots kept that an isotropic collar of the same radius would delete | Prediction (MODEL) |
|---|---|---|---|---|---|
| A4 | `h33-h33-2-b2-PRUNEanisoA4L2-20261023-0bf248e2` | 2,632 | 13.98 % | 1,193 | **+0.003**, plausible −0.010 to +0.010 |
| A5 | `h33-h33-2-b2-PRUNEanisoA5L2-20261023-15218061` | 3,663 | 19.46 % | 1,974 | **+0.002**, plausible −0.010 to +0.010 |
| A6 | `h33-h33-2-b2-PRUNEanisoA6L2-20261023-72dcdbd3` | 4,625 | 24.57 % | 2,176 | **+0.000**, plausible −0.010 to +0.010 |

Removed dots sit at a median 2.8–3.2 px **across** strike and 0.5 px along strike: the edit really is a
flank edit, not a wholesale re-thinning.

## Next three slots, in order (conditional on the human's quota)

| Order | File | Submit when | What the receipt changes |
|---|---|---|---|
| 1 | **A4** (`...PRUNEanisoA4L2...0bf248e2.tif`) | Now, if a weekly slot is free | Smallest dose, closest to the one rung that already paid. Δ ≥ +0.010 → the across-strike collar direction is real; go to slot 2. \|Δ\| < 0.010 → no evidence under the session rule; do **not** buy the A5 rung, use slot 2 for the control below. Δ ≤ −0.010 → close the collar line for this phase. |
| 2 | **A6** if slot 1 ≥ +0.010, else the isotropic comparator `GEMSDOE87 PRUNE4` (3,825 removed, same fixed-count refill policy) | After slot 1's receipt | A6 answers "does more collar keep paying?"; the isotropic rung answers the sharper question, "was the along-strike exemption worth anything?", against a nearly equal removed count. |
| 3 | Hold — reserve for the final submission and its fallback | Weeks 5–6 | Nothing new is learned; this protects the one final blind submission and the re-validation of both files. |

A live change below **0.01** is no evidence: the public chunks are a subset of the region and the private
score may differ. Do not promote a candidate on the local diagnostics; they rank nothing.

## Honest confound, stated up front

The refill is inherited from the parent lineage and is **dilutive**: 98.7–99.5 % of refill dots land within
3 px of a retained dot (median 1.00 px), i.e. mostly redundant mass that adds penalty and little fresh kernel
credit, and the replacements are non-local (median 845–888 px from the dot they replace). The predicted live
change therefore nets a positive collar term against a negative refill term, which is why all three doses
predict ≈ 0. If a receipt shows a null, the correct next test is the same collar **without** refill
(mass allowed to fall, as the parent's own 2 px rung did) — not a wider collar. That rung is *not* built here.

## Calendar to the supplied deadline

Deadline `2026-12-03` and the 3-scored-submissions-per-rolling-week rule come from the brief, not from a fresh
check (automated access to DrivenData is prohibited by its terms). The human must confirm both, plus the
current quota, from https://www.drivendata.org/competitions/306/competition-doe-gems/ and the rules document
https://docs.nlr.gov/docs/fy26osti/96647.pdf.

- **Week 1 (Oct 23–29):** slot 1 = A4. Request the submission-page receipt and its date.
- **Week 2 (Oct 30–Nov 5):** slot 2 only with slot 1's receipt in hand, per the table above.
- **Weeks 3–4 (Nov 6–19):** combine the two best *evidenced* axes only if at least one receipt clears ±0.010.
  With no receipt above the threshold, spend nothing: three unscored builds already exist per axis.
- **Weeks 5–6 (Nov 20–Dec 3):** choose the final file and a fallback blind, re-run `src.validate` on both,
  and check no duplicate sha256 is being re-submitted (at least 8 historical slots were exact repeats).

## Report-only diagnostics (never gates, never scores)

- Leakage canary (this session, 19 supplied feature bands, all 60,988 catalogue positives + 250,000 seeded
  off-catalogue footprint pixels): max symmetric AUC **0.5695** (band 4). No single feature above 0.90, so no
  stop-and-investigate trigger. This says nothing about live performance.
- Catalogue hide-and-recover and SGMC control: **not run** — no fold-clean instrument calibrated for a collar
  geometry; neither can rank these three files.

## Better axes proposed, not built this session

- **COLLAR_NOREFILL:** same strike-aligned collar, mass allowed to fall (≈ −10 % at A5). *Mechanism:* removes
  the dilution term above. *Confounder:* mass and geometry move together, so a gain cannot be attributed to
  either. *Falsifier:* paired live Δ ≤ −0.010, or a gain no larger than the isotropic no-refill rungs.
- **REDUNDANCY_BUDGET:** drop the dots whose 300 m kernel disk is already ≥ 90 % covered by neighbours, no
  refill, count free. *Mechanism:* T is a max-credit sum, so fully covered mass is pure penalty. *Confounder:*
  close parallel strands are real faults and their kernels overlap legitimately. *Falsifier:* paired live Δ ≤ −0.010.
