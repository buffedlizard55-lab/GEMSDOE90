# SLOT PLAN — Integrated Weekly Allocation & `AXIS=RELIEF` (2026-10-23)

**Incumbent R0:** `h33-h33-2-b2` (37,654 unit-mass dots, rebuilt byte-identically; `0.2778` is **CLAIM** until a portal receipt is logged). `TOP_PUBLIC` (with date) and weekly/total quota used are blank and must be supplied by the human before any upload. Quota is ONE entity at 3 scored submissions/rolling week and ONE blind final submission per official rules (https://docs.nlr.gov/docs/fy26osti/96647.pdf; problem/metric spec: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). Any public-chunk live `|Δ| < 0.010` DTI is **no evidence**.

**Why `AXIS=RELIEF` (session 2026-10-23d).** Equal-area landform relief terciles (`0.85·pct(det_elev) + 0.15·pct(gaussian_3km(det_elev_slope))`) show R0 allocates **17.2% Basin / 44.8% Piedmont / 37.9% Range-front**, whereas the USGS/INGENIOUS catalogue sits at **28.2% / 42.6% / 29.2%** (known pixels masked pixel-exactly; adjacent new faults scored: https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516) and off-catalogue USGS SGMC bedrock faults sit at **9.3% / 24.9% / 65.7%**. Undisclosed test sources (https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527) and 400 m GeoDAWN line spacing (https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7) make physiographic allocation an orthogonal single-axis lever alongside `MASS` and `PRUNE`, holding count at 37,654 on `H19-5` with `d_cat >= 3.0 px` on 100% of additions.

## Next 3 slots in order (one entity; upload NaN `.tif` primary only, never both twins)

| Slot | Candidate | Predicted Δ vs R0 (`MODEL`) | Decision rule from live receipt |
|---|---|---|---|
| 1 | `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f.tif` (12.5% = 4,707d Range→Piedmont) | **+0.004 DTI** (-0.010 to +0.015) | `Δ >= +0.010`: adopt down-relief enrichment; queue `RELIEFr2b10pct` in Slot 3. `Δ <= -0.010`: reject down-relief; pivot Slot 3 to up-relief `RELIEFp2r15pct`. `|Δ| < 0.010`: no evidence; hold RELIEF and test orthogonal axes. |
| 2 | `h33-h33-2-b2-MASSshadow20pct-20261023-c4ce118b.tif` (20% shadow drop → 30,123d; or `PRUNEanisoA4L2` if testing collar first) | **+0.009 DTI** (+0.004 to +0.041) | Orthogonal count probe. `Δ >= +0.010`: probe `MASSshadow40pct` vs `MASSrandom40pct` control next week; `Δ <= -0.010`: keep fixed count 37,654 and test `PRUNEanisoA4L2` (`0bf248e2`). |
| 3 | Conditional: `h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17.tif` (10% Range→Basin) **OR** `h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f.tif` (15% Piedmont→Range) | **+0.003** (`r2b10pct`) / **-0.004** (`p2r15pct`) | Upload `r2b10pct` if Slot 1 `Δ >= +0.010` (tests axial-basin graben reach); upload `p2r15pct` if Slot 1 `Δ <= -0.010` (tests exposed bedrock label regime); else test `PRUNEanisoA4L2` (`+0.003 MODEL`) so all 3 slots test distinct axes. |

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms on competition page)

- **Weeks 1–2 (Oct 23 – Nov 5, max 6 slots):** Confirm R0 live receipt first if missing; run Slots 1–3 above, then remaining orthogonal single-axis checks (`MASSshadow40pct` vs `MASSrandom40pct`, `PRUNEanisoA4L2` vs `PRUNE3p5px`) without repeating any `(AXIS, value)`.
- **Weeks 3–4 (Nov 6 – Nov 19, max 6 slots):** Combine the two axes whose live receipts cleared `Δ >= +0.010` (e.g., winning `RELIEF` tercile shift × winning `MASS` thinning or `PRUNE` collar) on exact parent code.
- **Weeks 5–6 (Nov 20 – Dec 3, max 6 slots + 1 blind final):** Confirm top composite, select ONE blind final `.tif` (accounting for private chunks + Phase 2 expert-expanded faults: https://community.drivendata.org/t/where-do-you-draw-the-line/11536) and its `-zeros.tif` fallback, and re-run `scripts/restore_releases.py` + `src/validate.py` before upload.

## Report-only diagnostics (`PROXY` / `REPORT ONLY` — never gates, never scores)

- **Leakage canary:** 19 supplied bands + `relief_idx` on 60,988 catalogue positives vs 250,000 seeded (`20261023`) off-catalogue pixels: max symmetric AUC = `0.5700` (`geod_2ndinv`), `relief_idx` = `0.5063` (`< 0.90` pass).
- **Catalogue hide-and-recover & SGMC controls (`PROXY`, `evidence/relief_build_receipt.json`):** 38 withheld 20×20 km catalogue blocks (`n = 13,920`, R0 `0.0072`): `r2b10pct` `Δ = -0.0003`, `r2p12p5pct` `Δ = -0.0004`, `p2r15pct` `Δ = -0.0006` (`>=3 px` additions earn zero catalogue credit). Off-catalogue SGMC (`n = 62,122`, R0 `0.0954`): `p2r15pct` `Δ = -0.0033` > `r2b10pct` `Δ = -0.0091` > `r2p12p5pct` `Δ = -0.0108` (reflecting SGMC's 65.7% bedrock-range bias).

## Better axes proposed (do not build this session)

- **CROSS_STRIKE_RIDGE_SNAP:** Snap R0 dots `<=2 px` strictly orthogonal to local `H19-5` strike onto high-pass magnetic tilt (`tc`) + `det_elev_slope` ridges (raw `tmi_hg`/`iso_grav_anom_slope` window-max pulls 84–86% of dots off `H19-5` due to multi-km wavelength). *Confounder:* dipping lithologic contacts offset magnetic gradients downdip from surface fault traces. *Falsifier:* paired live `Δ <= -0.010` vs R0.
- **STRAND_CONTINUITY_REBUDGET:** Reallocate or thin R0 dots while preserving `>=1 km` along-strike strand continuity (addressing `MASSshadow40pct` dropping all 838 `>=1 km` strands) by replacing short `<500 m` `H19-5` fragments with `2.8 px`-spaced extensions on multi-km corridors. *Confounder:* long unfaulted dikes, hogbacks, or pluvial shorelines also form multi-km corridors. *Falsifier:* paired live `Δ <= -0.010` vs R0 (or `<= -0.005` vs matched-count `MASSrandom`).
