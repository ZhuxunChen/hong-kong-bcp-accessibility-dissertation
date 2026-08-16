#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "UPLOAD_CONTENTS.csv"
MANIFEST = ROOT / "docs" / "REPOSITORY_MANIFEST.sha256"
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".Rproj.user"}
EXCLUDED_NAMES = {"network.dat", "r5r-log.log", "gtfs_errors.csv", "Rplots.pdf"}
RENV_RUNTIME_DIRS = {"library", "local", "cellar", "lock", "python", "sandbox", "staging"}


def is_renv_runtime(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    return len(parts) >= 2 and parts[0] == "renv" and parts[1] in RENV_RUNTIME_DIRS


def is_generated_supplementary_output(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    return len(parts) >= 3 and parts[:3] == ("analysis", "meeting3_checks", "results")


def is_generated_final_figure_output(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    return len(parts) >= 3 and parts[:3] == ("analysis", "final_figures", "results")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


files = sorted(
    path for path in ROOT.rglob("*")
    if (
        path.is_file()
        and path not in {OUTPUT, MANIFEST}
        and not EXCLUDED_PARTS.intersection(path.parts)
        and path.name not in EXCLUDED_NAMES
        and not is_renv_runtime(path)
        and not is_generated_supplementary_output(path)
        and not is_generated_final_figure_output(path)
        and ".mapdb" not in path.name
    )
)

with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(("path", "bytes", "sha256"))
    for path in files:
        writer.writerow((path.relative_to(ROOT).as_posix(), path.stat().st_size, digest(path)))

print(f"Wrote {len(files)} upload inventory records")
