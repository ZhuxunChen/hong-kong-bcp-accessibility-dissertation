#!/usr/bin/env python3
"""Create a portable Stage 9A checksum manifest, excluding r5 caches."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "analysis" / "stage9a"
MANIFEST = STAGE / "stage9a_manifest_v3.sha256"
SUMMARY = STAGE / "stage9a_manifest_v3.json"


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def included(path: Path) -> bool:
    relative = path.relative_to(STAGE)
    excluded_names = {"network.dat", "r5r-log.log", "gtfs_errors.csv"}
    if path.name in excluded_names or ".mapdb" in path.name:
        return False
    if "failed_attempt" in str(relative):
        return False
    return path.is_file() and path not in {MANIFEST, SUMMARY}


def main() -> None:
    force = "--force" in sys.argv[1:]
    if (MANIFEST.exists() or SUMMARY.exists()) and not force:
        raise FileExistsError("Refusing to overwrite Stage 9A manifest")
    files = sorted(path for path in STAGE.rglob("*") if included(path))
    entries = []
    for path in files:
        relative = path.relative_to(ROOT)
        entries.append(
            {"path": str(relative), "bytes": path.stat().st_size, "sha256": digest(path)}
        )
    MANIFEST.write_text(
        "".join(f"{entry['sha256']}  {entry['path']}\n" for entry in entries),
        encoding="utf-8",
    )
    SUMMARY.write_text(
        json.dumps(
            {
                "file_count": len(entries),
                "total_bytes": sum(entry["bytes"] for entry in entries),
                "excluded_generated_caches": [
                    "network.dat", "*.mapdb*", "r5r-log.log", "gtfs_errors.csv",
                    "failed_attempt*",
                ],
                "entries": entries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} Stage 9A checksums")


if __name__ == "__main__":
    main()
