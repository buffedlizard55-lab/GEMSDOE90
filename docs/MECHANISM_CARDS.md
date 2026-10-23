# Mechanism cards — AXIS=PRUNE (2026-10-23)

Parent R0: `h33-h33-2-b2`, 37,654 unit-mass dots. It was rebuilt byte-identically from the pinned h27-4 solo-d2.8 parent; `evidence/r0_rebuild_receipt.json` records the proof. R0's 0.2778 remains **CLAIM**, not a receipt. These local candidates are **BUILT**, not submitted; predictions are **MODEL**, not scores. Their rasters are local under ignored `releases/` and are not part of this public PR.

Shared hypothesis: the incumbent's >2 px catalogue collar may be too narrow. Known pixels are masked pixel-exactly, yet new-fault truth may lie adjacent to known traces; a broader collar can remove true new-fault credit as well as false-positive mass. Each variant removes parent dots at or inside a larger Euclidean-distance threshold, then refills to exactly 37,654 from the H19-5 support outside the threshold. Refill priority is the deterministically rebuilt FIFO-BFS visitation order used by the original 2.8 px thinning recipe. It is an algorithmic tie-break, **not** a geological probability.

| Candidate | Hypothesis / mechanism | Non-fault confounder | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| PRUNE 3.5 px | Extending the collar just beyond the 300 m kernel radius will remove redundant near-catalogue mass while retaining most of the incumbent's high-priority ridge set. 2,702 dots removed and 2,702 refilled. | New mapped fault splays, parallel strands, or geometry extensions can occur within 350 m of known traces; replacement H19-5 lineaments may be contacts or drainage margins. | +0.002 DTI; plausible interval -0.010 to +0.010. | Same-week paired live Δ≤-0.010 falsifies the positive collar hypothesis at this dose; |Δ|<0.010 is no evidence. |
| PRUNE 4.5 px | A wider uncertainty halo may further reduce false-positive mass, but now sacrifices more near-catalogue truth and more incumbent-priority pixels. 4,848 dots removed/refilled. | Same as above; broadened collar more likely to delete newly mapped faults close to the catalogue. | +0.000 DTI; plausible interval -0.010 to +0.010. | Paired live Δ≤-0.010 rejects this wider collar/refill policy; |Δ|<0.010 is no evidence. |
| PRUNE 5.5 px | A 550 m halo is likely beyond useful positional uncertainty, so lost adjacent new-fault credit may exceed any false-positive savings. 6,130 dots removed/refilled. | Mapped fault geometry may be displaced from its true trace by survey resolution; very broad pruning can remove legitimate nearby new geometry. | -0.003 DTI; plausible interval -0.010 to +0.010. | Paired live Δ≥+0.010 falsifies the predicted negative direction; |Δ|<0.010 is no evidence. |

The DTI algebra in `tests/test_metric_algebra.py` is unit-tested against synthetic component values. The official competition metric code was not accessed; no candidate was scored on labels or submitted. A local feature leakage canary is report-only; catalogue hide-and-recover and SGMC instruments were not used to rank candidates. Full inputs, exact hashes, parent differences and format receipts are in `evidence/build_receipt.json`.

## MASS (2026-10-23 session) — full cards in `ledger/mechanism_cards_mass.json`

**Shared mechanism.** DTI = T/(0.2T + 0.2(S−M) + 0.8|G|), 300 m triangular kernel. T is max-plus over dots:
a dot whose kernel disc is already claimed by a neighbour adds no unique credit, while a dot farther than 3 px
from hidden truth adds nothing to T and a full 1.0 to (S−M). Mass is a cost/benefit knob, not a neutral scale.

| Variant | Hypothesis | Non-fault mimic | Predicted live change (MODEL) | Falsifier |
|---|---|---|---|---|
| `uniq20` | 7,531 lowest-unique-credit dots are redundant mass; removing them cannot lower T and pays 0.2/Den each | Dense clusters also occur where several faults are mapped; a duplicated dot can be the second strand of a real step-over | +0.005 (−0.010 … +0.012) | live Δ ≤ −0.010 ⇒ the redundant dots were on hidden truth |
| `uniq30` | the same, deeper: the smallest dose whose optimistic end clears the 0.01 evidence bar | as above, plus risk of thinning genuine short isolated strands | +0.007 (−0.015 … +0.018) | live Δ ≤ −0.010 ⇒ mass reduction closed |
| `fifo20` | brief-literal control: the parent's own FIFO-BFS tail is an acceptable "least useful first" order | the FIFO tail is spatially arbitrary, so this arm mostly measures regional ablation | +0.001 (−0.012 … +0.009) | live Δ ≥ +0.010 ⇒ ordering does not matter, only count |

Structural-geologist note: check whether the removed dots concentrate on one trend or region. `uniq20` empties
13,380 of 26,645 eight-connected support patches (but only 21,356 support px, i.e. mostly single-pixel specks),
`fifo20` 10,311 (36,369 px). Both files keep every dot of the thick multi-pixel ridges.
