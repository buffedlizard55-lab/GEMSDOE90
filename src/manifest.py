"""Pin-and-verify gate for all inputs (brief s4.2, s5).

Usage:
  python -m src.manifest            # verify: OK / MISSING / MISMATCH / UNPINNED
  python -m src.manifest --fill     # human-run: record sha256 of files present under data/

No build may proceed unless every file it needs verifies OK.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "data_manifest.json"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load() -> dict:
    return json.loads(MANIFEST.read_text())


def verify(keys: list[str] | None = None) -> dict[str, str]:
    """Return {key: OK|MISSING|MISMATCH|UNPINNED}. Never raises on missing files."""
    files = load()["files"]
    out: dict[str, str] = {}
    for key, spec in files.items():
        if keys is not None and key not in keys:
            continue
        p = ROOT / spec["path"]
        if not p.exists():
            out[key] = "MISSING"
        elif not spec.get("sha256"):
            out[key] = "UNPINNED"
        elif sha256_of(p) != spec["sha256"]:
            out[key] = "MISMATCH"
        else:
            out[key] = "OK"
    return out


def require(keys: list[str]) -> dict[str, Path]:
    """Hard stop (SystemExit 2) unless every key verifies OK. Returns paths."""
    status = verify(keys)
    bad = {k: v for k, v in status.items() if v != "OK"}
    if bad:
        lines = ["STOP: required inputs not verified (brief s5: never approximate the parent):"]
        files = load()["files"]
        for k, v in bad.items():
            lines.append(f"  {k}: {v}  ({files[k]['path']}) -- {files[k]['required_for']}")
        print("\n".join(lines), file=sys.stderr)
        raise SystemExit(2)
    files = load()["files"]
    return {k: ROOT / files[k]["path"] for k in keys}


def fill() -> None:
    doc = load()
    for key, spec in doc["files"].items():
        p = ROOT / spec["path"]
        if p.exists():
            spec["sha256"] = sha256_of(p)
            spec["status"] = "PINNED"
            print(f"{key}: pinned {spec['sha256'][:8]}  {spec['path']}")
        else:
            spec["status"] = "MISSING"
            print(f"{key}: still missing  {spec['path']}")
    MANIFEST.write_text(json.dumps(doc, indent=2) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fill", action="store_true")
    args = ap.parse_args()
    if args.fill:
        fill()
    else:
        status = verify()
        for k, v in status.items():
            print(f"{k}: {v}")
        sys.exit(0 if all(v == "OK" for v in status.values()) else 2)
