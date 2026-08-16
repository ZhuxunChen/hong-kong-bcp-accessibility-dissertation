#!/usr/bin/env python3
"""Generate seven publication-ready candidate figures from frozen Stage 9A outputs."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch, Rectangle
import numpy as np
import pandas as pd
from libpysal.weights import Queen, lag_spatial
from scipy import stats
import statsmodels.api as sm


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "reference_outputs" / "stage9a"
INPUTS = STAGE / "inputs"
RESULTS = STAGE / "results"
OUT = Path(__file__).resolve().parent / "results"
SOURCE = OUT / "source_data"
SOURCE.mkdir(parents=True, exist_ok=True)

BLUE = "#0072B2"
SKY = "#56B4E9"
ORANGE = "#D55E00"
GREEN = "#009E73"
YELLOW = "#E69F00"
PURPLE = "#CC79A7"
INK = "#252525"
MID = "#777777"
LIGHT = "#D9D9D9"
PALE = "#F3F3F3"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
})


def export(fig: mpl.figure.Figure, stem: str) -> None:
    for suffix, kwargs in (
        ("png", {"dpi": 400}),
        ("pdf", {}),
        ("svg", {}),
    ):
        fig.savefig(OUT / f"{stem}.{suffix}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def panel_label(ax, label: str) -> None:
    ax.text(-0.04, 1.03, label, transform=ax.transAxes, fontsize=9,
            fontweight="bold", ha="left", va="bottom")


def map_finish(ax) -> None:
    ax.set_axis_off()
    ax.set_aspect("equal")


def add_scale_north(ax, length_m: float = 10000) -> None:
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x0 = xmin + 0.05 * (xmax - xmin)
    y0 = ymin + 0.055 * (ymax - ymin)
    ax.plot([x0, x0 + length_m], [y0, y0], color=INK, linewidth=2.0, solid_capstyle="butt")
    ax.plot([x0, x0], [y0 - 500, y0 + 500], color=INK, linewidth=0.8)
    ax.plot([x0 + length_m, x0 + length_m], [y0 - 500, y0 + 500], color=INK, linewidth=0.8)
    ax.text(x0 + length_m / 2, y0 + 1000, "10 km", ha="center", va="bottom", fontsize=7)
    ax.annotate("N", xy=(0.95, 0.88), xytext=(0.95, 0.73), xycoords="axes fraction",
                textcoords="axes fraction", ha="center", va="bottom", fontsize=8,
                fontweight="bold", arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))


def project_point(lon: float, lat: float) -> tuple[float, float]:
    point = gpd.GeoSeries(gpd.points_from_xy([lon], [lat]), crs=4326).to_crs(2326).iloc[0]
    return point.x, point.y


# Frozen inputs.
tpu_geo = gpd.read_file(INPUTS / "tpu_geography_v3.gpkg")
tpu_geo["TPU"] = tpu_geo["TPU"].astype(str).str.strip()
stpug_geo = gpd.read_file(INPUTS / "stpug_geography_v3.gpkg")
stpug_geo["stpug_id"] = stpug_geo["stpug_id"].astype(str).str.strip()
access = pd.read_csv(RESULTS / "accessibility_tpu_v3.csv", dtype={"area_id": str})
analysis = pd.read_csv(RESULTS / "analysis_stpug_v3.csv", dtype={"stpug_id": str})
bcp_raw = pd.read_csv(INPUTS / "bcp_destination_provenance_v3.csv")
bcp = gpd.GeoDataFrame(
    bcp_raw,
    geometry=gpd.points_from_xy(bcp_raw["lon"], bcp_raw["lat"]),
    crs=4326,
)
tpu_map = tpu_geo.to_crs(2326)
stpug_map = stpug_geo.to_crs(2326)
bcp_map = bcp.to_crs(2326)
tpu_map_display = tpu_map.copy()
tpu_map_display["geometry"] = tpu_map_display.geometry.simplify(25, preserve_topology=True)
stpug_map_display = stpug_map.copy()
stpug_map_display["geometry"] = stpug_map_display.geometry.simplify(25, preserve_topology=True)


# Figure A: study area locator.
fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.7), gridspec_kw={"width_ratios": [1.28, 1]})
for ax in axes:
    tpu_map_display.plot(ax=ax, facecolor="#F4F4F4", edgecolor="#BDBDBD", linewidth=0.20)
    tpu_map_display.dissolve().boundary.plot(ax=ax, color=INK, linewidth=0.72)

code_offsets = {
    "SB": (-15, 8), "HG": (-10, -13), "LMC": (-22, 8),
    "LW": (-3, -14), "MKT": (2, 7), "HYW": (3, 8),
}
for row in bcp_map.itertuples():
    axes[0].plot(row.geometry.x, row.geometry.y, marker="^", markersize=5.8,
                 color=ORANGE, markeredgecolor="white", markeredgewidth=0.45, zorder=5)
    axes[0].annotate(row.id, xy=(row.geometry.x, row.geometry.y), xytext=code_offsets[row.id],
                     textcoords="offset points", fontsize=6.4, color=INK,
                     fontweight="bold", zorder=6)

label_offsets = {
    "SB": (-68, 4), "HG": (-77, -18), "LMC": (-83, 19),
    "LW": (8, -25), "MKT": (10, 22), "HYW": (10, 30),
}
for row in bcp_map.itertuples():
    axes[1].plot(row.geometry.x, row.geometry.y, marker="^", markersize=6.5,
                 color=ORANGE, markeredgecolor="white", markeredgewidth=0.5, zorder=5)
    ox, oy = label_offsets[row.id]
    axes[1].annotate(f"{row.id}  {row.bcp_name}", xy=(row.geometry.x, row.geometry.y),
                     xytext=(ox, oy), textcoords="offset points", fontsize=6.5,
                     color=INK, fontweight="bold", zorder=6,
                     arrowprops=dict(arrowstyle="-", color="#777777", lw=0.55))

regional_labels = [
    (114.10, 22.60, "SHENZHEN", 8, "#777777"),
    (114.08, 22.40, "New Territories", 8, "#666666"),
    (114.17, 22.32, "Kowloon", 7, "#777777"),
    (114.18, 22.255, "Hong Kong Island", 7, "#777777"),
    (113.96, 22.275, "Lantau Island", 7, "#777777"),
]
for lon, lat, text, size, color in regional_labels[1:]:
    x, y = project_point(lon, lat)
    axes[0].text(x, y, text, ha="center", va="center", fontsize=size, color=color)

axes[0].set_title("Territory-wide TPU origins", loc="left", fontweight="bold")
panel_label(axes[0], "a")
add_scale_north(axes[0])
bxmin, bymin, bxmax, bymax = bcp_map.total_bounds
axes[1].set_xlim(bxmin - 24000, bxmax + 26000)
axes[1].set_ylim(bymin - 19000, bymax + 15000)
sx, sy = project_point(114.05, 22.575)
axes[1].text(sx, sy, "SHENZHEN", fontsize=8, color=MID, fontweight="bold", ha="center")
axes[1].set_title("Northern boundary detail", loc="left", fontweight="bold")
panel_label(axes[1], "b")
for ax in axes:
    map_finish(ax)
fig.suptitle("Study area and six operational land boundary control points", fontsize=10, fontweight="bold")
fig.text(0.5, 0.015, "BCP positions are anchored to retained transport-feed stops; Shenzhen is shown for geographic context.",
         ha="center", va="bottom", fontsize=6.8, color=MID)
fig.tight_layout(rect=[0, 0.04, 1, 0.94])
export(fig, "figure_A_study_area")
bcp_raw[["id", "bcp_name", "source_feed", "source_stop_id", "lon", "lat"]].to_csv(
    SOURCE / "figure_A_study_area.csv", index=False
)


# Figure B: workflow.
fig, ax = plt.subplots(figsize=(7.2, 4.4))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")


def box(x, y, w, h, title, body, face, edge=INK, title_color=INK):
    rect = Rectangle((x, y), w, h, facecolor=face, edgecolor=edge, linewidth=0.8)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h * 0.67, title, ha="center", va="center",
            fontsize=8, fontweight="bold", color=title_color)
    ax.text(x + w / 2, y + h * 0.30, body, ha="center", va="center",
            fontsize=6.7, color=INK, linespacing=1.25)
    return rect


def arrow(x1, y1, x2, y2, color=MID):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=9, lw=0.9, color=color,
                                 shrinkA=2, shrinkB=2))


box(0.03, 0.63, 0.20, 0.22, "Origin geographies", "292 TPUs\n211 census STPUGs", "#EAF2F8", BLUE)
box(0.29, 0.63, 0.19, 0.22, "Destinations", "6 operational\nland BCPs", "#FDEDEC", ORANGE)
box(0.54, 0.63, 0.19, 0.22, "Repeated routing", "5 r5r runs\nMonday 09:00", "#E8F6F3", GREEN)
box(0.79, 0.63, 0.18, 0.22, "Stable aggregate", "OD present in >=3 runs\nacross-run median", "#FCF3CF", YELLOW)
for x1, x2 in ((0.23, 0.29), (0.48, 0.54), (0.73, 0.79)):
    arrow(x1, 0.74, x2, 0.74)

box(0.28, 0.32, 0.20, 0.18, "Place sample", "209 stable TPUs\nof 292 submitted", "#EAF2F8", BLUE)
box(0.53, 0.32, 0.20, 0.18, "Model sample", "176 stable STPUGs\nof 211 submitted", "#EAF2F8", BLUE)
arrow(0.88, 0.63, 0.43, 0.50)
arrow(0.88, 0.63, 0.63, 0.50)

box(0.06, 0.05, 0.25, 0.16, "Inequality", "levels, Gini, thresholds\nand sensitivity", "#F4ECF7", PURPLE)
box(0.375, 0.05, 0.25, 0.16, "Spatial pattern", "global Moran's I, FDR LISA\nand omitted-origin maps", "#F4ECF7", PURPLE)
box(0.69, 0.05, 0.25, 0.16, "Socioeconomic association", "OLS, SAR, SEM, KNN5\nand exploratory GWR", "#F4ECF7", PURPLE)
arrow(0.38, 0.32, 0.19, 0.21)
arrow(0.38, 0.32, 0.50, 0.21)
arrow(0.63, 0.32, 0.815, 0.21)
ax.set_title("From transport inputs to three analytical evidence branches", loc="left", fontweight="bold", pad=10)
fig.tight_layout()
export(fig, "figure_B_workflow")
pd.DataFrame([
    ("Submitted TPU origins", 292), ("Submitted STPUG origins", 211),
    ("Routing runs", 5), ("Minimum runs for stable OD", 3),
    ("Stable TPU origins", 209), ("Stable STPUG origins", 176),
    ("Operational land BCPs", 6),
], columns=["stage", "count"]).to_csv(SOURCE / "figure_B_workflow.csv", index=False)


# Figure C: routed and omitted samples.
tpu_stable = set(access["area_id"].astype(str))
tpu_omit = pd.read_csv(RESULTS / "omitted_origin_audit_tpu_v3.csv", dtype={"id": str})
tpu_status = tpu_geo[["TPU", "geometry"]].copy()
tpu_status["status"] = np.where(tpu_status["TPU"].isin(tpu_stable), "Stable route", "Omitted")
tpu_status = tpu_status.merge(tpu_omit[["id", "classification"]], left_on="TPU", right_on="id", how="left")
tpu_status.loc[tpu_status["classification"] == "requires_snap_radius_over_1600m", "status"] = "Snap distance >1,600 m"
tpu_status = tpu_status.to_crs(2326)
tpu_status["geometry"] = tpu_status.geometry.simplify(25, preserve_topology=True)

stpug_stable = set(analysis["stpug_id"].astype(str))
stpug_status = stpug_geo[["stpug_id", "geometry"]].copy()
stpug_status["status"] = np.where(stpug_status["stpug_id"].isin(stpug_stable), "Stable route", "No stable route <=120 min")
stpug_status = stpug_status.to_crs(2326)
stpug_status["geometry"] = stpug_status.geometry.simplify(25, preserve_topology=True)

status_colors = {
    "Stable route": BLUE,
    "Omitted": ORANGE,
    "No stable route <=120 min": ORANGE,
    "Snap distance >1,600 m": "#8C8C8C",
}
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.5))
for ax, frame, id_col, title in (
    (axes[0], tpu_status, "TPU", "TPU origins"),
    (axes[1], stpug_status, "stpug_id", "Census STPUG origins"),
):
    for status, color in status_colors.items():
        subset = frame[frame["status"] == status]
        if len(subset):
            subset.plot(ax=ax, facecolor=color, edgecolor="white", linewidth=0.16)
    map_finish(ax)
    ax.set_title(title, loc="left", fontweight="bold")
panel_label(axes[0], "a")
panel_label(axes[1], "b")
axes[0].text(0.02, 0.02, "209 stable / 79 no stable route / 4 snap-distance omissions",
             transform=axes[0].transAxes, fontsize=6.6,
             bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2))
pop_coverage = analysis["population"].sum() / pd.read_csv(INPUTS / "census_stpug_v3.csv")["population"].sum()
axes[1].text(0.02, 0.02, f"176 stable / 35 omitted; {pop_coverage:.1%} population coverage",
             transform=axes[1].transAxes, fontsize=6.6,
             bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2))
handles = [
    Patch(facecolor=BLUE, label="Stable route"),
    Patch(facecolor=ORANGE, label="Snapped but no stable route <=120 min"),
    Patch(facecolor="#8C8C8C", label="TPU snap distance >1,600 m"),
]
fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.01), fontsize=7)
fig.suptitle("Stable-routing sample retention is geographically patterned", fontsize=10, fontweight="bold")
fig.tight_layout(rect=[0, 0.06, 1, 0.94])
export(fig, "figure_C_sample_retention")
pd.DataFrame([
    ("TPU", "Stable route", 209, 292, 209 / 292),
    ("TPU", "No stable route <=120 min", 79, 292, 79 / 292),
    ("TPU", "Snap distance >1,600 m", 4, 292, 4 / 292),
    ("STPUG", "Stable route", 176, 211, 176 / 211),
    ("STPUG", "No stable route <=120 min", 35, 211, 35 / 211),
], columns=["grain", "status", "n", "total", "share"]).to_csv(SOURCE / "figure_C_sample_retention.csv", index=False)


# Figure D: cumulative access curve.
thresholds = np.arange(20, 121)
tpu_curve = np.array([(access["min_tt"] <= threshold).mean() for threshold in thresholds])
population_total = analysis["population"].sum()
population_curve = np.array([
    analysis.loc[analysis["min_tt"] <= threshold, "population"].sum() / population_total
    for threshold in thresholds
])
fig, ax = plt.subplots(figsize=(6.4, 3.9))
ax.plot(thresholds, tpu_curve * 100, color=BLUE, linewidth=2.0, label="Stable TPUs (n=209)")
ax.plot(thresholds, population_curve * 100, color=ORANGE, linewidth=1.8, linestyle="--",
        label="Covered STPUG population (6.81 million)")
for threshold in (45, 60, 75, 90):
    ax.axvline(threshold, color="#C7C7C7", linewidth=0.65, zorder=0)
    ax.text(threshold, 2, str(threshold), ha="center", va="bottom", fontsize=6.5, color=MID)
idx60 = int(np.where(thresholds == 60)[0][0])
for value, color, dy in ((tpu_curve[idx60], BLUE, 5), (population_curve[idx60], ORANGE, -8)):
    ax.scatter([60], [value * 100], color=color, s=25, edgecolor="white", linewidth=0.4, zorder=4)
    ax.annotate(f"{value:.1%}", (60, value * 100), xytext=(8, dy), textcoords="offset points",
                color=color, fontsize=7, fontweight="bold")
ax.set_xlim(20, 120)
ax.set_ylim(0, 102)
ax.set_xlabel("Scheduled travel time to nearest operational BCP (minutes)")
ax.set_ylabel("Cumulative share within threshold (%)")
ax.grid(axis="y", alpha=0.18, linewidth=0.6)
ax.legend(loc="lower right")
ax.set_title("Most stable-routed origins remain beyond a 60-minute journey", loc="left", fontweight="bold")
fig.tight_layout()
export(fig, "figure_D_cumulative_access")
pd.DataFrame({
    "threshold_minutes": thresholds,
    "tpu_equal_share": tpu_curve,
    "covered_population_share": population_curve,
}).to_csv(SOURCE / "figure_D_cumulative_access.csv", index=False)


# Figure E: BCP profile.
matrix = pd.read_csv(RESULTS / "travel_time_matrix_tpu_v3.csv", dtype={"from_id": str})
bcp_order = bcp_raw["id"].tolist()
bcp_names = dict(zip(bcp_raw["id"], bcp_raw["bcp_name"]))
nearest_counts = access["nearest_bcp"].value_counts()
profile_rows = []
for code in bcp_order:
    subset = matrix[matrix["to_id"] == code]
    profile_rows.append({
        "bcp": code,
        "bcp_name": bcp_names[code],
        "valid_od_n": len(subset),
        "within_60_share_all_stable_tpus": (subset["travel_time_p50"] <= 60).sum() / len(access),
        "nearest_share_all_stable_tpus": nearest_counts.get(code, 0) / len(access),
        "median_valid_od_minutes": subset["travel_time_p50"].median(),
    })
profile = pd.DataFrame(profile_rows).sort_values("median_valid_od_minutes", ascending=False).reset_index(drop=True)
y = np.arange(len(profile))
fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.25), gridspec_kw={"width_ratios": [1.25, 1]})
axes[0].barh(y + 0.16, profile["within_60_share_all_stable_tpus"] * 100, height=0.30,
             color=BLUE, label="Reachable within 60 min")
axes[0].barh(y - 0.16, profile["nearest_share_all_stable_tpus"] * 100, height=0.30,
             color=ORANGE, label="Nearest BCP")
axes[0].set_yticks(y, [f"{r.bcp}  {r.bcp_name}" for r in profile.itertuples()])
axes[0].set_xlabel("Share of 209 stable TPUs (%)")
axes[0].grid(axis="x", alpha=0.18, linewidth=0.6)
axes[0].legend(loc="lower right", fontsize=6.8)
axes[0].set_xlim(0, max(45, (profile[["within_60_share_all_stable_tpus", "nearest_share_all_stable_tpus"]].max().max() * 100 + 7)))
axes[1].hlines(y, 0, profile["median_valid_od_minutes"], color="#C7C7C7", linewidth=1.1)
axes[1].scatter(profile["median_valid_od_minutes"], y, s=38, color=GREEN,
                edgecolor="white", linewidth=0.5, zorder=3)
for yi, row in enumerate(profile.itertuples()):
    axes[1].text(row.median_valid_od_minutes + 2, yi,
                 f"{row.median_valid_od_minutes:.0f} min  (n={row.valid_od_n})",
                 va="center", fontsize=6.7, color=INK)
axes[1].set_yticks(y, [])
axes[1].set_xlabel("Median time among valid routed OD pairs (minutes)")
axes[1].set_xlim(0, profile["median_valid_od_minutes"].max() + 35)
axes[1].grid(axis="x", alpha=0.18, linewidth=0.6)
panel_label(axes[0], "a")
panel_label(axes[1], "b")
fig.suptitle("The six BCP opportunities have unequal network reach", fontsize=10, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.94])
export(fig, "figure_E_bcp_profile")
profile.to_csv(SOURCE / "figure_E_bcp_profile.csv", index=False)


# Figure F: Moran scatterplots.
tpu_spatial = tpu_geo.merge(access, left_on="TPU", right_on="area_id", validate="one_to_one")
tpu_spatial = tpu_spatial.reset_index(drop=True)
queen = Queen.from_dataframe(tpu_spatial, use_index=False)
queen.transform = "r"
spatial_metrics = pd.read_csv(RESULTS / "figures_and_spatial" / "spatial_metrics_v3.csv").set_index("variable")
fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.05))
moran_source = []
for ax, variable, label, color in (
    (axes[0], "min_tt", "Minimum travel-time burden", ORANGE),
    (axes[1], "bcps_within_60", "BCPs reachable within 60 minutes", BLUE),
):
    z = stats.zscore(tpu_spatial[variable].to_numpy(dtype=float))
    wz = lag_spatial(queen, z)
    slope, intercept = np.polyfit(z, wz, 1)
    xline = np.linspace(z.min(), z.max(), 100)
    ax.axhline(0, color="#AAAAAA", lw=0.65)
    ax.axvline(0, color="#AAAAAA", lw=0.65)
    ax.scatter(z, wz, s=16, color=color, alpha=0.58, edgecolor="white", linewidth=0.25)
    ax.plot(xline, intercept + slope * xline, color=INK, linewidth=1.2)
    metric = spatial_metrics.loc[variable]
    ax.text(0.97, 0.04, f"Moran's I = {metric.moran_i:.4f}\np = {metric.p_permutation:.3f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, pad=2))
    ax.set_title(label, loc="left", fontweight="bold")
    ax.set_xlabel("Standardized value")
    ax.set_ylabel("Queen spatial lag")
    ax.grid(alpha=0.12, linewidth=0.5)
    for area_id, value, lag in zip(tpu_spatial["TPU"], z, wz):
        moran_source.append((variable, area_id, value, lag))
panel_label(axes[0], "a")
panel_label(axes[1], "b")
fig.suptitle("Both accessibility dimensions are strongly spatially clustered", fontsize=10, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.94])
export(fig, "figure_F_moran_scatter")
pd.DataFrame(moran_source, columns=["variable", "TPU", "standardized_value", "queen_spatial_lag"]).to_csv(
    SOURCE / "figure_F_moran_scatter.csv", index=False
)


# Figure G: coefficient transition and residual spatial dependence.
model = pd.read_csv(RESULTS / "model_comparison_stpug_v3.csv")
details = json.loads((RESULTS / "stage9a_results_v3.json").read_text())["model_details"]
X = pd.DataFrame({
    "income": stats.zscore(analysis["median_hh_income"].to_numpy(dtype=float)),
    "density": stats.zscore(analysis["pop_density_km2"].to_numpy(dtype=float)),
})
ols = sm.OLS(analysis["min_tt"].to_numpy(dtype=float), sm.add_constant(X)).fit(cov_type="HC3")
if not np.isclose(ols.params["income"], details["ols_income_beta"], atol=1e-8):
    raise ValueError("HC3 OLS reconstruction does not match frozen Stage 9A coefficient")

coef_rows = [
    ("OLS (HC3)", "Income", ols.params["income"], ols.bse["income"], details["ols_income_hc3_p"]),
    ("OLS (HC3)", "Population density", ols.params["density"], ols.bse["density"], details["ols_density_hc3_p"]),
    ("SEM Queen", "Income", details["sem_queen_income_beta"], details["sem_queen_income_se"], details["sem_queen_income_p"]),
    ("SEM Queen", "Population density", details["sem_queen_density_beta"], details["sem_queen_density_se"], details["sem_queen_density_p"]),
    ("SEM KNN5", "Income", details["sem_knn5_income_beta"], details["sem_knn5_income_se"], details["sem_knn5_income_p"]),
    ("SEM KNN5", "Population density", details["sem_knn5_density_beta"], details["sem_knn5_density_se"], details["sem_knn5_density_p"]),
]
coef = pd.DataFrame(coef_rows, columns=["model", "term", "beta", "se", "p"])
coef["lower_95"] = coef["beta"] - 1.96 * coef["se"]
coef["upper_95"] = coef["beta"] + 1.96 * coef["se"]

fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.15), gridspec_kw={"width_ratios": [1.35, 1]})
models = ["OLS (HC3)", "SEM Queen", "SEM KNN5"]
ybase = np.arange(len(models))[::-1]
for term, color, offset in (("Income", ORANGE, 0.12), ("Population density", BLUE, -0.12)):
    sub = coef.set_index(["model", "term"]).loc[[(m, term) for m in models]].reset_index()
    ypos = ybase + offset
    axes[0].errorbar(sub["beta"], ypos,
                     xerr=[sub["beta"] - sub["lower_95"], sub["upper_95"] - sub["beta"]],
                     fmt="o", color=color, ecolor=color, markersize=5, capsize=2.5,
                     linewidth=1.2, label=term)
axes[0].axvline(0, color="#888888", linestyle="--", linewidth=0.8)
axes[0].set_yticks(ybase, models)
axes[0].set_xlabel("Travel-time coefficient (minutes per SD; 95% CI)")
axes[0].grid(axis="x", alpha=0.16, linewidth=0.6)
axes[0].legend(loc="lower right", fontsize=6.8)
axes[0].set_title("Spatial filtering changes the coefficient story", loc="left", fontweight="bold")

residual = model[model["model"].isin(["OLS", "SAR Queen", "SEM Queen", "SEM KNN5", "GWR"])].copy()
residual["display"] = residual["model"].replace({"OLS": "OLS (HC3)", "GWR": "GWR (exploratory)"})
residual = residual.iloc[::-1]
colors = [GREEN if name.startswith("SEM") else MID for name in residual["display"]]
for yi, row, color in zip(range(len(residual)), residual.itertuples(), colors):
    axes[1].hlines(yi, 0, row.filtered_or_residual_moran_i, color="#C7C7C7", linewidth=1.0)
    face = color if row.moran_p < 0.05 else "white"
    axes[1].scatter(row.filtered_or_residual_moran_i, yi, s=46, facecolor=face,
                    edgecolor=color, linewidth=1.2, zorder=3)
    axes[1].text(row.filtered_or_residual_moran_i + 0.025, yi,
                 f"{row.filtered_or_residual_moran_i:.3f}",
                 ha="left", va="center", fontsize=6.6)
axes[1].axvline(0, color="#888888", linestyle="--", linewidth=0.8)
axes[1].set_yticks(range(len(residual)), residual["display"])
axes[1].set_xlabel("Residual or filtered Moran's I")
axes[1].set_xlim(-0.17, 0.75)
axes[1].grid(axis="x", alpha=0.16, linewidth=0.6)
axes[1].set_title("Residual spatial dependence is reduced", loc="left", fontweight="bold")
axes[1].text(0.98, 0.02, "Filled marker: p < 0.05", transform=axes[1].transAxes,
             ha="right", va="bottom", fontsize=6.5, color=MID)
panel_label(axes[0], "a")
panel_label(axes[1], "b")
fig.suptitle("Spatial models separate contextual association from spatial structure", fontsize=10, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.94])
export(fig, "figure_G_model_transition")
coef.to_csv(SOURCE / "figure_G_model_coefficients.csv", index=False)
residual[["display", "filtered_or_residual_moran_i", "moran_p"]].to_csv(
    SOURCE / "figure_G_residual_moran.csv", index=False
)

print("Generated seven candidate figures with PNG, PDF, SVG and source-data exports.")
