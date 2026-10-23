# Human submission packet — GEMSDOE90 SNAP candidates

**DO NOT UPLOAD YET.** These are LOCAL-ONLY experiments. R0 contains 1,611 dots at 2.236–3 px from the catalogue; literal ≤2 px SNAP cannot clear all of them without adding a PRUNE edit. The candidates inherit those exact pixels and add no new sub-3 px mass, but fail the brief's general ≥3 px rule. A human must resolve that conflict before any upload. The agent never submits.

## Files, names and form notes

Use only one candidate per authorized slot and only one encoding. The NaN file is preferred by spec; `-zeros.tif` is its fallback twin, not another experiment.

| Candidate | NaN-outside file in `releases/` |
|---|---|
| VG mean | `h33-h33-2-b2-SNAPvgmean2g10s2p8-20261023-33bbe8f2.tif` |
| TMI VG | `h33-h33-2-b2-SNAPtmivg2g10s2p8-20261023-64011c73.tif` |
| Gravity VG | `h33-h33-2-b2-SNAPgravvg2g10s2p8-20261023-332ab617.tif` |

Each fallback is the same base filename plus `-zeros.tif`. Copy these form notes exactly (each ≤140 chars):

- VG mean: `h33-h33-2-b2; SNAP <=2px to gated TMI+gravity VG mean edge, 2.8px spacing; predicted +0.002 DTI MODEL`
- TMI VG: `h33-h33-2-b2; SNAP <=2px to gated |TMI VG| edge, 2.8px spacing; predicted +0.001 DTI MODEL`
- Gravity VG: `h33-h33-2-b2; SNAP <=2px to gated |gravity VG| edge, 2.8px spacing; predicted -0.002 DTI MODEL`

Full SHA-256, both encodings, file sizes and per-check receipts are in `evidence/snap_build_receipt.json`; ledger rows contain the same hashes. No candidate has a receipt or live score. R0's 0.2778 remains **CLAIM**; predictions are **MODEL**.

## Format receipt and parent diff

All six files were re-read from disk and passed: sample CRS/transform/shape, one float32 band, finite values in [0,1] inside the footprint, correct outside encoding, exact expected mask, 37,654 unit dots, zero catalogue mass, and ≥2.828 px nearest-neighbour spacing. Maximum displacement is 2 px. The general ≥3 px catalogue check is explicitly **FAIL_INHERITED_FROM_R0**, not a pass.

| Candidate | Dots moved (% R0) | Mean displacement, all dots | NaN SHA-256 |
|---|---:|---:|---|
| VG mean | 8,010 (21.272640%) | 0.385331 px | `33bbe8f25c64b2d45470a0e6277cd68f694b845df1dabe53041ad2505dfdd77e` |
| TMI VG | 13,443 (35.701386%) | 0.632965 px | `64011c732952f56529ffad642680b108abd9b452359d710cae24d5165de60f8e` |
| Gravity VG | 2,999 (7.964625%) | 0.150466 px | `332ab6177307cc2a5ad62ae4a3a7e367be72729cb151b078a766ebd884b4ece8` |

## Regenerate and verify (required before any authorized use)

Competition rasters are gitignored and must not be committed to this public repository or attached to a public release.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py
.venv/bin/python scripts/build_snap_vertical.py --restore
.venv/bin/python scripts/build_snap_vertical.py --verify
.venv/bin/python -m pytest -q
```

`--build` is intentionally blocked after registration; `--restore` reproduces the recorded axis/value pairs and fails on any byte mismatch. Match the on-disk SHA-256 to the ledger before upload.

Human must supply: collar-eligibility decision; R0 submission-page receipt and date; dated TOP_PUBLIC; weekly/total slots used and remaining; confirmed official deadline/cutoff; and any candidate receipt. Default slot decision is HOLD (see `SLOT_PLAN.md`).
