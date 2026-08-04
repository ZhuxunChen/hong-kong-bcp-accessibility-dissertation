#!/usr/bin/env python3
"""Compare full R5 minimum times with a calibrated straight-line benchmark."""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "analysis" / "stage9a"
if not (STAGE / "inputs").exists():
    STAGE = ROOT / "reference_outputs" / "stage9a"
RESULTS = ROOT / "analysis" / "meeting3_checks" / "results"


def haversine_km(lon1, lat1, lon2, lat2):
    radius = 6371.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * radius * np.arcsin(np.sqrt(a))


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    origins = pd.read_csv(STAGE / "inputs" / "tpu_origins_v3.csv", dtype={"id": str}).rename(columns={"id": "area_id"})
    bcps = pd.read_csv(STAGE / "inputs" / "bcp_destinations_v3.csv")
    access = pd.read_csv(STAGE / "results" / "accessibility_tpu_v3.csv", dtype={"area_id": str})
    data = origins.merge(access[["area_id", "min_tt"]], on="area_id", how="inner")

    distance_columns = []
    for _, bcp in bcps.iterrows():
        column = f"distance_{bcp['id']}_km"
        data[column] = haversine_km(data["lon"], data["lat"], bcp["lon"], bcp["lat"])
        distance_columns.append(column)
    data["nearest_straight_km"] = data[distance_columns].min(axis=1)

    d = data["nearest_straight_km"].to_numpy()
    t = data["min_tt"].to_numpy()
    minutes_per_km = float(np.sum(d * t) / np.sum(d * d))
    speed_kph = 60.0 / minutes_per_km
    data["calibrated_distance_time"] = d * minutes_per_km
    data["fixed_20kph_time"] = d / 20.0 * 60.0
    data["calibrated_residual"] = t - data["calibrated_distance_time"]
    data.to_csv(RESULTS / "minimal_distance_benchmark_tpu.csv", index=False)

    pred = data["fixed_20kph_time"].to_numpy()
    summary = {
        "n": int(len(data)),
        "fixed_speed_kph": 20.0,
        "calibrated_speed_kph": speed_kph,
        "pearson_r": float(pd.Series(d).corr(pd.Series(t), method="pearson")),
        "spearman_rho": float(pd.Series(d).rank().corr(pd.Series(t).rank())),
        "mae_minutes": float(np.mean(np.abs(t - pred))),
        "rmse_minutes": float(np.sqrt(np.mean((t - pred) ** 2))),
        "median_absolute_error_minutes": float(np.median(np.abs(t - pred))),
        "p90_absolute_error_minutes": float(np.quantile(np.abs(t - pred), 0.90)),
        "largest_underprediction_minutes": float(np.max(t - pred)),
        "largest_overprediction_minutes": float(np.min(t - pred)),
    }
    (RESULTS / "minimal_distance_benchmark_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
