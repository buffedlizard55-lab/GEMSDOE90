# SLOT PLAN — `AXIS=MASS` add rungs (2026-10-23e) and the 3-slot order

**Incumbent R0:** `h33-h33-2-b2` (37,654 unit-mass dots, rebuilt byte-identically; `0.2778` is **CLAIM**).
`TOP_PUBLIC` (with date) and the weekly/total quota used are blank and must be supplied by the human before any
upload. Quota: ONE entity, 3 scored submissions per rolling week, one blind final submission
(https://docs.nlr.gov/docs/fy26osti/96647.pdf; metric/format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
Any public-chunk live `|Δ| < 0.010` DTI is **no evidence**.

**Why this session is MASS/ADD.** Every *valid* MASS row in this ledger is a deletion (shadow 10–48 %, random 40 %);
the add half of the dose curve has never been built validly, because the parent's stored FIFO rank is geographic at
both ends (IR90-20). Addition is also the only allowed edit whose downside is bounded: `T` is a max over dots, so an
added dot can never remove credit — it can only fail to earn its 0.2 mass. Break-even exclusive credit is
`0.2T/(D−0.2T) ≈ 0.056` at the claimed 0.2778; measured marginal support credit per added dot is 0.46 (blocknext) to
1.01 (gapmax). Placement is quota-proportional to the parent's own 5 km block counts, capped at +50 %/block, with zero
quota where R0 has no dots — the region-even repair proposed after IR90-20, not a new geography.

## Next 3 slots in order (one entity; upload the NaN `.tif` only, never both twins)

| Slot | Candidate | Predicted Δ vs R0 (`MODEL`) | Decision rule from the live receipt |
|---|---|---|---|
| 1 | `h33-h33-2-b2-MASSadd10pctGapmax-20261023-98408334.tif` (41,419 dots) | **+0.0107** (+0.0026 … +0.0226) | `Δ >= +0.010`: R0 is under-massed and the kernel has room — adopt ADD, and the deletion ladder was over-applied above d2.8. `−0.010 < Δ < +0.010`: no evidence; Slot 2 becomes `MASSadd10pctBlocknext` (placement contrast). `Δ <= −0.010`: R0 is at/over its mass optimum; abandon ADD and return to the thinning ladder with `MASSshadow20pct`. |
| 2 | `h33-h33-2-b2-MASSadd10pctBlocknext-20261023-89d16c16.tif` (41,419 dots) | **+0.0044** (+0.0003 … +0.0107) | Matched dose and matched geography, worse placement. If Slot 1 ≥ +0.010 and Slot 2 is null, **placement (kernel room) is the whole effect** and every future add must be gap-ranked; if both are ≈ +0.004…+0.011, plain mass addition pays and the ranking is second-order. If Slot 2 ≤ −0.010 while Slot 1 is positive, the FIFO-ranked cells are actively harmful and the brief's "next-ranked" recipe should be abandoned outright. |
| 3 | `h33-h33-2-b2-MASSadd20pctBlocknext-20261023-260d987e.tif` (45,185 dots) | **+0.0084** (+0.0005 … +0.0205) | Dose slope at fixed rule. Upload only if Slot 2 `Δ >= +0.010` (then this measures how far the add gradient runs) **or** if Slot 2 is null and Slot 1 is positive (then this is the cheaper second dose). If Slot 1/2 both null, use the slot on `MASSshadow20pct` to test the opposite sign instead — that pair is the decisive experiment on `dDTI/dS`. |

Do **not** upload any FIFO-order rung (`drop5pct-tail`, `add5pct-next`, `add20pct-next`; WITHDRAWN, IR90-20), the
50 % shadow arm (IR90-17), or both encodings of the same file (they are the same submission twice).

## Calendar to deadline (`2026-12-03` UNVERIFIED — human confirms on the competition page)

- **Weeks 1–2 (Oct 23 – Nov 5, ≤ 6 slots):** R0 receipt if missing, then Slots 1–3. The 10 % pair (gapmax vs
  blocknext) is the whole experiment; the 20 % rung is only worth a slot after the sign is known.
- **Weeks 3–4 (Nov 6 – Nov 19, ≤ 6 slots):** combine the winning sign of `dDTI/dS` with the winning *placement*
  (gapmax-style additions vs shadow-style deletions) on exact parent code; one combination, not a grid.
- **Weeks 5–6 (Nov 20 – Dec 3, ≤ 6 slots + 1 blind final):** confirm the best single edit, choose the blind final file
  and its `-zeros` fallback, re-run `scripts/restore_data.py` + `scripts/build_mass_add_variants.py --verify`, and
  re-validate both formats before upload.

## Session 2026-10-23e result (this branch)

| Variant | Dots | Change | Mean marginal support credit / added dot | Block-density CV 5 km / 10 km, before → after | Predicted (MODEL) |
|---|---|---|---|---|---|
| `…add10pctGapmax-…98408334` | 41,419 | +3,765 (10.0 %) | 1.013 | 0.9011 / 0.6353 → 0.9032 / 0.6361 | +0.0107 (+0.0026 … +0.0226) |
| `…add10pctBlocknext-…89d16c16` | 41,419 | +3,765 (10.0 %) | 0.486 | same | +0.0044 (+0.0003 … +0.0107) |
| `…add20pctBlocknext-…260d987e` | 45,185 | +7,531 (20.0 %) | 0.464 | 0.9011 / 0.6353 → 0.9040 / 0.6373 | +0.0084 (+0.0005 … +0.0205) |

All three: additions `d_cat ≥ 3.0 px` (min exactly 3.0), zero catalogue mass, inherited R0 collar untouched
(IR90-18), per-block addition share p05 0.087 / median 0.100 / p95 0.115 at the 10 % dose, **0 blocks** with zero
additions among the 848 blocks holding ≥ 20 R0 dots, added-centroid within 30 px of the parent's. Report-only SGMC
credit (off-catalogue USGS faults) rises by +39.2 / +73.1 / +53.0 — consistent with the additions landing on
independently mapped structure, and blind to the catalogue by construction (every addition is ≥ 3 px away).

## Report-only diagnostics (`PROXY` / `REPORT ONLY` — never gates, never scores)

- **Catalogue hide-and-recover is structurally blind to this axis:** every added dot is ≥ 3 px from the catalogue
  and the kernel radius is 3 px, so additions contribute exactly zero catalogue credit. Reported as an analytic zero,
  not as a measurement.
- **SGMC control** (off-catalogue USGS map faults, `d_cat > 3 px`): R0 coverage +39.2 / +73.1 / +53.0 credit units for
  the three arms. SGMC over-represents exposed bedrock (65.7 % range-front) and standalone SGMC scored 0.0512 CLAIM.
- **Leakage canary** not re-run: no new feature entered placement (additions sit on the existing H19-5 support). Last
  measured max symmetric AUC 0.5700 over 19 bands.

## Confounds stated, not hidden

- **The support may be saturated in truth, not just in field.** The model's point prediction assumes support precision
  0.20 (implied by `T ≈ 16.6 k` over 121,131 support px); at precision ≤ 0.11 the same algebra makes all three arms
  negative. The bracket spans zero for the two blocknext arms on purpose.
- **Additions cannot be tested against the catalogue.** There is no local instrument that scores added off-collar mass
  against new faults; the only decisive evidence is a live receipt, which is why this axis costs a slot.
- **`MASSadd20pctBlocknext` has the same dot count as the WITHDRAWN `MASSadd20pct-next` (45,185) but is a different
  file** (`260d987e…` vs `63954e89…`): quotas replace the global FIFO order, 0 removed dots, and the added set differs
  in 100 % of cells. Do not treat the two as repeats.
- **No prediction here is a score.** 0.2778 is CLAIM, every Δ is MODEL, SGMC is PROXY.

## Better axes proposed (not built this session)

- **CONCENTRATION — deprioritised, do not build (IR90-22).** Measured on the exact R0 rebuild: mean marginal support
  credit on eligible pixels is 0.543 / 0.543 / 0.543 / 0.557 / 0.646 by block-prior quintile and each dot's own
  exclusive credit is 0.980–0.997 in every quintile, so a fixed-count block reallocation loses ~0.98 and gains ~0.54
  per moved dot at *any* dose. Separately, R0's block-density CV (0.901 at 5 km, 0.635 at 10 km) is already above the
  brief's quoted best-file band 0.51–0.59, so the brief's own diagnostic argues against the brief's direction.
  *Mechanism if ever revived:* truth clusters in belts. *Confounder:* density tracks the H19-5 field, not truth
  (ρ = 0.12 with per-block catalogue density). *Falsifier:* any dose beats the measured −0.4 credit/move bound.
- **MASS_ORACLE_ADD.** Same gapmax operator, but rank candidate cells by *distance to the nearest existing dot*
  instead of kernel credit. *Mechanism:* the kernel is a max, so exclusive credit is almost a pure function of the
  nearest-neighbour distance; this isolates spacing from local ridge geometry. *Confounder:* it will push dots to the
  edges of the support. *Falsifier:* paired Δ ≤ −0.010 vs `MASSadd10pctGapmax`.
- **STRAND_CONTINUITY_REBUDGET** (carried over, still the best structural idea): reallocate R0 dots while preserving
  ≥ 1 km along-strike continuity, because `MASSshadow40pct` keeps 0 of R0's 838 strands. *Confounder:* long unfaulted
  dikes and shorelines form the same corridors. *Falsifier:* paired Δ ≤ −0.010 vs R0.
- **CROSS_STRIKE_RIDGE_SNAP** (carried over): snap dots ≤ 2 px strictly orthogonal to local strike onto high-pass
  magnetic tilt + `det_elev_slope` ridges. *Confounder:* dipping contacts offset magnetic gradients downdip.
  *Falsifier:* paired Δ ≤ −0.010 vs R0. Raw `tmi_hg`/`iso_grav_anom_slope` are unusable for this (IR90-19).
