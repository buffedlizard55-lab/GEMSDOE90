# SUBMIT — human upload checklist (brief §7)

**Never submit via code.** Human logs in at https://www.drivendata.org/competitions/306/ and uploads from registered account. One entity = 3 scored/week + 1 final blind; deadline 2026-12-03 (confirm on page).

## Current candidate (best MODEL-predicted, awaiting live receipt)

| Slot | File (local) | Upload name | Form note (≤140 chars) | Predicted Δ | Gates |
|------|--------------|-------------|------------------------|-------------|-------|
| 1 | `releases/h33-h33-2-b2-CONC2000M10PCT-20261023-e3d0073c.tif` + `-zeros.tif` fallback | `h33-h33-2-b2-CONC2000M10PCT-20261023-e3d0073c` | `parent h33-h33-2-b2; CONC 2000m move10% low->high prior CV4.09->4.89; pred +0.004 MODEL` (112 chars) | +0.004 MODEL | PASS |
| 2 | `releases/h33-h33-2-b2-CONC1000M15PCT-20261023-5af456e3.tif` | `h33-h33-2-b2-CONC1000M15PCT-20261023-5af456e3` | `parent h33-h33-2-b2; CONC 1000m move15% CV5.45->5.90; pred -0.002 MODEL` (96 chars) | -0.002 MODEL | PASS |
| 3 | `releases/h33-h33-2-b2-CONC5000M20PCT-20261023-9502239f.tif` | `h33-h33-2-b2-CONC5000M20PCT-20261023-9502239f` | `parent h33-h33-2-b2; CONC 5000m move20% CV2.89->5.14; pred -0.008 MODEL` (101 chars) | -0.008 MODEL | PASS |

**Recommended first slot:** `CONC2000M10PCT` (smallest CV increase, predicted +0.004, 3765 dots moved 10%). If live result is within ±0.01 treat as no evidence (public chunks only).

## Format receipt (fill after submission page response)
- [ ] Slot 1 uploaded: ______ date ______ score ______ receipt SHA8 ______ (copy receipt verbatim to ledger)
- [ ] Slot 2 uploaded: ______ date ______ score ______ receipt SHA8 ______
- [ ] Slot 3 uploaded: ______ date ______ score ______ receipt SHA8 ______

**Validator pre-flight (run before each upload, MUST pass):**
```bash
python src/validate.py releases/h33-h33-2-b2-CONC2000M10PCT-20261023-e3d0073c.tif
# expect: OK CRS 32611, OK shape 2500x2068, OK transform, OK dtype, OK NaN inside/outside, OK zero catalogue mass, OK >=3px buffer
sha256sum releases/h33-h33-2-b2-CONC2000M10PCT-20261023-e3d0073c.tif
# compare to ledger/submissions.csv; not already in ledger (dedupe on exact hash)
python -c "import rasterio; print(rasterio.open('releases/h33-h33-2-b2-CONC2000M10PCT-20261023-e3d0073c.tif').read(1).max())"  # values in [0,1], no NaN inside
```

**Fallback:** Use `-zeros.tif` only if platform rejects NaN outside (twin scores identically per ledger: 8 slots were exact sha repeats with NaN/zeros twins).

**What to copy to `ledger/submissions.csv` after scoring:**
`id, predicted_change -> receipt_score, receipt_date, note` — preserve parent/axis/value/pct_changed/sha256.

**Phase 2 track:** TRACKB GeoJSON + raster + evidence paragraph per trace is not a weekly-slot candidate unless human decides.

## History
- Parent `h33-h33-2-b2` CLAIM 0.2778 (no receipt) — 37654 dots, none within 2px, 4214546 eligible pixels.
- All 3 CONCENTRATION variants BUILT 2026-10-23, validated re-read from disk, sha256 unique (not in ledger prior).
