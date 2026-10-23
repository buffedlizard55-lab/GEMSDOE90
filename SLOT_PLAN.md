# SLOT PLAN — AXIS=RELIEF & Weekly Allocation (2026-10-23)

**Incumbent parent R0:** `h33-h33-2-b2` (37,654 unit-mass dots, rebuilt byte-identically; `0.2778` is **CLAIM** until a submission-page receipt is logged). `TOP_PUBLIC` (with date) and weekly/total quota used are blank and must be supplied by the human before uploading any file. Quota is ONE entity at 3 scored submissions/rolling week and ONE blind final submission per official rules (https://docs.nlr.gov/docs/fy26osti/96647.pdf; problem/metric spec: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). Any live `|Δ| < 0.010` DTI on public chunks is treated as **no evidence**.

**Why AXIS=RELIEF this session.** Partitioning the footprint into equal-area landform relief terciles from `det_elev` (0.85 percentile weight) and 3 km Gaussian-smoothed `det_elev_slope` (0.15 weight) exposes a sharp structural mismatch: R0 allocates **17.2% Basin / 44.8% Piedmont / 37.9% Range-front**, whereas the USGS/INGENIOUS catalogue sits at **28.2% / 42.6% / 29.2%** (known pixels masked pixel-exactly; adjacent new faults scored: https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) and off-catalogue USGS SGMC bedrock faults sit at **9.3% / 24.9% / 65.7%**. Undisclosed test sources (https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527) and 400 m GeoDAWN flight-line positional uncertainty (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7) make physiographic allocation a first-order lever while keeping 100% of dots on `H19-5` and all additions at `d_cat >= 3.0 px`.

## Next 3 slots in order (one entity; upload NaN `.tif` primary only, never both twins)

| Slot | Candidate | Predicted Δ vs R0 (`MODEL`) | Decision rule from live receipt |
|---|---|---|---|
| 1 | `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f.tif` (12.5% = 4,707d Range→Piedmont) | **+0.004 DTI** (-0.010 to +0.015) | `Δ >= +0.010`: adopt down-relief piedmont enrichment; test `r2b10pct` next. `Δ <= -0.010`: reject down-relief; pivot Slot 3 to up-relief `p2r15pct`. `|Δ| < 0.010`: no evidence; move to orthogonal `PRUNE3p5px`. |
| 2 | `h33-h33-2-b2-PRUNE3p5px-20261023-8b96d891.tif` (collar `d_cat<=3.5 px`, fixed count) | **+0.002 DTI** (-0.010 to +0.010) | Orthogonal Week-1/2 collar probe. `Δ >= +0.010`: widen catalogue collar to 3.5 px for Week 3–4 combination; `Δ <= -0.010`: keep R0's `>2 px` collar. |
| 3 | Conditional: `h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17.tif` (10% Range→Basin) **OR** `h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f.tif` (15% Piedmont→Range) | **+0.003** (`r2b10pct`) / **-0.004** (`p2r15pct`) | Upload `r2b10pct` if Slot 1 `Δ >= +0.010` (tests concealed graben basin reach); upload `p2r15pct` only if Slot 1 `Δ <= -0.010` (tests exposed bedrock/range-front label regime); hold slot if both Slot 1 & 2 are `<0.010`. |

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms on competition page)

- **Weeks 1–2 (Oct 23 – Nov 5, max 6 slots):** Confirm R0 live receipt first if absent; run Slots 1–3 above plus single-axis MASS / CONCENTRATION probes from the entity ledger without repeating any `(AXIS, value)`.
- **Weeks 3–4 (Nov 6 – Nov 19, max 6 slots):** Combine the two axes with `Δ >= +0.010` live receipts (e.g., winning `RELIEF` direction × winning `PRUNE` collar or `MASS` trim) on exact parent code; test interaction cleanly.
- **Weeks 5–6 (Nov 20 – Dec 3, max 6 slots + 1 final):** Confirm top composite on fresh paired check, freeze ONE blind final `.tif` (maximizing private-chunk + Phase 2 expert-expanded fault robustness: https://community.drivendata.org/t/where-do-you-draw-the-line/11536) and its `-zeros.tif` fallback, and re-run `scripts/restore_releases.py` + `src/validate.py` before upload.

## Report-only diagnostics (`PROXY` / `REPORT ONLY` — never gates, never scores)

- **Leakage canary:** 19 supplied bands + composite `relief_idx` on 60,988 catalogue positives vs 250,000 seeded (`20261023`) off-catalogue pixels: max symmetric AUC = `0.5700` (`geod_2ndinv`), `relief_idx` = `0.5063` (`< 0.90` pass).
- **Catalogue hide-and-recover (`PROXY`):** 38 withheld 20×20 km blocks (`n = 13,920` positives, 1,000× block bootstrap): R0 `0.0072` (`[0.0058, 0.0088]`); `r2b10pct` `Δ = -0.0003` (`[-0.0005, -0.0001]`), `r2p12p5pct` `Δ = -0.0004` (`[-0.0006, -0.0001]`), `p2r15pct` `Δ = -0.0006` (`[-0.0009, -0.0004]`) — attenuated by R0's `>2 px` and additions' `>=3 px` collar.
- **SGMC off-catalogue control (`PROXY`):** 162 blocks (`n = 62,122` pixels, `d_cat > 3 px`): R0 `0.0954`; `p2r15pct` `Δ = -0.0033` (`[-0.0052, -0.0015]`) > `r2b10pct` `Δ = -0.0091` (`[-0.0111, -0.0070]`) > `r2p12p5pct` `Δ = -0.0108` (`[-0.0133, -0.0084]`), reflecting SGMC's 65.7% bedrock-range bias.

## Better axes proposed (do not build this session)

- **CROSS_STRIKE_RIDGE_SNAP:** Snap R0 dots `<=2 px` strictly orthogonal to local `H19-5` strike onto zero-crossings / maxima of high-pass magnetic tilt (`tc`) + `det_elev_slope` (raw `tmi_hg`/`iso_grav_anom_slope` window-max pulls 84–86% of dots off `H19-5` due to multi-km potential-field wavelength). *Confounder:* dipping lithologic contacts shift magnetic gradients downdip from surface fault traces. *Falsifier:* paired live `Δ <= -0.010` vs R0.
- **STRAND_CONTINUITY_REBUDGET:** Reallocate mass at fixed count from short (`<500 m`) isolated `H19-5` fragments into `>=1.5 km` strike-persistent corridors using `2.8 px`-spaced extensions from ancestor `H19-4` ridges rather than submodular `1.4 px` infill. *Confounder:* long unfaulted dikes, hogbacks, or pluvial shorelines also form multi-km corridors. *Falsifier:* paired live `Δ <= -0.010` vs R0.
