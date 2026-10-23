# Mechanism cards — AXIS=SNAP, vertical-gradient gain gate (2026-10-23)

Parent R0 `h33-h33-2-b2`: 37,654 unit dots; 0.2778 is **CLAIM**, not a receipt. All 26 pins and both byte-identical R0 encodings were verified. These three **BUILT, LOCAL-ONLY** files have no live score. Predictions are **MODEL**; SGMC results below are **PROXY**, never scores.

**Shared mechanism.** GeoDAWN Area 2's 400 m line spacing makes 100–200 m misregistration plausible ([USGS GeoDAWN release](https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7)). Each eligible dot may move ≤2 px to its strongest currently admissible response only when the realised gain is ≥0.10 footprint percentile. Gain-descending deterministic assignment reserves unprocessed origins and enforces ≥2.8 px final separation. Count and unit mass are fixed. R0's 1,611 inherited sub-3 px catalogue-collar dots are also fixed; all moved origins/destinations are ≥3 px. Thus no new near-collar mass appears, but the general ≥3 px hard constraint **does not pass** and upload is blocked pending human resolution.

## 1. TMI vertical gradient — `SNAPtmivg2g10s2p8`

- **Hypothesis / mechanism:** `abs(tmi_vg)` enhances shallow magnetic contrasts. A decisive local gain may re-centre misregistered dots without the wholesale movement of earlier SNAP recipes. 13,443 dots moved (35.701%); mean displacement 0.6330 px overall / 1.7729 px among movers.
- **Non-fault mimic:** Dikes, volcanic or lithologic contacts, cultural ferrous sources and gridding noise; a dipping contact's derivative maximum need not coincide with the surface fault.
- **Predicted live change:** **+0.001 DTI MODEL**, plausible −0.010 to +0.010.
- **Falsifier:** Paired live Δ≤−0.010 versus R0; |Δ|<0.010 is no evidence.
- **Overlap limitation:** GEMSDOE86 `vg2` already tested smoothed `|tmi_vg|` with spacing control ([source](https://github.com/buffedlizard55-lab/GEMSDOE86/blob/main/scripts/build_snap_variants.py)); this arm is an incremental unsmoothed, percentile-gain-gated recipe, not a virgin signal.

## 2. Isostatic-gravity vertical gradient — `SNAPgravvg2g10s2p8`

- **Hypothesis / mechanism:** `abs(iso_grav_anom_vg)` tests whether shallow density edges locate a small misregistered subset. Only 2,999 dots moved (7.965%); mean displacement 0.1505 px overall / 1.8892 px among movers.
- **Non-fault mimic:** Basin-fill thickness changes, intrusive/lava margins, density layering and processing artifacts; source depth and dip can displace the crest from a fault.
- **Predicted live change:** **−0.002 DTI MODEL**, plausible −0.010 to +0.010.
- **Falsifier:** Paired live Δ≥+0.010 rejects the predicted negative direction; |Δ|<0.010 is no evidence.

## 3. TMI/gravity vertical-gradient mean — `SNAPvgmean2g10s2p8`

- **Hypothesis / mechanism:** An equal mean of both percentile responses should suppress single-field noise and retain only defensible shallow-contrast relocations. 8,010 dots moved (21.273%); mean displacement 0.3853 px overall / 1.8114 px among movers.
- **Non-fault mimic:** Both fields can express the same basin or lithologic boundary, so their agreement is not independent proof of faulting; correlated gridding and dipping-source offsets remain.
- **Predicted live change:** **+0.002 DTI MODEL**, plausible −0.010 to +0.010.
- **Falsifier:** Paired live Δ≤−0.010 versus R0; |Δ|<0.010 is no evidence.

## Report-only diagnostics

Leakage canary symmetric AUC: gravity VG **0.5087**, TMI VG **0.5227** (60,894 valid catalogue positives; 249,845 seeded valid off-catalogue negatives); neither triggers 0.90. Off-catalogue SGMC control has 62,122 proxy pixels. Parent PROXY 0.0953861; candidate deltas are −0.0001451 (TMI), −0.0001913 (gravity), and −0.0000212 (mean), under the explicit `src/dti.py` assumptions. Catalogue hide-and-recover was not run because R0 used the full catalogue and no fold-clean recovery instrument is validated. None of these diagnostics gates or ranks a live submission.

Full recipe, hashes, parent diffs and disk receipts: `evidence/snap_build_receipt.json`.
