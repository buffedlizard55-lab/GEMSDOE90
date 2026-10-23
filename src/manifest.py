"""Verify the commit-pinned raster/data manifest used by this repository.

The canonical manifest schema is the `files: [...]` array in
`registry/data_manifest.json`; every entry includes a commit-pinned GitHub source,
destination, byte length and SHA-256. Inputs are stored only in ignored `.cache/`.
The older `src.build_prune` interface is retained for compatibility, but its
human-provided ranked_candidates/metric-code keys are not in the current manifest
and it therefore stops rather than creating a different/approximate candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "data_manifest.json"
DATA_ROOT = ROOT / ".cache" / "gems_data"
ALIASES = {
    "sample_submission": "sample_submission",
    "r0_raster": "parent_r0_zeros",
    "catalogue_raster": "existing_faults",
    "preprune_dots": "scored_h27_4_solo_d28",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def entries_by_id() -> dict[str, dict]:
    raw = load().get("files", [])
    if not isinstance(raw, list):
        raise ValueError("registry/data_manifest.json files must be a pinned-entry array")
    return {entry["id"]: entry for entry in raw}


def _resolve(key: str) -> tuple[dict | None, Path | None]:
    ident = ALIASES.get(key, key)
    entry = entries_by_id().get(ident)
    if entry is None:
        return None, None
    return entry, DATA_ROOT / entry["dest"]


def verify(keys: list[str] | None = None) -> dict[str, str]:
    """Return OK/MISSING/MISMATCH statuses; never claims an absent pin is verified."""
    all_ids = list(entries_by_id())
    names = list(ALIASES) + [ident for ident in all_ids if ident not in ALIASES.values()]
    selected = keys if keys is not None else names
    out: dict[str, str] = {}
    for key in selected:
        entry, path = _resolve(key)
        if entry is None or path is None or not path.is_file():
            out[key] = "MISSING"
        elif not entry.get("sha256"):
            out[key] = "UNPINNED"
        elif path.stat().st_size != entry["bytes"] or sha256_of(path) != entry["sha256"]:
            out[key] = "MISMATCH"
        else:
            out[key] = "OK"
    # Historical builder inputs not present in the pinned canonical manifest must remain missing.
    for key in ("ranked_candidates", "metric_code"):
        if keys is None or key in selected:
            out.setdefault(key, "MISSING")
    return out


def require(keys: list[str]) -> dict[str, Path]:
    """Hard stop unless every requested key resolves to a pinned, hash-matching file."""
    status = verify(keys)
    bad = {key: state for key, state in status.items() if state != "OK"}
    if bad:
        lines = ["STOP: required inputs are not verified; never approximate R0:"]
        for key, state in bad.items():
            entry, path = _resolve(key)
            detail = str(path) if path else "no matching pinned entry in registry/data_manifest.json"
            lines.append(f"  {key}: {state} ({detail})")
        print("\n".join(lines), file=sys.stderr)
        raise SystemExit(2)
    out = {}
    for key in keys:
        _entry, path = _resolve(key)
        assert path is not None
        out[key] = path
    return out


def fill() -> None:
    """Compatibility no-op: canonical source pins are immutable and never guessed locally."""
    print("STOP: this manifest is commit-pinned; do not replace source hashes from local files.")
    print("To restore/reverify inputs, run: .venv/bin/python scripts/restore_data.py")
    raise SystemExit(2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fill", action="store_true")
    args = ap.parse_args()
    if args.fill:
        fill()
    status = verify()
    for key, state in status.items():
        print(f"{key}: {state}")
    sys.exit(0 if all(state == "OK" for state in status.values()) else 2)
