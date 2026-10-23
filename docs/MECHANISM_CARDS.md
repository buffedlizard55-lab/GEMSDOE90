# Mechanism cards — AXIS=PRUNE (session 2026-10-23, GEMSDOE90)

Status: **NOT BUILT** — blocked on pinned inputs (see IRREGULARITIES.md #1).
Predictions are MODEL. Live changes < 0.01 are no evidence (brief §5).

Why PRUNE: R0's defining edit (solo-d28 0.2708 → prune ≤2 px 0.2778, both
CLAIM) gained +0.0070 — below the 0.01 no-evidence bar — and is confounded
with mass loss (dots were removed; count was not held, per the brief's climb
description). PRUNE is also the only axis executable without undisclosed
bands/recipes: MASS needs the parent field's ranking, SNAP needs gradient
bands, CONCENTRATION/RELIEF need prior/relief rasters — none supplied. A
count-held ≤1 / ≤2 / ≤3 dose–response from the common pre-prune parent is the
cheapest experiment that can falsify the incumbent's own last step.

Shared mechanism: dots within ~200 m of a mapped trace spend most of their
300 m triangular kernel on ground whose fault pixels are already captured by
USGS/INGENIOUS (masked pixel-exactly; scored only against *new*-fault truth).
A unit dot pays iff its marginal credit beats ~0.2·DTI ≈ 0.056 (brief §2;
exact recomputation in `src/dti.py`, UNVERIFIED vs official code). The
non-fault mimic: the parent field was trained/tuned against the catalogue, so
it concentrates mass near known faults because range fronts, lithologic
contacts and lineament-friendly terrain correlate with *known*-fault
environments — not because unmapped fault pixels lie beside every trace.

## V1 — prune ≤3 px + refill to 37,654 (slot 1)
- Hypothesis: the 2–3 px ring is still mostly kernel wasted on captured
  geometry; the highest-ranked far dots earn more credit on genuinely new
  traces (parallel strands, step-overs, extensions beyond mapped tips).
- Mimic / risk: "new fault" includes newly mapped geometry of existing
  systems, and truth can lie within 300 m of known traces — the 3 px ring is
  exactly where re-mapped geometry would sit, so V1 could delete true credit.
- Predicted live change (MODEL): +0.000 to +0.010. Small because the ring is
  a minor share of 37,654 dots and refill dots are by construction marginal.
- Falsifier: V1 ≤ R0 − 0.01 ⇒ near-catalogue mass was earning real credit;
  abandon outward prune, test V2 direction instead.

## V2 — prune ≤1 px, count held by dropping lowest-ranked (slot 2)
- Hypothesis: the dist-2 ring R0 deleted contains re-mappable geometry
  (fault-zone width, splays, 400 m GeoDAWN line-spacing positional error ≈
  kernel radius) worth more than the parent field's lowest-ranked far dots.
- Mimic / risk: dist-2 dots may merely be catalogue-proximity bias of the
  field (see shared mechanism); restoring them re-imports that bias.
- Predicted live change (MODEL): −0.005 to +0.005; the value of V2 is the
  *sign of the slope* across ≤1/≤2/≤3, not its own score.
- Falsifier: V2 ≥ R0 + 0.01 ⇒ R0's prune was harmful and its +0.007 CLAIM was
  mass/noise; V2 ≤ R0 − 0.01 with V1 ≥ R0 confirms monotone outward benefit.

## V3 — prune ≤3 px, NO refill (control; build, submit only if V1 ambiguous)
- Hypothesis: if V1 ≈ V3, refill dots earn ~nothing and any V1 gain is pure
  mass reduction (a MASS effect wearing PRUNE clothes) — redirect next
  session to MASS −10% by parent ranking.
- Predicted live change (MODEL): −0.005 to +0.005 vs R0.
- Falsifier: V3 ≫ V1 ⇒ the ranking's tail is actively harmful (credit <
  break-even); V1 ≫ V3 ⇒ refill quality is real and the ranking has signal
  beyond the current 37,654 — supports a future MASS +10% test.
