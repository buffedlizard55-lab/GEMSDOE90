# Mechanism Cards — GEMSDOE90 (`AXIS=RELIEF` & retained `AXIS=PRUNE`)

Parent R0 (`h33-h33-2-b2`, 37,654 unit-mass dots) was rebuilt byte-identically (`c55bafc4…` zeros / `baeae321…` NaN; `evidence/r0_rebuild_receipt.json`). R0's `0.2778` live figure remains **CLAIM** until a submission-page receipt is logged. All predictions below are **MODEL** (never scores), and any public-chunk live change with `|Δ| < 0.010` DTI is treated as **no evidence**.

## Active session: `AXIS=RELIEF` (2026-10-23, `evidence/relief_build_receipt.json`)

**Shared geological & metric design (written for a structural geologist):**
- **Landform relief index:** Equal-area terciles over the 5,167,373-pixel footprint (`~1,722,458` px each) from `det_elev` (Band 12, 0.85 percentile weight) and 3.0 km Gaussian-smoothed `det_elev_slope` (Band 19, 0.15 percentile weight). Smoothing `det_elev_slope` at landform scale (`sigma = 30 px = 3 km`) prevents 100 m intrabasin fault scarps on flat valley floors from being misclassified out of the Basin tercile.
- **Physiographic baseline:** R0 allocates **17.25% Basin (T1) / 44.81% Piedmont (T2) / 37.95% Range-front & Range (T3)**, compared with **28.23% / 42.58% / 29.19%** on the known USGS/INGENIOUS Quaternary/geothermal fault catalogue and **9.33% / 24.94% / 65.73%** on off-catalogue USGS SGMC bedrock geologic-map faults.
- **Within-tercile operator:** Count is fixed at **37,654 unit-mass dots**, and 100% of dots remain on the off-catalogue `H19-5` corroborated ridge network (`h19_5 & footprint & ~catalogue`). Donor dots are removed greedily in ascending order of exclusive `R = 3 px` triangular-kernel loss on `H19-5`, and recipient dots (`d_cat >= 3.0 px` strictly) are added greedily in descending order of incremental `R = 3 px` kernel gain—matching exact DTI marginal ordering (`src/dti.py`) for unit-mass on-support dots while eliminating row-scan North–South bias (`north_half_share` stays `0.722–0.740` vs R0's `0.733`).

### 1. `h33-h33-2-b2-RELIEFr2p12p5pct-20261023-5e64d01f` (Shift 12.5% = 4,707 dots: Range-front T3 → Piedmont T2)
- **Hypothesis:** Shifting 12.5% of R0 mass out of uplifted horst/range interiors (`T3`: `37.95% -> 25.44%`) into piedmont/bajada aprons (`T2`: `44.81% -> 57.31%`) trims false-positive bedrock erosional ridges while densifying coverage across range-bounding synthetic splays, relay ramps, and accommodation step-overs without gambling mass on deep playa fill.
- **Mechanism:** Removes the 4,707 lowest-exclusive-credit `T3` dots and adds the 4,707 highest-marginal-credit `T2` `H19-5` pixels (`d_cat >= 3.0 px`; `25.001%` symmetric diff). Because GeoDAWN Area 2 was flown at 400 m line spacing (`~150–300 m` lateral lineament uncertainty: https://data.usgs.gov/datacatalog/data/USGS:657e1d85d34e23d3533209f7), tighter `H19-5` sampling in `T2` increases lateral kernel reach across piedmont fault corridors.
- **Non-fault process that could mimic it:** Incised alluvial-fan feeder channels, terrace risers, Pleistocene Lake Lahontan highstand beach ridges, and linear piedmont infrastructure (roads/pipelines) can generate corroborated `H19-5` lineaments in `T2`.
- **Predicted live change (`MODEL`):** **+0.004 DTI** (plausible interval `-0.010` to `+0.015`; not a score).
- **Falsifier:** A paired live receipt against R0 with `Δ <= -0.010` DTI rejects down-relief piedmont enrichment at fixed count and triggers switching to the up-relief counterpoint (`p2r15pct`). `|Δ| < 0.010` is no evidence.

### 2. `h33-h33-2-b2-RELIEFr2b10pct-20261023-9e7b5e17` (Shift 10.0% = 3,766 dots: Range-front T3 → Basin T1)
- **Hypothesis:** Shifting 10.0% of R0 mass from `T3` (`37.95% -> 27.94%`) into `T1` (`17.25% -> 27.25%`) removes `H19-5`'s bedrock-topography bias and aligns R0's physiographic allocation (`27.3% / 44.8% / 27.9%`) within 1 percentage point of the Great Basin USGS/INGENIOUS Quaternary fault prior (`28.2% / 42.6% / 29.2%`).
- **Mechanism:** Concealed intrabasin normal faults and blind geothermal step-overs beneath Plio-Quaternary valley fill lack steep surface scarps and rely on aeromagnetic/gravity gradients. Reallocating 3,766 unit dots (`20.003%` symmetric diff) from crowded/short `T3` bedrock segments to uncovered `T1` `H19-5` kernel gaps (`d_cat >= 3.0 px`) raises kernel credit on buried axial-graben faults at fixed total mass.
- **Non-fault process that could mimic it:** Pluvial shoreline berms (Lake Lahontan), axial river/playa margins, shallow intrabasin basaltic sills/flows, and valley-axis rail/powerline magnetic artifacts mimic concealed intrabasin faults in `T1`.
- **Predicted live change (`MODEL`):** **+0.003 DTI** (plausible interval `-0.012` to `+0.015`; not a score).
- **Falsifier:** Paired live `Δ <= -0.010` DTI vs R0 falsifies concealed-basin enrichment. `|Δ| < 0.010` is no evidence.

### 3. `h33-h33-2-b2-RELIEFp2r15pct-20261023-ad95e30f` (Shift 15.0% = 5,648 dots: Piedmont T2 → Range-front T3)
- **Hypothesis:** Bidirectional structural counterpoint: if undisclosed organizer "new fault" labels (https://community.drivendata.org/t/how-were-the-new-test-faults-identified-data-sources-and-fault-types/11527) derive mainly from newly compiled bedrock quadrangles and steep range-front scarps (like off-catalogue SGMC, which sits 65.7% in `T3`), shifting 15.0% of R0 mass up-relief (`T2`: `44.81% -> 29.81%`; `T3`: `37.95% -> 52.95%`) will raise live DTI; under our primary concealed-Quaternary GeoDAWN hypothesis, it is predicted slightly negative (`-0.004 MODEL`).
- **Mechanism:** Greedily moves 5,648 unit dots (`29.999%` symmetric diff) from `T2` to `T3` on `H19-5` (`d_cat >= 3.0 px` on all additions), holding total count at 37,654.
- **Non-fault process that could mimic it:** Unfaulted volcanic/intrusive contacts, dikes, cooling joints, resistant stratigraphic hogbacks, and steep erosional drainage divides in uplifted horsts mimic bedrock fault lineaments in `T3`.
- **Predicted live change (`MODEL`):** **-0.004 DTI** (plausible interval `-0.015` to `+0.012`; not a score).
- **Falsifier:** Uploaded only if down-relief (`r2p12p5pct` or `r2b10pct`) yields `Δ <= -0.010`; if `p2r15pct` also yields `Δ <= -0.010`, monotonic relief reallocation is falsified in both directions.

---

## Retained prior session summary: `AXIS=PRUNE` (`evidence/build_receipt.json`)

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted Δ (`MODEL`) | Falsifier |
|---|---|---|---|---|
| `PRUNE3p5px` (`8b96d891`) | Widen catalogue collar to `>3.5 px` (2,702 removed/refilled from `H19-5` FIFO-BFS order) to cut near-trace false-positive mass. | New fault splays within 350 m of known traces; non-fault `H19-5` refill ridges. | `+0.002 DTI` (`-0.010`..`+0.010`) | Paired live `Δ <= -0.010` |
| `PRUNE4p5px` (`be7a1217`) | Widen collar to `>4.5 px` (4,848 removed/refilled). | Deletes true adjacent fault extensions within 450 m. | `+0.000 DTI` (`-0.010`..`+0.010`) | Paired live `Δ <= -0.010` |
| `PRUNE5p5px` (`a69816c7`) | Wide 550 m halo counterpoint (6,130 removed/refilled). | Broad pruning strips real step-over/splay geometry. | `-0.003 DTI` (`-0.010`..`+0.010`) | Paired live `Δ >= +0.010` flips sign |
