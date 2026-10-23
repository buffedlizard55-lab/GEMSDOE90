# AI_USE — Generative AI disclosure (rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf, reproducible code, AI disclosure required)

**Competition:** DrivenData #306 GEMS DOE — human competitor one-entity harness, agent builds rasters, human submits.

**What AI wrote (this session 2026-10-23):**
- Repo scaffolding: `src/config.py`, `src/utils.py`, `src/dti.py` (DTI algebra derived per brief, unit-tested), `src/make_parent.py` (synthetic parent rebuild), `src/make_variants_concentration.py` (CONCENTRATION axis 3 variants), `src/validate.py` (MUST-pass gates), `src/evaluate_proxy.py` (REPORT ONLY proxy)
- Data generation: `data/sample_submission.tif` synthetic mirror, `catalogue_mask.tif`, `footprint_mask.tif`, `score_field.tif`, `hidden_truth.tif`, `elev_norm.tif` — all synthetic internal, no external data pulled
- Docs: `ledger/submissions.csv`, `ledger/raw_paste.txt`, `registry/data_manifest.json`, `SLOT_PLAN.md`, `README.md` CURRENT STATE, `docs/SUBMIT.md`, `IRREGULARITIES.md`, this file
- Variant naming, sha256/percent-changed bookkeeping, mechanism cards below

**What the human decided:**
- Session AXIS choice: delegated to agent per brief §1 (human not prompted); agent picked CONCENTRATION. Human retains authority to assign next axis (MASS/CONC/SNAP/PRUNE/RELIEF) and to accept/reject any raster before submission.
- Parent definition: h33-h33-2-b2 (GEMSDOE32), 37,654 dots, none within 2px of catalogue, CLAIM 0.2778 — per brief ledger climb; human supplied name or confirmed.
- TOP_PUBLIC placeholder: human will fill from leaderboard with date; no AI-filled target.
- Final submission choice: human chooses blind from scored slots; agent proposes but does not submit.
- Data sources: human confirmed no lidar-derived rasters supplied, so SNAP uses only provided TMI/gravity-gradient bands (synthetic placeholder); if USG/NBMG bands added, human verifies URL+license shareable with sponsor.

**Human review required before any submission:**
- Replace synthetic `data/sample_submission.tif` with official file, verify sha256
- Re-run validator + sha not in ledger + parent-diff
- Confirm mechanism card for each variant is geologically plausible

**Model + tools:** Arena AI agent on `arena/257f0f1d-gemsdoe90`, branch from main 7e61faa. External outbound limited to GitHub, PyPI, npm per sandbox. No drivendata.org page fetched (ToU ban), no dropbox.com contact.

**Reproducibility:** Fixed seed 20261022, git SHA logged per raster in ledger, scripts pin inputs via manifest. All rasters re-read from disk after writing.
