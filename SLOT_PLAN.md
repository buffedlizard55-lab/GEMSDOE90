# SLOT PLAN — R0 SNAP vertical-gradient gate (2026-10-23)

**Agent-selected axis: SNAP.** R0 `h33-h33-2-b2` (37,654 dots; 0.2778 **CLAIM**) and all 26 input hashes reproduced exactly. Three gain-gated variants were BUILT locally, never submitted. `TOP_PUBLIC`, dated target, receipts and quota are unknown. **Default: preserve slots.** Every prediction is below the 0.01 evidence threshold, SGMC PROXY deltas are slightly negative, prior SNAP recipes overlap, and all three inherit R0's 1,611 sub-3 px collar dots. They are **not upload-eligible** unless the human resolves that rule conflict.

## Next three slots — conditional order only, one entity

| Order | Candidate | Moved / mean displacement | Prediction (MODEL, not a score) | What a receipt changes |
|---|---|---:|---|---|
| 1 | `…-SNAPvgmean2g10s2p8-20261023-33bbe8f2.tif` | 8,010 (21.273%) / 0.3853 px | +0.002 DTI; plausible −0.010…+0.010 | Δ≥+0.010 supports gated cross-field re-centring; Δ≤−0.010 closes it. Otherwise no evidence; do not proceed automatically. |
| 2 | `…-SNAPtmivg2g10s2p8-20261023-64011c73.tif` | 13,443 (35.701%) / 0.6330 px | +0.001; same interval | Run only if slot 1 is ≥+0.010 and a magnetic-only decomposition is worth a slot. A loss rejects the magnetic-gain mechanism. |
| 3 | `…-SNAPgravvg2g10s2p8-20261023-332ab617.tif` | 2,999 (7.965%) / 0.1505 px | −0.002; same interval | Reserve, not a routine slot. Only a prior VG gain makes the gravity control informative; Δ≥+0.010 would falsify its negative prediction. |

If the collar conflict is not resolved, **none of these files may be uploaded**. If it is resolved, use at most one candidate per available rolling-week slot and only one encoding; `-zeros.tif` is a fallback twin. Copy the submission-page score and date into the ledger. Any |Δ|<0.010 is no evidence on public chunks and says nothing reliable about private chunks.

## Calendar to supplied deadline (2026-12-03, UNVERIFIED)

- **Oct 23–29:** human resolves collar eligibility and supplies R0 receipt, dated TOP_PUBLIC, quota and official cutoff. Default: no SNAP slot.
- **Oct 30–Nov 19:** conditional slots 1–2 only after the preceding result is ≥+0.010; otherwise preserve slots for a better axis/receipt.
- **Nov 20–Dec 3:** no routine gravity control; confirm the best eligible file and fallback blind, revalidate both, and make only one final submission.

The deadline and 3-per-week rule come from the brief, not a fresh page fetch. Official references for the human: https://www.drivendata.org/competitions/306/competition-doe-gems/ and https://docs.nlr.gov/docs/fy26osti/96647.pdf. Agent did not access DrivenData or submit.

**Restore before any authorized use:** `scripts/restore_data.py`, then `scripts/build_snap_vertical.py --restore`, then `--verify`; match SHA-256 to `ledger/submissions.csv`. Rasters are gitignored because this repository is public.

## Report-only diagnostics and better axes (not built)

Canary AUCs are 0.5087/0.5227; no 0.90 trigger. SGMC PROXY deltas are −0.000021 to −0.000191; hide-and-recover was not run (no fold-clean instrument). Details: `docs/MECHANISM_CARDS_SNAP.md`.

- **KERNEL_BUDGET:** re-space only redundant dots at matched exclusive 300 m credit. *Confounder:* real parallel strands/step-overs. *Falsifier:* paired live Δ≤−0.010.
- **TIP_PRIOR:** fixed-count moves toward known-trace tips/interactions as a structural prior, never vent/heat targeting. *Confounder:* catalogue masking and non-unique interaction geometry. *Falsifier:* no ≥+0.010 gain over an equal-count control.
