#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "reference_outputs" / "stage9a"
MANIFEST = json.loads((REFERENCE / "stage9a_manifest_v3.json").read_text())

def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def resolve(source_path: str) -> Path:
    suffix = Path(source_path).relative_to("analysis/stage9a")
    if suffix.parts[0] in {"scripts", "reference_inputs"}:
        return ROOT / "analysis" / "stage9a" / suffix
    return REFERENCE / suffix

failures = []
for entry in MANIFEST["entries"]:
    path = resolve(entry["path"])
    if not path.is_file():
        failures.append(f"MISSING {path.relative_to(ROOT)}")
    elif path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
        failures.append(f"MISMATCH {path.relative_to(ROOT)}")

results = json.loads((REFERENCE / "results" / "stage9a_results_v3.json").read_text())
spatial = json.loads((REFERENCE / "results" / "figures_and_spatial" / "stage9a_spatial_results_v3.json").read_text())
claims = {
    "routed_tpus": results["place_metrics"]["stable_routed_tpus"] == 209,
    "routed_stpugs": results["stpug_metrics"]["routed_stpugs"] == 176,
    "mean_min_tt": abs(results["place_metrics"]["new_mean_min_tt"] - 67.0) < 1e-12,
    "min_tt_gini": abs(results["place_metrics"]["new_gini_min_tt"] - 0.14832980082531877) < 1e-12,
    "gini_60": abs(results["place_metrics"]["new_gini_bcps_within_60"] - 0.7780194287371321) < 1e-12,
    "moran_i": abs(spatial["spatial_tpu"]["min_tt"]["moran_i"] - 0.8399443413732915) < 1e-12,
}
failures.extend(f"CLAIM FAILED {key}" for key, ok in claims.items() if not ok)

if failures:
    print("\n".join(failures))
    raise SystemExit(1)
print(f"Stage 9A verification passed: {len(MANIFEST['entries'])}/{len(MANIFEST['entries'])} hashes and {len(claims)}/{len(claims)} headline claims.")
