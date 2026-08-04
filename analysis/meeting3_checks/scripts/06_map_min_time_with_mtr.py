#!/usr/bin/env python3
"""Rebuild the minimum-time map with the analytical MTR network overlaid."""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
import pandas as pd
from shapely.geometry import LineString


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "analysis" / "stage9a"
if not (STAGE / "inputs").exists():
    STAGE = ROOT / "reference_outputs" / "stage9a"
INPUTS = STAGE / "inputs"
RESULTS = STAGE / "results"
GTFS = STAGE / "network" / "mtr_gtfs_bidirectional_v3.zip"
OUTPUT = ROOT / "analysis" / "meeting3_checks" / "results"

COLOURS = {
    "MTR_EAL": "#53B7E8",
    "MTR_EAL_LMC": "#53B7E8",
    "MTR_TWL": "#E2231A",
    "MTR_KTL": "#00AB4E",
    "MTR_ISL": "#007DC5",
    "MTR_TML": "#8B5A3C",
    "MTR_TKL": "#7D499D",
    "MTR_TCL": "#F7943E",
    "MTR_SIL": "#A6B727",
}


def read_gtfs_table(archive: zipfile.ZipFile, name: str) -> pd.DataFrame:
    with archive.open(name) as handle:
        return pd.read_csv(io.TextIOWrapper(handle, encoding="utf-8-sig"), dtype=str)


