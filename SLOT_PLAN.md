# SLOT PLAN — PRUNE collar dose (2026-10-23)

**State.** Parent R0 is `h33-h33-2-b2`, 37,654 unit dots; 0.2778 is a **CLAIM**, not a receipt. All 26 manifest pins were verified, and R0 was rebuilt byte-identically (`evidence/r0_rebuild_receipt.json`). R0 has 1,611 dots within 3 px of the catalogue. I selected **PRUNE** so the required ≥3 px exclusion can be tested without adding a second, confounding relocation axis. Exact candidates and hashes are in `evidence/build_receipt.json`; the ignored TIFFs can be restored and revalidated with the commands in `docs/SUBMIT.md`. None has been submitted.

Known catalogue pixels are masked pixel-exactly, while adjacent new-fault pixels can still score; widening the collar may therefore remove either false-positive mass or true new-fault credit ([organizer clarification](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516)). Refill holds 37,654 dots using the reconstructed FIFO-BFS H19-5 order, an algorithmic tie-break—not a geological probability.

## Next three slots

| Order / candidate | Prediction (MODEL, not a score) | What the receipt changes |
|---|---|---|
| 1. `h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` | +0.002 DTI; plausible interval −0.010 to +0.010 | Same-week paired Δ≥+0.010 supports a collar just beyond the 300 m metric radius; Δ≤−0.010 rejects this cutoff/refill policy. |
| 2. `h33-h33-2-b2-PRUNE4p5px-20261023-be7a1217.tif` | +0.000 DTI; same interval | Tests a wider collar only if slot 1 leaves the question worth pursuing; |Δ|<0.010 is no evidence. |
| 3. `h33-h33-2-b2-PRUNE5p5px-20261023-a69816c7.tif` | −0.003 DTI; same interval | A Δ≤−0.010 supports retaining nearby dots; Δ≥+0.010 reverses the prediction. |

These exact `(PRUNE, value)` pairs are already BUILT; do not rebuild them as new experiments. Upload at most one encoding per available scored slot, only after the human checks the entity quota (3 per rolling week) and confirms the deadline. Current `TOP_PUBLIC`, its date, slots used/remaining, and the exact cutoff are unknown. The human fills them from the [competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/) and [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf); no automated page access or submission was made.

## Calendar to the supplied deadline (2026-12-03; unverified)

- **Oct 23–Nov 5:** consider candidate 1 if a weekly slot is available; record the portal receipt.
- **Nov 6–19:** consider candidate 2 only if receipt 1 is ≥+0.010 or the unresolved collar question remains worth a slot.
- **Nov 20–Dec 3:** consider candidate 3 only if earlier receipts justify it; otherwise preserve slots. Choose the final file and fallback blind and revalidate both. One final submission only.

**Report-only:** prior leakage canary max symmetric AUC 0.5700; not predictive validation. Catalogue hide-and-recover and SGMC control were not run; no proxy gates a candidate. **Better axes proposed, not built:** (1) `EDGE_COHERENCE`—multi-scale edge persistence; confounder: lithologic contacts/drainage scarps; falsifier: paired Δ≤−0.010 or no repeatable untouched-fold gain. (2) `KERNEL_BUDGET`—re-space redundant nearby kernel coverage; confounder: real parallel strands/step-overs; falsifier: paired Δ≤−0.010. The official metric uses a 300 m triangular kernel ([metric page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)).
