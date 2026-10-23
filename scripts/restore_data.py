#!/usr/bin/env python3
"""Restore and SHA-256 verify all pinned inputs from registry/data_manifest.json.

Hard Constraint #1 & #2 compliance:
- Fetches strictly from commit-pinned GitHub objects via `gh api` or `codeload.github.com`
  (never contacts dropbox.com or drivendata.org; never touches credentials).
- Stores all competition and external rasters locally under `.cache/gems_data/`
  (strictly `.gitignore`d — never committed to public Git repos or releases).
- Verifies exact SHA-256 and byte length on every single file before any script can use it;
  aborts immediately with non-zero exit status on any mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_github_blob(repo: str, ref: str, path: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        # Check blob sha via contents metadata (handles blobs > 100 MiB cleanly via git/blobs too)
        meta_raw = subprocess.check_output(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}"],
            text=True,
        )
        meta = json.loads(meta_raw)
        blob_sha = meta["sha"]
        with tmp.open("wb") as out:
            subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{repo}/git/blobs/{blob_sha}",
                    "-H",
                    "Accept: application/vnd.github.raw",
                ],
                stdout=out,
                check=True,
            )
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def restore_entry(entry: dict, target_dir: Path) -> dict:
    dest = target_dir / entry["dest"]
    expected_sha = entry["sha256"]
    expected_bytes = entry["bytes"]

    if dest.is_file() and dest.stat().st_size == expected_bytes and sha256_file(dest) == expected_sha:
        return {
            "id": entry["id"],
            "dest": entry["dest"],
            "group": entry["group"],
            "status": "present_verified",
            "bytes": dest.stat().st_size,
            "sha256": expected_sha,
        }

    if "parts" in entry:
        tmp = dest.with_suffix(".assembling")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        parts_dir = target_dir / "_parts"
        try:
            with tmp.open("wb") as out:
                for part in entry["parts"]:
                    part_file = parts_dir / Path(part).name
                    fetch_github_blob(entry["repo"], entry["ref"], part, part_file)
                    with part_file.open("rb") as src:
                        while True:
                            buf = src.read(1 << 20)
                            if not buf:
                                break
                            out.write(buf)
                    part_file.unlink(missing_ok=True)
            got_bytes = tmp.stat().st_size
            got_sha = sha256_file(tmp)
            if got_sha != expected_sha or got_bytes != expected_bytes:
                tmp.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Integrity verification failed for {entry['id']}: "
                    f"sha256={got_sha} (expected {expected_sha}), bytes={got_bytes} (expected {expected_bytes})"
                )
            tmp.replace(dest)
        finally:
            tmp.unlink(missing_ok=True)
    else:
        fetch_github_blob(entry["repo"], entry["ref"], entry["path"], dest)
        got_bytes = dest.stat().st_size
        got_sha = sha256_file(dest)
        if got_sha != expected_sha or got_bytes != expected_bytes:
            dest.unlink(missing_ok=True)
            raise RuntimeError(
                f"Integrity verification failed for {entry['id']}: "
                f"sha256={got_sha} (expected {expected_sha}), bytes={got_bytes} (expected {expected_bytes})"
            )

    return {
        "id": entry["id"],
        "dest": entry["dest"],
        "group": entry["group"],
        "status": "restored_verified",
        "bytes": dest.stat().st_size,
        "sha256": expected_sha,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=str(ROOT / "registry" / "data_manifest.json"))
    ap.add_argument("--target-dir", default=str(ROOT / ".cache" / "gems_data"))
    ap.add_argument("--receipt", default=str(ROOT / "evidence" / "manifest_verification.json"))
    ap.add_argument("--group", default="all")
    args = ap.parse_args()

    t0 = time.time()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    target_dir = Path(args.target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for entry in manifest["files"]:
        if args.group not in ("all", entry["group"]):
            continue
        res = restore_entry(entry, target_dir)
        results.append(res)
        print(f"[{res['status']:17s}] {res['id']:46s} {res['bytes']:10d} B  sha256={res['sha256'][:16]}...")

    receipt = {
        "schema_version": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manifest_path": "registry/data_manifest.json",
        "verified_files_count": len(results),
        "all_sha256_matched": True,
        "organizer_authenticated": False,
        "note": "All SHA-256 and byte pins verified against registry/data_manifest.json. Files stored outside Git in .cache/gems_data/ per Hard Constraint #2.",
        "elapsed_s": round(time.time() - t0, 2),
        "files": results,
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(results)}/{len(results)} pinned inputs in {receipt['elapsed_s']}s -> {receipt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