def representative_lines() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    with zipfile.ZipFile(GTFS) as archive:
        routes = read_gtfs_table(archive, "routes.txt")
        trips = read_gtfs_table(archive, "trips.txt")
        stop_times = read_gtfs_table(archive, "stop_times.txt")
        stops = read_gtfs_table(archive, "stops.txt")

    stops["stop_lon"] = stops["stop_lon"].astype(float)
    stops["stop_lat"] = stops["stop_lat"].astype(float)
    stop_times["stop_sequence"] = stop_times["stop_sequence"].astype(int)
    trips = trips.merge(routes[["route_id", "route_short_name", "route_long_name"]], on="route_id")
    forward = trips[trips["direction_id"].fillna("0") == "0"].copy()

    records = []
    for route_id, group in forward.groupby("route_id", sort=False):
        candidates = stop_times[stop_times["trip_id"].isin(group["trip_id"])]
        counts = candidates.groupby("trip_id").size()
        trip_id = counts.sort_values(ascending=False).index[0]
        sequence = (
            stop_times[stop_times["trip_id"] == trip_id]
            .sort_values("stop_sequence")
            .merge(stops[["stop_id", "stop_name", "stop_lon", "stop_lat"]], on="stop_id")
        )
        route = routes[routes["route_id"] == route_id].iloc[0]
        records.append({
            "route_id": route_id,
            "route_name": route["route_long_name"],
            "colour": COLOURS.get(route_id, "#666666"),
            "geometry": LineString(zip(sequence["stop_lon"], sequence["stop_lat"])),
        })

    lines = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    stations = gpd.GeoDataFrame(
        stops,
        geometry=gpd.points_from_xy(stops["stop_lon"], stops["stop_lat"]),
        crs="EPSG:4326",
    )
    return lines, stations


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "pdf.fonttype": 42,
    })

    tpu = gpd.read_file(INPUTS / "tpu_geography_v3.gpkg").to_crs(4326)
    tpu["TPU"] = tpu["TPU"].astype(str).str.strip()
    access = pd.read_csv(RESULTS / "accessibility_tpu_v3.csv", dtype={"area_id": str})
    tpu_all = tpu.merge(access, left_on="TPU", right_on="area_id", how="left", validate="one_to_one")
    tpu_routed = tpu_all.dropna(subset=["min_tt"]).copy()

    bcp_raw = pd.read_csv(INPUTS / "bcp_destination_provenance_v3.csv", dtype={"source_stop_id": str})
    bcp = gpd.GeoDataFrame(
        bcp_raw,
        geometry=gpd.points_from_xy(bcp_raw["lon"], bcp_raw["lat"]),
        crs="EPSG:4326",
    )
    lines, stations = representative_lines()

    fig, ax = plt.subplots(figsize=(7.2, 5.3))
    tpu_all.plot(ax=ax, color="#D9D9D9", edgecolor="white", linewidth=0.18, zorder=1)
    tpu_routed.plot(
        ax=ax,
        column="min_tt",
        cmap="viridis_r",
        vmin=20,
        vmax=115,
        edgecolor="white",
        linewidth=0.18,
        zorder=2,
    )

    for row in lines.itertuples():
        is_east_rail = row.route_id in {"MTR_EAL", "MTR_EAL_LMC"}
        width = 2.0 if is_east_rail else 0.9
        alpha = 0.95 if is_east_rail else 0.72
        gpd.GeoSeries([row.geometry], crs=lines.crs).plot(
            ax=ax, color="white", linewidth=width + 1.0, alpha=0.8, zorder=3
        )
        gpd.GeoSeries([row.geometry], crs=lines.crs).plot(
            ax=ax, color=row.colour, linewidth=width, alpha=alpha, zorder=4
        )

    stations.plot(ax=ax, color="white", edgecolor="#444444", linewidth=0.25, markersize=4, zorder=5)
    sheung_shui = stations[stations["stop_id"] == "MTR_SHS"]
    if not sheung_shui.empty:
        point = sheung_shui.iloc[0].geometry
        ax.annotate(
            "Sheung Shui",
            (point.x, point.y),
            xytext=(-34, -12),
            textcoords="offset points",
            fontsize=6,
            color="#333333",
            fontweight="bold",
            zorder=8,
        )

    offsets = {
        "SB": (-17, 8), "HG": (-14, -13), "LMC": (-22, 8),
        "LW": (-6, 9), "MKT": (3, 8), "HYW": (4, -12),
    }
    for row in bcp.itertuples():
        ax.plot(
            row.geometry.x,
            row.geometry.y,
            "^",
            color="#A93226",
            markersize=5.5,
            markeredgecolor="white",
            markeredgewidth=0.4,
            zorder=7,
        )
        ax.annotate(
            row.id,
            (row.geometry.x, row.geometry.y),
            xytext=offsets[row.id],
            textcoords="offset points",
            fontsize=6,
            color="#7B241C",
            fontweight="bold",
            zorder=8,
        )

    sm = mpl.cm.ScalarMappable(norm=Normalize(20, 115), cmap="viridis_r")
    cbar = fig.colorbar(sm, ax=ax, fraction=0.026, pad=0.015)
    cbar.set_label("Minimum travel time (minutes)")
    ax.legend(
        handles=[
            Line2D([0], [0], marker="^", linestyle="none", markerfacecolor="#A93226",
                   markeredgecolor="white", label="Operational land BCP"),
            Line2D([0], [0], color="#53B7E8", linewidth=2.2, label="East Rail branches"),
            Line2D([0], [0], color="#777777", linewidth=1.0, label="Other analytical MTR lines"),
        ],
        loc="lower left",
        frameon=True,
        facecolor="white",
        framealpha=0.88,
        fontsize=6.5,
    )
    ax.set_axis_off()
    ax.set_aspect("equal")
    ax.set_title("Minimum transit time and the analytical MTR network", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT / "figure_min_tt_with_mtr.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT / "figure_min_tt_with_mtr.pdf", bbox_inches="tight")
    plt.close(fig)

    with (OUTPUT / "figure_min_tt_with_mtr_provenance.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["asset", "source"])
        writer.writerow(["TPU geography", str((INPUTS / "tpu_geography_v3.gpkg").relative_to(ROOT))])
        writer.writerow(["Accessibility", str((RESULTS / "accessibility_tpu_v3.csv").relative_to(ROOT))])
        writer.writerow(["MTR network", str(GTFS.relative_to(ROOT))])
        writer.writerow(["BCPs", str((INPUTS / "bcp_destination_provenance_v3.csv").relative_to(ROOT))])

    print(OUTPUT / "figure_min_tt_with_mtr.png")


if __name__ == "__main__":
    main()
