#!/usr/bin/env python3
"""Create reproducible evidence for the local cases discussed after Meeting 3."""

from __future__ import annotations

import math
from pathlib import Path
import zipfile

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "analysis" / "stage9a"
if not (STAGE / "inputs").exists():
    STAGE = ROOT / "reference_outputs" / "stage9a"
RESULTS = ROOT / "analysis" / "meeting3_checks" / "results"


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def nearest_stop(stops: pd.DataFrame, lon: float, lat: float) -> pd.Series:
    distances = [
        haversine_m(lon, lat, stop_lon, stop_lat)
        for stop_lon, stop_lat in zip(stops["stop_lon"], stops["stop_lat"])
    ]
    return stops.assign(distance_m=distances).sort_values("distance_m").iloc[0]


def load_stops(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as feed:
        stops = pd.read_csv(feed.open("stops.txt"), dtype=str)
    stops["stop_lon"] = pd.to_numeric(stops["stop_lon"])
    stops["stop_lat"] = pd.to_numeric(stops["stop_lat"])
    return stops


def load_lo_wu_feeder_headways(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as feed:
        frequencies = pd.read_csv(feed.open("frequencies.txt"), dtype=str)
        trips = pd.read_csv(feed.open("trips.txt"), dtype=str)
        routes = pd.read_csv(feed.open("routes.txt"), dtype=str)
    joined = frequencies.merge(trips[["trip_id", "route_id"]], on="trip_id").merge(
        routes[["route_id", "route_short_name", "route_long_name"]], on="route_id"
    )
    feeder = joined.loc[joined["route_short_name"].eq("51B")].copy()
    feeder["headway_minutes"] = pd.to_numeric(feeder["headway_secs"]) / 60
    # Keep frequency windows that intersect the 08:00-08:30 analysis window.
    return feeder.loc[(feeder["start_time"] < "08:30:00") & (feeder["end_time"] > "08:00:00")]


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    origins = pd.read_csv(STAGE / "inputs" / "stpug_origins_v3.csv", dtype={"id": str})
    matrix = pd.read_csv(
        STAGE / "results" / "travel_time_matrix_stpug_v3.csv",
        dtype={"from_id": str, "to_id": str},
    )
    gwr = gpd.read_file(STAGE / "results" / "figures_and_spatial" / "gwr_local_results_stpug_v3.gpkg")
    bus_stops = load_stops(STAGE / "network" / "hk_gtfs.zip")
    mtr_stops = load_stops(STAGE / "network" / "mtr_gtfs_bidirectional_v3.zip")

    # Reproduce the Lo Wu adjacency evidence used in the interpretation.
    tpu_geo = gpd.read_file(STAGE / "inputs" / "tpu_geography_v3.gpkg").to_crs(2326)
    tpu_geo["TPU"] = tpu_geo["TPU"].astype(str).str.strip()
    tpu_origins = pd.read_csv(STAGE / "inputs" / "tpu_origins_v3.csv", dtype={"id": str})
    origin_geo = gpd.GeoDataFrame(
        tpu_origins,
        geometry=gpd.points_from_xy(tpu_origins["lon"], tpu_origins["lat"]),
        crs=4326,
    ).to_crs(2326)
    bcp = pd.read_csv(STAGE / "inputs" / "bcp_destination_provenance_v3.csv")
    lo_wu = bcp.loc[bcp["id"].eq("LW")].iloc[0]
    lo_wu_point = gpd.GeoSeries(gpd.points_from_xy([lo_wu["lon"]], [lo_wu["lat"]]), crs=4326).to_crs(2326).iloc[0]
    lw_matrix = pd.read_csv(
        STAGE / "results" / "travel_time_matrix_tpu_v3.csv",
        dtype={"from_id": str, "to_id": str},
    )
    lw_matrix = lw_matrix.loc[lw_matrix["to_id"].eq("LW")].rename(columns={"from_id": "TPU"})
    audit = tpu_geo[["TPU", "geometry"]].copy()
    audit["covers_lo_wu"] = audit.geometry.covers(lo_wu_point)
    audit["boundary_distance_m"] = audit.geometry.distance(lo_wu_point)
    audit = audit.merge(
        origin_geo[["id", "geometry"]].rename(columns={"id": "TPU", "geometry": "origin_geometry"}),
        on="TPU",
        how="left",
    )
    audit["origin_distance_m"] = audit["origin_geometry"].apply(
        lambda point: point.distance(lo_wu_point) if point is not None else float("nan")
    )
    audit = audit.merge(lw_matrix, on="TPU", how="left").sort_values("boundary_distance_m").head(10)
    audit.drop(columns=["geometry", "origin_geometry"]).to_csv(
        RESULTS / "lo_wu_adjacent_tpu_spatial_audit.csv", index=False
    )

    rows = []
    for stpug_id in ["634", "757", "288S"]:
        origin = origins.loc[origins["id"].eq(stpug_id)].iloc[0]
        model = gwr.loc[gwr["stpug_id"].eq(stpug_id)].iloc[0]
        best = matrix.loc[matrix["from_id"].eq(stpug_id)].sort_values("travel_time_p50").iloc[0]
        bus = nearest_stop(bus_stops, origin["lon"], origin["lat"])
        mtr = nearest_stop(mtr_stops, origin["lon"], origin["lat"])
        rows.append(
            {
                "stpug_id": stpug_id,
                "origin_lon": origin["lon"],
                "origin_lat": origin["lat"],
                "median_hh_income_hkd": model["median_hh_income"],
                "population_density_km2": model["pop_density_km2"],
                "minimum_time_minutes": model["min_tt"],
                "nearest_bcp": best["to_id"],
                "gwr_income_beta": model["gwr_income_beta"],
                "gwr_income_t": model["gwr_income_t"],
                "gwr_income_significant": model["gwr_income_significant"],
                "nearest_bus_stop": bus["stop_name"],
                "nearest_bus_stop_distance_m": bus["distance_m"],
                "nearest_mtr_station": mtr["stop_name"],
                "nearest_mtr_station_distance_m": mtr["distance_m"],
            }
        )

    cases = pd.DataFrame(rows)
    cases.to_csv(RESULTS / "gwr_local_case_evidence.csv", index=False)

    # The Lo Wu audit uses the TPU 622 representative origin and the frozen public feed.
    tpu_origin = pd.read_csv(STAGE / "inputs" / "tpu_origins_v3.csv", dtype={"id": str})
    lo_wu_origin = tpu_origin.loc[tpu_origin["id"].eq("622")].iloc[0]
    nearby = bus_stops.assign(
        distance_m=[
            haversine_m(lo_wu_origin["lon"], lo_wu_origin["lat"], lon, lat)
            for lon, lat in zip(bus_stops["stop_lon"], bus_stops["stop_lat"])
        ]
    ).sort_values("distance_m").head(5)
    nearby[["stop_id", "stop_name", "distance_m"]].to_csv(
        RESULTS / "lo_wu_tpu622_nearest_stops.csv", index=False
    )
    feeder = load_lo_wu_feeder_headways(STAGE / "network" / "hk_gtfs.zip")
    feeder[["route_short_name", "route_long_name", "start_time", "end_time", "headway_minutes"]].to_csv(
        RESULTS / "lo_wu_route51b_frequency_windows.csv", index=False
    )

    text = [
        "Local-case evidence for the supplementary checks",
        "================================================",
        "",
        "TPU 622 is documented in lo_wu_adjacent_tpu_spatial_audit.csv. Its origin is 1.71 km",
        "from Lo Wu, and the frozen routing result requires route 51B towards Sheung Shui",
        "before returning north on East Rail. The feed represents the Ma Tso Lung-to-Sheung",
        "Shui direction with a 60-minute headway around the 08:00 departure window, so waiting",
        "and transfer structure are material alongside the missing direct pedestrian link.",
        "",
        "STPUG 634 has a significant positive local income coefficient. Its representative",
        "origin is 3.24 km from Fanling MTR and 0.52 km from the nearest listed bus stop; its",
        "minimum BCP time is 44 minutes. This is consistent with feeder dependence but does",
        "not identify a causal income mechanism.",
        "",
        "STPUG 757 has a significant negative local income coefficient. Its representative",
        "origin is 0.53 km from Ma On Shan MTR, but the nearest BCP still takes 71 minutes",
        "because reaching East Rail requires movement through the wider rail network. The",
        "contrast with STPUG 634 shows why local coefficient signs should be read as spatial",
        "diagnostics rather than direct effects.",
    ]
    (RESULTS / "feedback_local_case_evidence.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(cases.to_string(index=False))


if __name__ == "__main__":
    main()
