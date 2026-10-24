# SLOT PLAN — agent-selected `AXIS=CONCENTRATION` (2026-10-23e)

**Incumbent R0:** `h33-h33-2-b2`, 37,654 unit-mass dots; rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN), 26/26 SHA-256 pins verified. `0.2778` remains **CLAIM** until a portal receipt is filed. `TOP_PUBLIC`, its date, weekly slots left/used, and the `2026-12-03` deadline are **human-supplied / UNVERIFIED**. One entity: 3 scored submissions per rolling week and one blind final (official rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf; metric/spec: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). Any public-chunk live `|Δ| < 0.010` DTI is **no evidence**. The agent does not submit.

**Why this axis:** R0's 15 km block-density CV is `0.5103`, inside the brief's reported `0.51–0.59` best-file band. A read-only audit of 79 public `buffedlizard55-lab/GEMSDOE*` default branches found 33 occupied `CONCENTRATION` values, none at 15 km with this prior. The prior uses only pinned `training_features.tif` bands `tmi_hg`, `geod_2ndinv`, `geod_shearrate`, `iso_grav_anom_hg` (equal absolute-percentile ranks, averaged per 15 km block); no wells, springs, vents or hidden/public truth. Known catalogue pixels are masked pixel-exactly but adjacent new-fault pixels still score: https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516.

## Built this session (all `MODEL`; fixed count; report-only `PROXY` never gates)

| Value / preferred NaN file (`-zeros` twin available) | Moved / diff | 15 km CV | Predicted Δ | New-dot collar / geography |
|---|---:|---:|---:|---|
| `CONCENTRATIONb15kmstruct10pct-20261023-8deb8269` | 3,765 / 19.998% | 0.5103→0.5990 | **+0.002** (-0.008..+0.012) | 0 added dots <3 px; no donor block ≥90% emptied |
| `CONCENTRATIONb15kmstruct15pct-20261023-fdba3c0a` | 5,648 / 29.999% | 0.5103→0.6949 | **-0.002** (-0.013..+0.009) | same; max donor removal 70.8% |
| `CONCENTRATIONb15kmstruct20pct-20261023-bc411adb` | 7,531 / 40.001% | 0.5103→0.7769 | **-0.006** (-0.018..+0.006) | same; max donor removal 80.0% |

Receipt: `evidence/concentration_build_receipt.json`. Hide/recover `PROXY` (n=13,920, R0 0.007191): Δ +0.000001 / +0.000024 / +0.000011, 95% CIs span zero. SGMC `PROXY` (n=62,122): Δ -0.006381 / -0.009540 / -0.014211 — a physiographic control, not a score. Leakage canary max symmetric AUC **0.574747** (the new prior; <0.90). All six files pass the disk re-read format gate, zero catalogue mass, unique SHA-256. Untouched R0 dots retain the parent's 2.236 px floor (IR90-21); all **added** dots clear ≥3 px.

## Next 3 slots in order (one entity; upload **one** file per slot, NaN primary unless portal rejects it)

| Slot | Candidate | Predicted Δ (`MODEL`) | What the receipt changes |
|---|---|---:|---|
| 1 | `h33-h33-2-b2-MASSshadow20pct-20261023-c4ce118b.tif` (30,123 dots) | +0.009 | Strongest orthogonal count probe. `Δ≥+0.010`: next week test `shadow40` and `random40` to separate dose from ranking. `Δ≤-0.010`: stop thinning, hold 37,654. Null: keep orthogonal slots. Re-emit with `scripts/restore_releases.py` (all 18 pairs); inherits R0 collar (IR90-07). |
| 2 | `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f.tif` (37,654 dots) | +0.004 | Physiographic test. `Δ≥+0.010`: queue `RELIEFr2b10pct`. `Δ≤-0.010`: queue `RELIEFp2r15pct`. Null: hold RELIEF. Restore with `scripts/restore_releases.py`. |
| 3 | `h33-h33-2-b2-CONCENTRATIONb15kmstruct10pct-20261023-8deb8269.tif` (37,654 dots) | +0.002 | Lowest-dose structural-prior probe; CV stays nearest the reported band. `Δ≥+0.010`: queue the 15% arm. `Δ≤-0.010`: reject this prior; pivot to `MASSrandom40pct` control or `PRUNEanisoA4L2`. Null: hold. |

Before any slot: human supplies dated `TOP_PUBLIC`, used/remaining slots, deadline confirmation, and R0 receipt; verifies the chosen SHA-256 was never submitted; confirms data-use terms; restores from pinned inputs (`scripts/restore_data.py`, then `scripts/restore_releases.py`) and re-runs the format gate. Never upload both NaN and zeros twins.

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms)

- **Wk1–2 (Oct 23–Nov 5, ≤6 slots):** slots 1–3 above, then the paired `shadow40`/`random40` control or the winning RELIEF/PRUNE branch. Do **not** spend a slot on FIFO-ranked MASS rungs (IR90-20).
- **Wk3–4 (Nov 6–19, ≤6 slots):** combine only the two axes whose paired receipts clear `Δ≥+0.010`; otherwise spend one slot on the 40% random control and one on collar geometry. Confirm the winner on a fresh re-emission.
- **Wk5–6 (Nov 20–Dec 3, ≤6 slots + 1 blind final):** choose one primary and one encoding fallback; re-run SHA-256, format, zero-catalogue-mass and conflict-marker checks. Private chunks and expert-expanded Phase 2 labels can reverse public signs (https://community.drivendata.org/t/where-do-you-draw-the-line/11536).

## Better axes proposed (not built)

- **PRIOR_MISMATCH_SPREAD:** 10% high→low 15 km prior, count fixed. *Mechanism:* direct sign control on the CV band. *Confounder:* low-prior blocks may be blind basin faults. *Falsifier:* live Δ≤-0.010 against the 10% concentration arm.
- **CONTINUITY_AWARE_DOSE:** same 40% dose, forbid deletions that split ≥1 km strands at 5 px linking. *Confounder:* long dikes/shorelines also link. *Falsifier:* Δ≤-0.010 vs `shadow40`.
- **KERNEL_ORACLE_DOSE:** re-space survivors to ~6 px instead of deleting. *Confounder:* 600 m gaps miss 300 m-offset strands. *Falsifier:* Δ≤-0.010 vs `shadow48`.
- **COLLAR_NOREFILL:** strike-aligned collar with mass allowed to fall. *Confounder:* mass and geometry move together. *Falsifier:* gain no larger than isotropic no-refill controls.

**Evidence labels:** every prediction above is `MODEL`; hide/recover, SGMC and AUC values are `PROXY`/report-only. No agent-generated number is a live score.
