# Mechanism cards — CONCENTRATION axis (structural geologist)

## Variant 1: h33-h33-2-b2-CONC2000M10PCT-20261023-e3d0073c
- **Parent:** h33-h33-2-b2 (37654 dots, none within 2px catalogue)
- **Change:** CONCENTRATION — block 2000m (20 px) — move 10% (3765 dots) from lowest-prior km-blocks to highest-prior blocks. Prior = 0.45·catalogue-intersection density +0.35·range-front (elev 0.6 Gaussian) +0.20·score smooth. Within target blocks, highest-ranked empty eligible pixels (score descending) filled; zero mass on catalogue and >=3px (2px exclusion) buffer enforced; count fixed 37654; CV 4.092→4.886 (Δ+0.794). Exact % changed =10.0.
- **Hypothesis:** Geothermal systems in the Great Basin cluster at fault step-overs, intersections and terminations (Faulds inventory) — block-scale prior captures this interaction; concentrating mass there aligns with expert-expanded private labels (Phase 2 rescore) that extend beyond public chunks.
- **Mechanism:** Organizer confirmed new-fault truth can lie within 300m (3px) of known traces, so block prior that weights intersection density should capture newly mapped geometry of existing systems (e.g., offset splays within 3px). DTI pays with credit >0.2·DTI (~0.056) for isolated pixel, lower for line-like — clustered high-prior blocks provide continuous line credit, boosting T while S-M penalty limited.
- **Non-fault mimicker:** Piedmont alluvial fans and range-front colluvial aprons create similar gravity/detrended-elevation gradients without faulting; our range-front prior could concentrate false positives on fan toes. Lithologic contacts also score high in TMI and mimic fault lineaments (ledger lanes 0.00-0.19).
- **Predicted sign & size (MODEL):** +0.004 (small positive). PROXY vs synthetic hidden truth shows -0.151 drop (0.937→0.787) because synthetic truth is intentionally dispersed — not predictive (proxy-live correlation -0.87 to +0.54 per ledger). Live change <0.01 = no evidence per brief §5; expect neutral to weak positive if private labels follow intersection prior.
- **Falsifier:** If live score <parent-0.01 (i.e., ≤0.2678 if parent claim holds) despite CV increase, concentration harms generalization — reject block-concentration hypothesis, favor uniform or MASS axis. Leakage canary AUC 0.998 flagged (synthetic leakage, see IRREGULARITIES) does not falsify but warns proxy is confounded.

## Variant 2: h33-h33-2-b2-CONC1000M15PCT-20261023-5af456e3
- **Parent:** h33-h33-2-b2
- **Change:** CONCENTRATION block 1000m (10 px) move 15% (5648 dots). Finer block scale tests km-scale heterogeneity. CV 5.453→5.904 (Δ+0.451). % changed 15.0.
- **Hypothesis:** ~1km block scale matches GeoDAWN Area 2 line spacing (400m) uncertainty radius (~3px=300m) — faults located within kernel radius, so finer blocks resolve individual step-overs vs basin-wide trends.
- **Mechanism:** Same prior, but 1km blocks isolate narrow relay zones where new faults splay off known traces within 3px. Expected T boost per truth pixel where fault density high; S-M term penalizes isolated dots in low-prior basin blocks removed.
- **Non-fault mimicker:** 400m flight-line artifacts and N-S cultural lineaments (roads/powerlines) generate 1km-periodic TMI stripes that mimic step-overs at this block size.
- **Predicted sign & size (MODEL):** -0.002 (neutral). Larger move (15%) increases CV moderately but risks overfitting to synthetic prior's intersection peaks; live private chunks may be more dispersed, so penalty may offset gain.
- **Falsifier:** If live CV vs Δ correlation is ~0 (both CONC10 and CONC15 neutral within ±0.01), km-scale concentration provides no signal at 1km — try 5km or switch to PRUNE.

## Variant 3: h33-h33-2-b2-CONC5000M20PCT-20261023-9502239f
- **Parent:** h33-h33-2-b2
- **Change:** CONCENTRATION block 5000m (50 px) move 20% (7531 dots). Coarse 5km blocks, strong 20% concentration. CV 2.891→5.142 (Δ+2.251, largest jump). % changed 20.0.
- **Hypothesis:** Basin-scale (5km) piedmont/range-front terciles control where geothermal systems sit (range-front 0.6 elev Gaussian) — coarse concentration tests basin vs range bias rather than individual intersections. RELIEF axis variant would shift mass between terciles; this CONC variant does so indirectly via block prior.
- **Mechanism:** 5km blocks average out high-frequency noise (AUC 0.57 single band) and favor range-front tercile; DTI beta=0.8 weight on |G| means missing large structures hurts more than missing isolated pixels — concentrating at basin scale hedges against expert-expanded labels that add km-scale systems (Phase 2).
- **Non-fault mimicker:** Broad gravity lows from deep basin fill mimic 5km prior but contain no faults; 20% mass shift amplifies this bias.
- **Predicted sign & size (MODEL):** -0.008 (small negative). Most aggressive move; PROXY drops most (0.937→0.645) because synthetic hidden truth is fine-scale dispersed, not basin-scale; live risk of false-positive penalty likely exceeds T gain.
- **Falsifier:** If live score drops >0.01 vs parent and vs CONC10, coarse concentration falsified — indicates best-files' CV 0.51-0.59 (moderate) is upper bound; our CV after 5.14 exceeds it, suggesting over-concentration. Next test should be less aggressive (e.g., 2000m 7% move) or combine with MASS reduction.

---
**Shared notes:** All variants count-fixed 37654, zero catalogue mass, >=3px buffer, NaN outside (primary) + zeros fallback. Per-pixel signal weak (best GBM 0.68 PROXY) so live changes <0.01 = no evidence. Faulds step-over inventory used only as prior on fault-interaction zones — target is fault pixels, never vents/heat.
