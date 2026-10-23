# IRREGULARITIES.md

Only items that change a decision. Logged 2026-10-23.

## 1. Repo is a bare skeleton — none of the brief's referenced artifacts exist
The checkout at `arena/3efb9d9c-gemsdoe90` contains exactly one file (`README.md`,
11 bytes) and one commit (`7e61faa`). Absent, and not present anywhere else on the
sandbox filesystem:

- `registry/data_manifest.json` (no pinned inputs exist)
- `ledger/submissions.csv` and `ledger/raw_paste.txt`
- `sample_submission.tif` (needed for CRS / shape / transform / dtype / band-count gates)
- the fault catalogue (needed to enforce "zero catalogue mass, >=3 px away")
- the R0 ranking recipe / ranking output (needed for MASS, CONCENTRATION, RELIEF, SPACING)
- all generation scripts, `releases/`, `docs/SUBMIT.md`, `AI_USE.md`, `SLOT_PLAN.md`

**Decision changed:** the session task's first step — "verify manifest hashes; rebuild R0
and match its sha256" — cannot be executed. The brief says: if you cannot rebuild R0,
stop and report; never approximate the parent. **No variant was built.** Every week in
SLOT_PLAN.md shifts by however long it takes to restore these inputs.

## 2. No CI configuration in the repo
There is no `.github/workflows/` or equivalent. The gate "merge only if CI is green and
no conflict markers exist" is unresolvable here; no PR will be opened until a CI config
(or an explicit human waiver) exists. Recorded rather than assumed.

## 3. The brief's ledger column spec conflicts with itself
§3 defines `ledger/submissions.csv` columns as `site, name, score, encoding, n_dots,
sha8, parent, receipt Y/N`; §7 defines them as `id, parent, axis, value, n_dots, %
changed, sha256, status, predicted change`. The header written here carries both sets
(plus `date`) so neither format has to be guessed at again. Not a scoring issue, but it
would have cost a slot's worth of confusion later.

## 4. Input-source constraint makes self-provisioning impossible
The sandbox reaches GitHub, PyPI and npm only; `drivendata.org` automated access is
banned by the terms (and Dropbox is off-limits by rule). The competition rasters
(`sample_submission.tif`, the catalogue) therefore cannot be fetched by this agent and
are not pip/npm artifacts. They must be supplied by the human. Flagged so nobody assumes
"the agent will just download them."

## 5. The h33/GEMSDOE lineage cannot be reconstructed from this repo
`GEMSDOE32`, `GEMSDOE76-81` etc. are named in the brief but none of their files or
scripts are present. Any claim about R0's prior steps (0.1922 → 0.2477 → 0.2600 → 0.2708
→ 0.2778) remains CLAIM/RECEIPT-sourced narrative, not something reproducible here.
