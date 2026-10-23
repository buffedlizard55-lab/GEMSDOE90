# IRREGULARITIES (decision-changing items only)

1. **Empty repo at session start.** No `registry/data_manifest.json`, no
   `ledger/`, no R0 raster, no `sample_submission.tif`, no catalogue, no
   parent recipe, no metric code (only a one-line README). Per brief §5,
   R0 cannot be rebuilt or hash-matched, so **no variant was built** —
   approximating the parent is forbidden. This session instead ships the
   gated pipeline (`src/`, tests, ledger skeleton) that builds the 3 PRUNE
   variants in one command once the human pins the files in `data/`.
   The agent cannot fetch them: drivendata.org/dropbox.com are barred
   (brief §4.1) and unreachable from the sandbox anyway.
2. **This repository is PUBLIC** (`gh repo view`: isPrivate=false).
   Competition rasters/data must stay out (brief §4.2; data-use terms
   unchecked = UNVERIFIED). Mitigation: `.gitignore` covers `data/` and all
   `*.tif`; `releases/*.tif` will exist only on the human's machine / this
   sandbox disk. Human should make the repo private before adding anything
   data-adjacent (dot CSVs included).
3. **R0's 0.2778 is CLAIM, and its margin over solo-d28 (+0.0070) is below
   the brief's own 0.01 no-evidence threshold** and confounded with mass
   loss. The incumbent's defining edit is therefore unproven — this is why
   the session axis is PRUNE with count-held controls rather than building
   on ≤2 px as settled fact.
4. **Distance definition of "≤2 px" is unrecorded** (Euclidean vs Chebyshev
   vs dilation count). The builder probes Euclidean then Chebyshev and
   hard-stops if neither reproduces R0's dot set exactly from the pre-prune
   dots. If it stops, the recorded recipe is required.
5. **DTI kernel discretisation UNVERIFIED.** `src/dti.py` implements the
   brief's algebra under two stated assumptions (k(d)=max(0,1−d/3);
   T = Σ_g max_p p·k). Official metric code was not supplied and may not be
   fetched; all predictions are MODEL until it is pinned in the manifest.
6. **TOP_PUBLIC, slots remaining, and deadline 2026-12-03 are UNVERIFIED**
   (blank in the brief; agent may not open the competition page). Human
   fills README CURRENT STATE from the leaderboard with a date.
