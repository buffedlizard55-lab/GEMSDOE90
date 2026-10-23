# Mechanism cards

## Session 2026-10-23 (2): AXIS = PRUNE, value family = strike-aligned (anisotropic) collar

Parent R0 `h33-h33-2-b2`: 37,654 unit-mass dots, isotropic >2 px catalogue collar; 0.2778 is a **CLAIM**
(no submission-page receipt). These three files are **BUILT**, format-gated and unscored. Their predictions are
**MODEL**. Files live in ignored `releases/`; hashes and full statistics are in `evidence/build_aniso_receipt.json`.

Shared hypothesis, written for a structural geologist: the parent's collar treats positional error as
direction-free, but the two directions do different work. Across strike, a dot 2–3 px from a mapped trace is
usually flank mass: the known pixels there are masked anyway, so it earns penalty without new credit. Along
strike, a dot near a mapped trace is plausibly the continuation of that system — geometry the organiser says is
still scored as "new". A collar that widens only across strike should therefore buy the precision gain of a
3 px uniform collar while keeping the along-strike credit a uniform 3 px collar would throw away.

Mechanism: local strike from a structure tensor of the catalogue mask (major eigenvector = across strike, since a
thin trace's gradients run across it); each dot is projected onto that frame at its nearest catalogue pixel and
removed if `(along/2)² + (across/A)² ≤ 1`. Where the tensor is incoherent (< 0.3), no along-strike exemption is
granted and the collar falls back to isotropic A. The count is held at 37,654 by refilling from the pinned
H19-5 support in the lineage's recovered FIFO-BFS thinning order, outside the collar.

| Variant | Removed / refilled | % of R0 changed | Along-strike dots kept that an isotropic collar of the same radius deletes | Predicted live change (MODEL) | Non-fault confounder | Falsifier |
|---|---|---|---|---|---|---|
| A4 (`…0bf248e2`) | 2,632 | 13.98 % | 1,193 | **+0.003** (−0.010 to +0.010) | A parallel strand or a step-over a few pixels across strike from a mapped trace is a real fault, not flank noise; steeply dipping strands surface offset from their mapped trace. | Paired same-week Δ ≤ −0.010 rejects the across-strike-only collar at this dose; \|Δ\| < 0.010 is no evidence. |
| A5 (`…15218061`) | 3,663 | 19.46 % | 1,974 | **+0.002** (−0.010 to +0.010) | Same, plus: the refill pool shrinks and its replacement pixels get worse as the collar widens. | As above; a monotone decline over A4→A6 rejects the dose-response the mechanism implies. |
| A6 (`…72dcdbd3`) | 4,625 | 24.57 % | 2,176 | **+0.000** (−0.010 to +0.010) | Same; a 600 m across-strike halo is beyond survey positional error, so genuine adjacent truth starts to be deleted. | Paired same-week Δ ≥ +0.010 would falsify the predicted flattening and support a still wider collar. |

Prediction decomposition (why the numbers are small and nearly flat): positive collar term scales with removed
dots (+0.004…+0.008), negative refill term scales with refills (−0.001…−0.005). The refill is the weak link:
98.7–99.5 % of refill dots land within 3 px of a retained dot (median 1.00 px), i.e. they mostly add the
0.2·(S−M) penalty and very little fresh kernel credit, and the replacement is non-local (median 845–888 px from
the dot it replaces). This dilution is inherited from the parent lineage's refill policy and is **not** part of
the collar geometry under test — see `IRREGULARITIES.md` #IR90-07. Removed dots sit at median 2.8–3.2 px across
strike and 0.5 px along strike, so the edit is a genuine flank edit.

Report-only diagnostics: leakage canary max symmetric AUC 0.5695 over 19 supplied bands (60,988 catalogue
positives + 250,000 seeded off-catalogue pixels) — no single feature above 0.90. Catalogue hide-and-recover and
SGMC control were not run; no fold-clean instrument is calibrated for a collar geometry, and none of these
numbers rank a file.

---

## Session 2026-10-23 (1): AXIS = PRUNE, isotropic collar rungs 3.5 / 4.5 / 5.5 px

Parent R0: `h33-h33-2-b2`, 37,654 unit-mass dots. It was rebuilt byte-identically from the pinned h27-4 solo-d2.8 parent; `evidence/r0_rebuild_receipt.json` records the proof. R0's 0.2778 remains **CLAIM**, not a receipt. These local candidates are **BUILT**, not submitted; predictions are **MODEL**, not scores. Their rasters are local under ignored `releases/` and are not part of this public PR.

Shared hypothesis: the incumbent's >2 px catalogue collar may be too narrow. Known pixels are masked pixel-exactly, yet new-fault truth may lie adjacent to known traces; a broader collar can remove true new-fault credit as well as false-positive mass. Each variant removes parent dots at or inside a larger Euclidean-distance threshold, then refills to exactly 37,654 from the H19-5 support outside the threshold. Refill priority is the deterministically rebuilt FIFO-BFS visitation order used by the original 2.8 px thinning recipe. It is an algorithmic tie-break, **not** a geological probability.

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| PRUNE 3.5 px | Extending the collar just beyond the 300 m kernel radius will remove redundant near-catalogue mass while retaining most of the incumbent's high-priority ridge set. 2,702 dots removed and 2,702 refilled. | New mapped fault splays, parallel strands, or geometry extensions can occur within 350 m of known traces; replacement H19-5 lineaments may be contacts or drainage margins. | +0.002 DTI; plausible interval -0.010 to +0.010. | Same-week paired live Δ≤-0.010 falsifies the positive collar hypothesis at this dose; |Δ|<0.010 is no evidence. |
| PRUNE 4.5 px | A wider uncertainty halo may further reduce false-positive mass, but now sacrifices more near-catalogue truth and more incumbent-priority pixels. 4,848 dots removed/refilled. | Same as above; broadened collar more likely to delete newly mapped faults close to the catalogue. | +0.000 DTI; plausible interval -0.010 to +0.010. | Paired live Δ≤-0.010 rejects this wider collar/refill policy; |Δ|<0.010 is no evidence. |
| PRUNE 5.5 px | A 550 m halo is likely beyond useful positional uncertainty, so lost adjacent new-fault credit may exceed any false-positive savings. 6,130 dots removed/refilled. | Mapped fault geometry may be displaced from its true trace by survey resolution; very broad pruning can remove legitimate nearby new geometry. | -0.003 DTI; plausible interval -0.010 to +0.010. | Paired live Δ≥+0.010 falsifies the predicted negative direction; |Δ|<0.010 is no evidence. |

The DTI algebra in `tests/test_metric_algebra.py` is unit-tested against synthetic component values. The official competition metric code was not accessed; no candidate was scored on labels or submitted. A local feature leakage canary is report-only; catalogue hide-and-recover and SGMC instruments were not used to rank candidates. Full inputs, exact hashes, parent differences and format receipts are in `evidence/build_receipt.json`.
