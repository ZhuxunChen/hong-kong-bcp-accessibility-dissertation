#!/usr/bin/env python3
"""Validate the Stage 9A bidirectional custom MTR GTFS."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
ZIP_PATH = ROOT / "analysis" / "stage9a" / "network" / "mtr_gtfs_bidirectional_v3.zip"
OUT = ROOT / "analysis" / "stage9a" / "network" / "mtr_gtfs_validation_v3.json"


def time_seconds(value: str) -> int:
    hour, minute, second = (int(part) for part in value.split(":"))
    return hour * 3600 + minute * 60 + second


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUT}")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        trips = pd.read_csv(archive.open("trips.txt"), dtype={"trip_id": str})
        stop_times = pd.read_csv(archive.open("stop_times.txt"), dtype={"trip_id": str, "stop_id": str})
        routes = pd.read_csv(archive.open("routes.txt"), dtype={"route_id": str})
        stops = pd.read_csv(archive.open("stops.txt"), dtype={"stop_id": str})

    errors: list[str] = []
    if trips["trip_id"].duplicated().any():
        errors.append("Duplicate trip_id values")
    if stops["stop_id"].duplicated().any():
        errors.append("Duplicate stop_id values")
    if set(trips["direction_id"].unique()) != {0, 1}:
        errors.append("Direction IDs are not exactly {0, 1}")

    route_audit = []
    for route_id in routes["route_id"]:
        subset = trips[trips["route_id"] == route_id]
        directions = sorted(subset["direction_id"].unique().tolist())
        if directions != [0, 1]:
            errors.append(f"{route_id} does not contain both directions")
        route_audit.append(
            {
                "route_id": route_id,
                "trip_count": int(len(subset)),
                "direction_ids": directions,
            }
        )

    trip_routes = trips.set_index("trip_id")["route_id"]
    stop_times["route_id"] = stop_times["trip_id"].map(trip_routes)
    if stop_times["route_id"].isna().any():
        errors.append("stop_times contains unknown trip IDs")

    monotonic_failures = []
    endpoint_failures = []
    for trip_id, rows in stop_times.groupby("trip_id", sort=False):
        rows = rows.sort_values("stop_sequence")
        seconds = rows["arrival_time"].map(time_seconds)
        if not seconds.is_monotonic_increasing:
            monotonic_failures.append(trip_id)
        if trip_id.endswith("_R"):
            forward_id = trip_id[:-2]
            forward = stop_times[stop_times["trip_id"] == forward_id].sort_values("stop_sequence")
            if forward.empty or rows["stop_id"].tolist() != list(reversed(forward["stop_id"].tolist())):
                endpoint_failures.append(trip_id)
    if monotonic_failures:
        errors.append(f"Non-monotonic stop times in {len(monotonic_failures)} trips")
    if endpoint_failures:
        errors.append(f"Reverse stop sequence mismatch in {len(endpoint_failures)} trips")

    routes_per_stop = stop_times.groupby("stop_id")["route_id"].nunique()
    interchange_stops = sorted(routes_per_stop[routes_per_stop >= 2].index.tolist())
    required_interchanges = {"MTR_ADM", "MTR_HUH", "MTR_KOT", "MTR_TAW"}
    missing_interchanges = sorted(required_interchanges - set(interchange_stops))
    if missing_interchanges:
        errors.append(f"Required interchange stop IDs are not shared: {missing_interchanges}")

    required_bcp_stops = {"MTR_LOW", "MTR_LMC"}
    if not required_bcp_stops.issubset(set(stops["stop_id"])):
        errors.append("Lo Wu or Lok Ma Chau BCP stop missing")

    result = {
        "valid": not errors,
        "errors": errors,
        "routes": int(len(routes)),
        "trips": int(len(trips)),
        "stop_time_rows": int(len(stop_times)),
        "directions": sorted(trips["direction_id"].unique().tolist()),
        "route_audit": route_audit,
        "interchange_stop_count": len(interchange_stops),
        "interchange_stops": interchange_stops,
        "monotonic_failure_count": len(monotonic_failures),
        "reverse_sequence_failure_count": len(endpoint_failures),
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
