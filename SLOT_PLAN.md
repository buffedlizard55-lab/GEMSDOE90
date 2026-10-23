# SLOT PLAN — ONE entity, 3 scored slots/week + 1 final blind (deadline 2026-12-03)

**Current session AXIS: CONCENTRATION** (picked by agent; human assigns next). 3 variants built: CONC 2000M10PCT, 1000M15PCT, 5000M20PCT. All share parent h33-h33-2-b2, 37654 dots, 10-20% moved, validated.

## Next 3 slots in order (wk1-2 default: MASS, CONCENTRATION, SNAP, PRUNE, RELIEF)

### Slot 1 (Week 1, Day 1-2): MASS — test dot count / ranking threshold
**Build:** `h33-h33-2-b2-MASS-M10` drop lowest-ranked 10% (33888 dots) and `MASS-P10` add next-ranked 10% (41419 dots) by parent's own ranking (rebuild from `data/ranking.npy` + `score_field.tif`). Keep buffer 2px. Report S, T, DTI proxy delta per added dot; exact % changed = 10.0.
**Mechanism:** More mass pays only if marginal credit >0.2*DTI (~0.056 at 0.28); line-like truth lowers bar — fewer dots may reduce false-positive penalty in S-M term. Non-fault mimicker: lithologic contacts that score high but are not fault pixels cause mass to hurt.
**Falsifier:** If both -10% and +10% lower live score by >0.01 vs parent 0.2778, mass hypothesis rejected; move to spacing.
**What result would change:** Confirms whether best-files' 37-44k cluster (0.7-0.85% footprint) is causal or confounded with field quality; informs final mass target.

### Slot 2 (Week 1, Day 3-4): CONCENTRATION follow-up — now live data
**Build:** Hold 2000M10PCT (smallest CV jump +0.79) vs 5000M20PCT (largest CV jump +2.25). If CONC10 beats CONC20 by >0.01 live, build `CONC 2000M 7PCT` (finer) else `CONC 5000M 12PCT` (moderate). Same axis, new (axis,value) pair not repeated per brief §5.
**Mechanism:** Step-over / intersection prior (Faulds inventory) clusters geothermal systems at block-scale interactions; block-density CV 0.51-0.59 for best files suggests moderate heterogeneity is optimal. Mimicker: basin fill edges produce similar block prior without faulting.
**Falsifier:** If CV vs live Δ correlation |r|<0.2 after 2 points, concentration provides no gain.
**What result would change:** Decides whether expert-expanded private labels (Phase 1+2) favor interaction zones vs uniform coverage; determines if final file should be concentrated.

### Slot 3 (Week 2, Day 1): PRUNE — buffer sensitivity
**Build:** `PRUNE-1px` (refill from >=3px eligible), `PRUNE-3px` (remove <=3px, refill) at matched count 37654. Same count, diff buffer only. Report dots removed per buffer and refill distance.
**Mechanism:** Organizer masked known traces pixel-exactly; pixels beside are scored normally but may be down-weighted by proximity penalty in private chunks. Testing 1 vs 3px tells if 2px (R0) is too loose/tight.
**Falsifier:** If PRUNE-3px drops live >0.01 vs parent, current 2px is near-optimal.
**What result would change:** Final file buffer choice; if 3px wins, rebuild all future variants with 3px.

## Weeks to deadline (6 weeks left as of 2026-10-23 → 2026-12-03)
- **Wk3-4 (2026-11-02 — 2026-11-15): Combine two best axes.** Example: MASS-best + CONC-best (e.g., 33888 dots re-concentrated at 2000m). Test interaction: does mass reduction + concentration stack? Build at most 2 combos, each new (axis,value) unique. If one beats parent+0.01, promote to candidate final.
- **Wk5-6 (2026-11-16 — 2026-11-29): Confirm, choose final + fallback, re-validate.** Hold 3 submission slots: 1) candidate final (e.g., parent-CONC-MASS combo) with NaN outside + zeros fallback; 2) second-best as immediate confirm if live dips (public chunks only); 3) reserve for unexpected Phase-2 trackB trace (strike-consistent >=1km GeoJSON + evidence paragraph) — not a weekly slot unless human decides per brief §5. Re-run `src/validate.py` on both files, re-read from disk, check sha256 not in ledger, git SHA pinned.
- **Final blind (by 2026-12-03):** One final upload, blind. Default: best live file unless proxy-leakage concern (AUC>0.90) suggests overfit — then fallback to more conservative (parent).

**Rules:** 3 scored/week/entity, one final, reproducible code, AI disclosure (AI_USE.md). Never scrape leaderboard or submit via code; human submits from registered account.

**Proposed better axes (not built this session):**
- **TRACK-CONTINUITY:** Build strike-consistent traces >=1km from top-ranked dots (Hough / tensor voting) vs Poisson-disk isotropy — tests if expert labels are mapped as continuous faults vs dots. Confounder: lidar scarps mimic continuity. Falsifier: trace file scores worse than dot-equivalent at same count.
- **RELIEF-SNAP hybrid:** Move dots only along range-front tercile (detrended elevation) to strongest TMI gradient within 2px — tests basin/range interaction prior with scarp snapping. Confounder: anthropogenic lineaments (roads) mimic scarps.
