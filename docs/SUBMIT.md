# Human submission packet — GEMSDOE90 MASS shadow-dose ladder

**The agent does not submit.** These local GeoTIFFs are git-ignored so competition rasters stay out of
this public repository and out of any release. One candidate per scored slot; the `-zeros.tif` twin is
a fallback encoding of the *same* experiment, not a second slot.

Session 2026-10-23b · parent `h33-h33-2-b2` · axis MASS · doses are nested (each larger file contains
the previous file's dot set minus more dots).

## Files and form notes

| Candidate | Preferred file (NaN outside footprint) | Fallback twin (zeros outside) | Form note (< 140 chars) |
|---|---|---|---|
| shadow-drop 10 % → 33,889 dots | `releases/h33-h33-2-b2-MASSshadow10pct-20261023-e2e518d5.tif` | `…-e2e518d5-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 10% -> 33889 dots; predicted +0.005 MODEL` |
| shadow-drop 20 % → 30,123 dots | `releases/h33-h33-2-b2-MASSshadow20pct-20261023-c4ce118b.tif` | `…-c4ce118b-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 20% -> 30123 dots; predicted +0.009 MODEL` |
| shadow-drop 30 % → 26,358 dots | `releases/h33-h33-2-b2-MASSshadow30pct-20261023-9d64151a.tif` | `…-9d64151a-zeros.tif` | `h33-h33-2-b2; MASS shadow-drop 30% -> 26358 dots; predicted +0.012 MODEL` |

Also still available, unsubmitted from the earlier session: PRUNE collar 3.5 / 4.5 / 5.5 px
(`-8b96d891`, `-be7a1217`, `-a69816c7`), each count-held at 37,654 dots.

## Validation summary (re-read from disk after writing)

Each file: CRS EPSG:32611, shape and affine transform equal to `sample_submission.tif`, float32,
single band, finite and within [0, 1] inside the footprint, NaN outside (primary) or 0 outside
(`-zeros`), zero catalogue mass, **strict subset of R0** (no additions, no moves), 10.00 / 20.00 /
30.00 % of R0 changed, one SHA per file, no SHA already in the ledger. SHA-256, checks and parent-diff
statistics: `evidence/mass_build_receipt.json`. Re-run with
`.venv/bin/python scripts/build_mass_shadow.py --verify`.

**Known deviation, read before submitting.** Brief §4 asks for ≥ 3 px from the catalogue. R0's own
minimum is 2.236 px (1,611 dots, IR90-01) and these files inherit that collar unchanged, because
changing it would be a second axis; they add no mass whatsoever. If the group prefers a strictly
compliant file, submit a PRUNE candidate instead, or say so and a 3 px-collared version of the same
dose can be built as a separate experiment (do not mix it silently into this ladder).

## What the human must supply

1. R0's own receipt (score + date) — without it the 0.2778 comparison is CLAIM, and a paired Δ is
   not computable.
2. Current `TOP_PUBLIC` with its date, and slots used / remaining for this entity this rolling week.
3. Confirmation of the 2026-12-03 deadline and the 3-submissions-per-rolling-week rule from the
   official page (the agent may not fetch it).
4. A geology look at the *deleted* dot set: `docs/MECHANISM_CARDS.md` explains what to check
   (a deleted dot on an unmapped strand rather than in a neighbour's shadow makes the deletion wrong).
5. Receipt scores + dates copied into `ledger/submissions.csv` (`receipt` = Y). Never submit more than
   the quota; never submit both encodings of one candidate.
