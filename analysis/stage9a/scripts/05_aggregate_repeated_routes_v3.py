#!/usr/bin/env python3
"""Aggregate repeated r5r matrices and quantify routing uncertainty."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "analysis" / "stage9a"
RUNS = STAGE / "runs"
RESULTS = STAGE / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def aggregate(grain: str) -> tuple[pd.DataFrame, dict]:
    paths = sorted(RUNS.glob(f"run_*/travel_time_matrix_{grain}_v3.csv"))
    if len(paths) < 3:
        raise ValueError(f"Expected at least three {grain} routing repetitions, found {len(paths)}")
    frames = []
    per_run = []
    for run_number, path in enumerate(paths, start=1):
        frame = pd.read_csv(path)
        frame["from_id"] = frame["from_id"].astype(str)
        frame["to_id"] = frame["to_id"].astype(str)
        if frame.duplicated(["from_id", "to_id"]).any():
            raise ValueError(f"Duplicate OD keys in {path}")
        frame["run"] = run_number
        frames.append(frame)
        per_run.append(
            {
                "run": run_number,
                "path": str(path.relative_to(ROOT)),
                "rows": int(len(frame)),
                "origins_with_any_row": int(frame["from_id"].nunique()),
                "origins_with_valid_p50": int(frame.loc[frame["travel_time_p50"].notna(), "from_id"].nunique()),
                "valid_p50_rows": int(frame["travel_time_p50"].notna().sum()),
            }
        )

    combined = pd.concat(frames, ignore_index=True)
    n_runs = len(paths)
    min_presence = math.ceil(n_runs / 2)
    grouped = combined.groupby(["from_id", "to_id"], sort=True)
    rows = []
    p50_sds = []
    p50_ranges = []
    for (from_id, to_id), group in grouped:
        p50 = group["travel_time_p50"].dropna()
        if len(p50) < min_presence:
            continue
        p25 = group["travel_time_p25"].dropna()
        p75 = group["travel_time_p75"].dropna()
        p50_sd = float(p50.std(ddof=1)) if len(p50) > 1 else 0.0
        p50_range = float(p50.max() - p50.min())
        p50_sds.append(p50_sd)
        p50_ranges.append(p50_range)
        rows.append(
            {
                "from_id": from_id,
                "to_id": to_id,
                "travel_time_p25": float(p25.median()) if not p25.empty else np.nan,
                "travel_time_p50": float(p50.median()),
                "travel_time_p75": float(p75.median()) if not p75.empty else np.nan,
                "runs_present_p50": int(len(p50)),
                "p50_run_sd": p50_sd,
                "p50_run_range": p50_range,
            }
        )

    result = pd.DataFrame(rows).sort_values(["from_id", "to_id"]).reset_index(drop=True)
    summary = {
        "grain": grain,
        "n_runs": n_runs,
        "minimum_run_presence": min_presence,
        "per_run": per_run,
        "stable_od_rows": int(len(result)),
        "stable_origins": int(result["from_id"].nunique()),
        "od_rows_present_all_runs": int((result["runs_present_p50"] == n_runs).sum()),
        "p50_run_sd_median": float(np.median(p50_sds)),
        "p50_run_sd_p95": float(np.quantile(p50_sds, 0.95)),
        "p50_run_range_median": float(np.median(p50_ranges)),
        "p50_run_range_max": float(np.max(p50_ranges)),
    }
    return result, summary


def main() -> None:
    outputs = {
        "tpu": RESULTS / "travel_time_matrix_tpu_v3.csv",
        "stpug": RESULTS / "travel_time_matrix_stpug_v3.csv",
        "summary": RESULTS / "routing_uncertainty_v3.json",
    }
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite Stage 9A route aggregates: {existing}")

    tpu, tpu_summary = aggregate("tpu")
    stpug, stpug_summary = aggregate("stpug")
    tpu.to_csv(outputs["tpu"], index=False)
    stpug.to_csv(outputs["stpug"], index=False)
    payload = {
        "aggregation_rule": "Median travel time across runs; retain OD if p50 exists in at least ceil(n_runs/2) runs.",
        "tpu": tpu_summary,
        "stpug": stpug_summary,
    }
    outputs["summary"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
