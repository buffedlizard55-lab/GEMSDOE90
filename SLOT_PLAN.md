# SLOT PLAN — merged R0 experiments (2026-10-23)

R0 `h33-h33-2-b2`: 37,654 dots; 0.2778 is **CLAIM**, with no receipt. Twelve local candidates exist (MASS 3, isotropic PRUNE 3, anisotropic PRUNE 3, SNAP 3); none was submitted. `TOP_PUBLIC`, dated target, quota and official cutoff remain human inputs. One entity, at most 3 scored slots per rolling week and one final file.

## Next three slots, in order

| Order | File / mechanism | Prediction (MODEL, not a score) | What the receipt changes |
|---|---|---|---|
| 1 | `MASSshadow10pct` — delete the 10% with least exclusive 300 m credit | +0.005 | Δ≥+0.010 validates mass reduction and promotes `MASSshadow30pct`; +0.005…+0.010 promotes 20%; Δ≤−0.005 stops the ladder. |
| 2 | `PRUNEanisoA4L2` — 4 px across-strike / 2 px along-strike collar | +0.003 | Δ≥+0.010 supports the along-strike exemption; Δ≤−0.010 closes this collar line. |
| 3 | Escalate whichever of slots 1–2 cleared +0.010; otherwise **hold** | — | Confirmation beats another blind mechanism. If both are null, preserve the slot and revalidate R0/final alternatives. |

Any |Δ|<0.010 is **no evidence** on public chunks; private chunks may differ. Use one encoding per slot; `-zeros.tif` is only a fallback. Copy submission-page score/date into the ledger.

## Where the other candidates stand

- **MASSshadow20pct/30pct:** nested escalation only, +0.009/+0.012 MODEL; a peak at 10% says the tail still earns credit.
- **PRUNEanisoA5/A6 and isotropic 3.5/4.5/5.5 px:** comparators, not automatic slots. Count-held refill is highly redundant (IR90-12); isotropic A4 comparison separates collar width from strike alignment.
- **SNAP TMI-VG / gravity-VG / VG-mean:** 35.701% / 7.965% / 21.273% moved, mean displacement 0.6330 / 0.1505 / 0.3853 px; predictions +0.001 / −0.002 / +0.002 MODEL. All SGMC PROXY deltas are slightly negative and canaries pass (0.509–0.523). **Not queued and LOCAL ONLY:** they inherit R0's 1,611 sub-3 px collar dots (IR90-15); prior TMI-VG overlap limits novelty (IR90-16).

## Calendar to supplied deadline (2026-12-03, UNVERIFIED)

- **Oct 23–29:** slot 1 only after human supplies dated TOP_PUBLIC, quota, deadline and R0 receipt; request candidate receipt/date.
- **Oct 30–Nov 5:** slot 2 with slot 1 receipt in hand. Do not substitute SNAP without clearing its collar blocker and a stronger decision rationale.
- **Nov 6–19:** slot 3 = escalation or hold. Twelve unscored files already exceed the useful feedback budget; do not build merely for novelty.
- **Nov 20–Dec 3:** choose final and fallback blind, revalidate both formats/hashes, confirm no exact repeat and use only one final submission.

Deadline/rule references for human confirmation: https://www.drivendata.org/competitions/306/competition-doe-gems/ and https://docs.nlr.gov/docs/fy26osti/96647.pdf. Agent did not fetch DrivenData or submit. Restore from pinned inputs and match each ledger SHA-256 before any upload.

## Proposed next axes — not built

- **COLLAR_NOREFILL:** strike-aligned collar with mass allowed to fall. *Confounder:* mass and geometry change together. *Falsifier:* Δ≤−0.010 or no gain over isotropic no-refill.
- **REDUNDANCY_BUDGET:** drop dots whose kernel disk is ≥90% covered, no refill. *Confounder:* real parallel strands overlap. *Falsifier:* paired Δ≤−0.010.
