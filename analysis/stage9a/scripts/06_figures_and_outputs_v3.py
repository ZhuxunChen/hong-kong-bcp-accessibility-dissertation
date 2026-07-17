#!/usr/bin/env python3
"""Generate Stage 9A figures and spatial diagnostics without fixed sample sizes."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, Normalize, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from esda.moran import Moran, Moran_Local
from libpysal.weights import Queen
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from scipy import stats
from statsmodels.stats.multitest import multipletests


warnings.filterwarnings("ignore")
SEED = 42
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "analysis" / "stage9a" / "results"
INPUTS = ROOT / "analysis" / "stage9a" / "inputs"
OUTPUT = SOURCE / "figures_and_spatial"

OUTPUT_FILES = [
    OUTPUT / "inequality_metrics_v3.csv",
    OUTPUT / "spatial_metrics_v3.csv",
    OUTPUT / "lisa_counts_v3.csv",
    OUTPUT / "lisa_assignments_tpu_v3.csv",
    OUTPUT / "gwr_local_results_stpug_v3.csv",
    OUTPUT / "gwr_local_results_stpug_v3.gpkg",
    OUTPUT / "stage9a_spatial_results_v3.json",
    *[OUTPUT / f"fig{i}_v3.{ext}" for i in range(1, 7) for ext in ("png", "pdf")],
    OUTPUT / "fig_threshold_sensitivity_v3.png",
    OUTPUT / "fig_threshold_sensitivity_v3.pdf",
]
existing = [path for path in OUTPUT_FILES if path.exists()]
if existing:
    raise FileExistsError(f"Refusing to overwrite Stage 9A figure outputs: {existing}")
OUTPUT.mkdir(parents=True, exist_ok=True)

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
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})


def gini(values: np.ndarray, weights: np.ndarray | None = None) -> float:
    x = np.asarray(values, dtype=float)
    w = np.ones_like(x) if weights is None else np.asarray(weights, dtype=float)
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[mask], w[mask]
    order = np.argsort(x, kind="stable")
    x, w = x[order], w[order]
    total = np.sum(x * w)
    if total == 0:
        return 0.0
    cum_w = np.insert(np.cumsum(w) / np.sum(w), 0, 0.0)
    cum_x = np.insert(np.cumsum(x * w) / total, 0, 0.0)
    return float(1 - 2 * np.trapezoid(cum_x, cum_w))


def lorenz_points(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.sort(np.asarray(values, dtype=float))
    cumulative = np.cumsum(x)
    y = cumulative / cumulative[-1] if cumulative[-1] else np.zeros_like(cumulative)
    return np.insert(np.arange(1, len(x) + 1) / len(x), 0, 0), np.insert(y, 0, 0)


def summary(values: pd.Series) -> dict[str, float]:
    x = values.to_numpy(dtype=float)
    q = np.quantile(x, [0.10, 0.25, 0.50, 0.75, 0.90])
    return {
        "n": int(len(x)), "minimum": float(x.min()), "maximum": float(x.max()),
        "mean": float(x.mean()), "sd": float(x.std(ddof=1)),
        "p10": float(q[0]), "p25": float(q[1]), "median": float(q[2]),
        "p75": float(q[3]), "p90": float(q[4]), "gini": gini(x),
        "zero_count": int((x == 0).sum()), "zero_share": float((x == 0).mean()),
    }


def weighted_summary(values: pd.Series, population: pd.Series) -> dict[str, float]:
    x = values.to_numpy(dtype=float)
    w = population.to_numpy(dtype=float)
    order = np.argsort(x, kind="stable")
    x, w = x[order], w[order]
    quantiles = []
    for q in (0.10, 0.25, 0.50, 0.75, 0.90):
        quantiles.append(float(x[np.searchsorted(np.cumsum(w), q * w.sum(), side="left")]))
    mean = float(np.average(x, weights=w))
    return {
        "n": int(len(x)), "population": int(w.sum()),
        "minimum": float(x.min()), "maximum": float(x.max()), "mean": mean,
        "sd": float(np.sqrt(np.average((x - mean) ** 2, weights=w))),
        "p10": quantiles[0], "p25": quantiles[1], "median": quantiles[2],
        "p75": quantiles[3], "p90": quantiles[4], "gini": gini(x, w),
        "zero_count": int((x == 0).sum()),
        "zero_share": float(w[x == 0].sum() / w.sum()),
    }


def finish_map(ax, show_legend: bool = True) -> None:
    ax.set_axis_off()
    ax.set_aspect("equal")
    if show_legend:
        ax.legend(
            handles=[Line2D([0], [0], marker="^", linestyle="none",
                            markerfacecolor="#A93226", markeredgecolor="white",
                            label="Operational land BCP")],
            loc="lower left", frameon=False, fontsize=7,
        )


def add_bcps(ax, bcp: gpd.GeoDataFrame) -> None:
    offsets = {
        "SB": (-17, 8), "HG": (-14, -13), "LMC": (-22, 8),
        "LW": (-6, 9), "MKT": (3, 8), "HYW": (4, -12),
    }
    for row in bcp.itertuples():
        ax.plot(row.geometry.x, row.geometry.y, "^", color="#A93226", markersize=5.5,
                markeredgecolor="white", markeredgewidth=0.4, zorder=6)
        ax.annotate(
            row.id, (row.geometry.x, row.geometry.y), xytext=offsets[row.id],
            textcoords="offset points", fontsize=6, color="#7B241C",
            fontweight="bold", zorder=7,
        )


# Load stable Stage 9A geography and accessibility.
tpu = gpd.read_file(INPUTS / "tpu_geography_v3.gpkg").to_crs(4326)
tpu["TPU"] = tpu["TPU"].astype(str).str.strip()
access = pd.read_csv(SOURCE / "accessibility_tpu_v3.csv", dtype={"area_id": str})
if access.empty or access["area_id"].duplicated().any():
    raise ValueError("Stage 9A TPU accessibility must contain unique rows")
tpu_all = tpu.merge(access, left_on="TPU", right_on="area_id", how="left", validate="one_to_one")
tpu_routed = tpu_all.dropna(subset=["min_tt"]).copy().reset_index(drop=True)
if len(tpu_routed) != len(access):
    raise ValueError("Stage 9A TPU geography join changed row count")

bcp_raw = pd.read_csv(INPUTS / "bcp_destination_provenance_v3.csv", dtype={"source_stop_id": str})
bcp = gpd.GeoDataFrame(
    bcp_raw, geometry=gpd.points_from_xy(bcp_raw["lon"], bcp_raw["lat"]), crs="EPSG:4326"
)

# Place-based inequality and threshold outputs.
metric_rows = []
for variable in ["min_tt", "bcps_within_45", "bcps_within_60", "bcps_within_75", "bcps_within_90"]:
    values = summary(tpu_routed[variable])
    metric_rows.append({"grain": "TPU", "weighting": "equal", "variable": variable, **values})

# STPUG data and population-weighted complementary results.
stpug_csv = pd.read_csv(SOURCE / "analysis_stpug_v3.csv", dtype={"stpug_id": str})
stpug_geo = gpd.read_file(INPUTS / "stpug_geography_v3.gpkg")
stpug_geo["stpug_id"] = stpug_geo["stpug_id"].astype(str)
stpug = stpug_csv.merge(
    stpug_geo[["stpug_id", "geometry"]], on="stpug_id", validate="one_to_one"
)
stpug = gpd.GeoDataFrame(stpug, geometry="geometry", crs=stpug_geo.crs)
if len(stpug) != len(stpug_csv):
    raise ValueError("Stage 9A STPUG geography join changed row count")
for variable in ["min_tt", "bcps_within_45", "bcps_within_60", "bcps_within_75", "bcps_within_90"]:
    values = weighted_summary(stpug[variable], stpug["population"])
    metric_rows.append({"grain": "STPUG", "weighting": "population", "variable": variable, **values})
metrics = pd.DataFrame(metric_rows)
metrics.to_csv(OUTPUT / "inequality_metrics_v3.csv", index=False)

# Global and local spatial statistics for the stable routed TPU sample.
np.random.seed(SEED)
queen = Queen.from_dataframe(tpu_routed, use_index=False)
queen.transform = "r"
global_results = {}
local_results = {}
local_clusters = {}
spatial_rows = []
lisa_rows = []
lisa_assignments = tpu_routed[["TPU", "min_tt", "bcps_within_60"]].copy()
quadrant_names = {0: "Not significant", 1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"}
for variable in ["min_tt", "bcps_within_60"]:
    np.random.seed(SEED)
    mi = Moran(tpu_routed[variable].to_numpy(), queen, permutations=999)
    np.random.seed(SEED)
    local = Moran_Local(tpu_routed[variable].to_numpy(), queen, permutations=999)
    raw_significant = local.p_sim < 0.05
    fdr_significant = multipletests(local.p_sim, alpha=0.05, method="fdr_bh")[0]
    cluster_raw = np.where(raw_significant, local.q, 0).astype(int)
    cluster_fdr = np.where(fdr_significant, local.q, 0).astype(int)
    global_results[variable] = mi
    local_results[variable] = local
    local_clusters[variable] = {"raw": cluster_raw, "fdr_bh": cluster_fdr}
    lisa_assignments[f"{variable}_cluster_raw"] = [quadrant_names[value] for value in cluster_raw]
    lisa_assignments[f"{variable}_cluster_fdr_bh"] = [quadrant_names[value] for value in cluster_fdr]
    lisa_assignments[f"{variable}_p_sim"] = local.p_sim
    values = tpu_routed[variable].to_numpy(dtype=float)
    spatial_rows.append({
        "variable": variable, "n": len(values), "minimum": values.min(),
        "maximum": values.max(), "mean": values.mean(), "median": np.median(values),
        "sd": values.std(ddof=1), "moran_i": mi.I, "expected_i": mi.EI,
        "z_normal": mi.z_norm, "p_permutation": mi.p_sim,
        "queen_islands": len(queen.islands), "queen_mean_neighbors": queen.mean_neighbors,
    })
    for correction, cluster in (("raw_p_lt_0.05", cluster_raw), ("fdr_bh_0.05", cluster_fdr)):
        for code, label in quadrant_names.items():
            lisa_rows.append({
                "variable": variable, "correction": correction,
                "cluster": label, "count": int((cluster == code).sum())
            })
pd.DataFrame(spatial_rows).to_csv(OUTPUT / "spatial_metrics_v3.csv", index=False)
pd.DataFrame(lisa_rows).to_csv(OUTPUT / "lisa_counts_v3.csv", index=False)
lisa_assignments.to_csv(OUTPUT / "lisa_assignments_tpu_v3.csv", index=False)

# Refit the retained exploratory GWR specification to save its local surface.
y = stpug["min_tt"].to_numpy().reshape(-1, 1)
X = np.column_stack([
    stats.zscore(stpug["median_hh_income"].to_numpy()),
    stats.zscore(stpug["pop_density_km2"].to_numpy()),
])
coords = np.column_stack([stpug.geometry.centroid.x, stpug.geometry.centroid.y])
selector = Sel_BW(coords, y, X, kernel="bisquare", fixed=False, spherical=False, n_jobs=1)
bw = selector.search(criterion="AICc")
gwr = GWR(coords, y, X, bw=bw, kernel="bisquare", fixed=False,
          spherical=False, n_jobs=1).fit()
critical_t = float(gwr.critical_tval())
stpug["gwr_intercept"] = gwr.params[:, 0]
stpug["gwr_income_beta"] = gwr.params[:, 1]
stpug["gwr_density_beta"] = gwr.params[:, 2]
stpug["gwr_income_t"] = gwr.tvalues[:, 1]
stpug["gwr_income_significant"] = np.abs(gwr.tvalues[:, 1]) >= critical_t
gwr_fields = [
    "stpug_id", "min_tt", "median_hh_income", "pop_density_km2",
    "gwr_intercept", "gwr_income_beta", "gwr_density_beta", "gwr_income_t",
    "gwr_income_significant",
]
stpug[gwr_fields].to_csv(OUTPUT / "gwr_local_results_stpug_v3.csv", index=False)
stpug[gwr_fields + ["geometry"]].to_file(
    OUTPUT / "gwr_local_results_stpug_v3.gpkg", layer="gwr_stpug_v3", driver="GPKG"
)

# Figure 1: corrected minimum travel-time burden.
fig, ax = plt.subplots(figsize=(7.2, 5.3))
tpu_all.plot(ax=ax, color="#D9D9D9", edgecolor="white", linewidth=0.18)
tpu_routed.plot(ax=ax, column="min_tt", cmap="viridis_r", vmin=20, vmax=115,
                edgecolor="white", linewidth=0.18)
sm = mpl.cm.ScalarMappable(norm=Normalize(20, 115), cmap="viridis_r")
cbar = fig.colorbar(sm, ax=ax, fraction=0.026, pad=0.015)
cbar.set_label("Minimum travel time (minutes)")
add_bcps(ax, bcp); finish_map(ax)
ax.set_title("Minimum transit travel time to six operational land BCPs", fontweight="bold")
fig.tight_layout()
fig.savefig(OUTPUT / "fig1_v3.png", dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT / "fig1_v3.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 2: corrected opportunity breadth.
fig, ax = plt.subplots(figsize=(7.2, 5.3))
tpu_all.plot(ax=ax, color="#D9D9D9", edgecolor="white", linewidth=0.18)
cmap = mpl.colormaps["YlGnBu"].resampled(7)
norm = BoundaryNorm(np.arange(-0.5, 6.5, 1), cmap.N)
tpu_routed.plot(ax=ax, column="bcps_within_60", cmap=cmap, norm=norm,
                edgecolor="white", linewidth=0.18)
sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
cbar = fig.colorbar(sm, ax=ax, fraction=0.026, pad=0.015, ticks=range(6))
cbar.set_label("Operational BCPs reachable within 60 minutes")
add_bcps(ax, bcp); finish_map(ax)
ax.set_title("Operational land BCPs reachable within 60 minutes", fontweight="bold")
fig.tight_layout()
fig.savefig(OUTPUT / "fig2_v3.png", dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT / "fig2_v3.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 3: Lorenz curves for the two place-based accessibility measures.
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.45))
panels = [
    (axes[0], tpu_routed["min_tt"].to_numpy(), "#D55E00",
     "a  Minimum travel-time burden",
     "Cumulative share of TPUs\n(shorter to longer travel time)",
     "Cumulative share of minimum\ntravel-time burden"),
    (axes[1], tpu_routed["bcps_within_60"].to_numpy(), "#0072B2",
     "b  BCPs reachable within 60 minutes",
     "Cumulative share of TPUs\n(fewer to more reachable BCPs)",
     "Cumulative share of reachable BCP count"),
]
for ax, values, color, title, xlabel, ylabel in panels:
    x_curve, y_curve = lorenz_points(values)
    coefficient = gini(values)
    ax.plot([0, 1], [0, 1], color="#777777", linestyle="--", linewidth=0.9)
    ax.fill_between(x_curve, y_curve, x_curve, color=color, alpha=0.12)
    ax.plot(x_curve, y_curve, color=color, linewidth=1.8)
    ax.set_title(title, loc="left", fontweight="bold")
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
    ax.grid(alpha=0.14, linewidth=0.5)
    ax.text(0.97, 0.05, f"Gini = {coefficient:.3f}", ha="right", va="bottom",
            transform=ax.transAxes, color=color, fontweight="bold")
axes[1].text(0.03, 0.93, f"{(tpu_routed['bcps_within_60'] == 0).mean():.1%} of TPUs reach no BCP",
             transform=axes[1].transAxes, va="top", fontsize=7)
fig.suptitle(f"Distribution of access to six operational land BCPs ({len(tpu_routed)} TPUs)",
             fontsize=10, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(OUTPUT / "fig3_v3.png", dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT / "fig3_v3.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 4: LISA clusters, where labels describe value clusters rather than advantage.
lisa_colors = {0: "#D9D9D9", 1: "#D73027", 2: "#91BFDB", 3: "#4575B4", 4: "#FDAE61"}
fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.5))
for ax, variable, title in [
    (axes[0], "min_tt", "a  Minimum travel-time burden"),
    (axes[1], "bcps_within_60", "b  BCPs reachable within 60 minutes"),
]:
    plotted = tpu_routed.copy()
    plotted["cluster"] = local_clusters[variable]["fdr_bh"]
    tpu_all.plot(ax=ax, color="#EFEFEF", edgecolor="white", linewidth=0.15)
    for category, color in lisa_colors.items():
        subset = plotted[plotted["cluster"] == category]
        if len(subset):
            subset.plot(ax=ax, color=color, edgecolor="white", linewidth=0.15)
    ax.set_title(title, loc="left", fontweight="bold")
    finish_map(ax, show_legend=False)
handles = [Patch(facecolor=lisa_colors[i], label=quadrant_names[i]) for i in [1, 3, 4, 2, 0]]
fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False,
           bbox_to_anchor=(0.5, -0.01), fontsize=7)
fig.suptitle(f"FDR-adjusted local spatial clusters ({len(tpu_routed)} TPUs)",
             fontsize=10, fontweight="bold")
fig.tight_layout(rect=[0, 0.06, 1, 0.94])
fig.savefig(OUTPUT / "fig4_v3.png", dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT / "fig4_v3.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 5: descriptive bivariate relationship at the STPUG analytical grain.
x_income = stpug["median_hh_income"].to_numpy(dtype=float) / 1000
y_time = stpug["min_tt"].to_numpy(dtype=float)
slope, intercept = np.polyfit(x_income, y_time, 1)
r_value, r_p = stats.pearsonr(x_income, y_time)
fig, ax = plt.subplots(figsize=(4.9, 3.45))
ax.scatter(x_income, y_time, s=20, alpha=0.62, color="#0072B2",
           edgecolor="white", linewidth=0.3)
x_line = np.linspace(x_income.min(), x_income.max(), 100)
ax.plot(x_line, intercept + slope * x_line, color="#D55E00", linewidth=1.5)
ax.set_xlabel("Median monthly household income (HKD thousands)")
ax.set_ylabel("Minimum travel time to an operational BCP (minutes)")
p_label = "p < 0.001" if r_p < 0.001 else f"p = {r_p:.3f}"
ax.text(0.97, 0.96, f"Pearson r = {r_value:.3f}; {p_label}", transform=ax.transAxes,
        ha="right", va="top", fontsize=7)
ax.grid(alpha=0.15, linewidth=0.5)
fig.tight_layout()
fig.savefig(OUTPUT / "fig5_v3.png", dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT / "fig5_v3.pdf", bbox_inches="tight")
plt.close(fig)

# Figure 6: exploratory local income coefficients at the STPUG grain.
fig, ax = plt.subplots(figsize=(7.2, 5.0))
limit = float(np.max(np.abs(stpug["gwr_income_beta"])))
div_norm = TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit)
stpug.plot(ax=ax, column="gwr_income_beta", cmap="RdBu_r", norm=div_norm,
           edgecolor="white", linewidth=0.22)
non_sig = stpug[~stpug["gwr_income_significant"]]
significant = stpug[stpug["gwr_income_significant"]]
non_sig.plot(ax=ax, color="white", edgecolor="#CCCCCC", linewidth=0.12, alpha=0.62)
significant.plot(ax=ax, facecolor="none", edgecolor="#222222", linewidth=0.85)
sm = mpl.cm.ScalarMappable(norm=div_norm, cmap="RdBu_r")
cbar = fig.colorbar(sm, ax=ax, fraction=0.026, pad=0.015)
cbar.set_label("Local income coefficient (minutes per SD)")
finish_map(ax, show_legend=False)
ax.set_title(f"Exploratory GWR income coefficients ({len(stpug)} STPUGs)", fontweight="bold")
ax.legend(
    handles=[
        Patch(facecolor="#EEEEEE", edgecolor="#CCCCCC", label="Below adjusted |t| threshold"),
        Patch(facecolor="none", edgecolor="#222222", linewidth=0.85,
              label="Exceeds adjusted |t| threshold"),
    ],
    loc="lower left", frameon=False, fontsize=7,
)
fig.tight_layout()
fig.savefig(OUTPUT / "fig6_v3.png", dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT / "fig6_v3.pdf", bbox_inches="tight")
plt.close(fig)

# Supplementary threshold sensitivity figure.
thresholds = [45, 60, 75, 90]
equal_gini = [gini(tpu_routed[f"bcps_within_{threshold}"].to_numpy()) for threshold in thresholds]
population_gini = [
    gini(stpug[f"bcps_within_{threshold}"].to_numpy(), stpug["population"].to_numpy())
    for threshold in thresholds
]
fig, ax = plt.subplots(figsize=(4.8, 3.35))
ax.plot(thresholds, equal_gini, color="#0072B2", marker="o", linewidth=1.8,
        label=f"TPU equal (n={len(tpu_routed)})")
ax.plot(thresholds, population_gini, color="#D55E00", marker="s", linestyle="--",
        linewidth=1.6, label=f"Population weighted ({len(stpug)} STPUGs)")
ax.set_xlabel("Travel-time threshold (minutes)")
ax.set_ylabel("Gini of reachable BCP count")
ax.set_xticks(thresholds); ax.set_ylim(0, 1)
ax.grid(axis="y", alpha=0.18, linewidth=0.6); ax.legend(frameon=False)
for x_value, y_value in zip(thresholds, equal_gini):
    ax.annotate(f"{y_value:.3f}", (x_value, y_value), xytext=(0, 6),
                textcoords="offset points", ha="center", color="#0072B2", fontsize=7)
fig.tight_layout()
fig.savefig(OUTPUT / "fig_threshold_sensitivity_v3.png", dpi=300, bbox_inches="tight")
fig.savefig(OUTPUT / "fig_threshold_sensitivity_v3.pdf", bbox_inches="tight")
plt.close(fig)

payload = {
    "place_tpu": {row["variable"]: row for row in metric_rows if row["grain"] == "TPU"},
    "population_weighted_stpug": {
        row["variable"]: row for row in metric_rows if row["grain"] == "STPUG"
    },
    "spatial_tpu": {row["variable"]: row for row in spatial_rows},
    "lisa_counts": lisa_rows,
    "gwr": {
        "n": len(stpug), "bandwidth": float(bw), "r2": float(gwr.R2),
        "adjusted_r2": float(gwr.adj_R2), "aicc": float(gwr.aicc),
        "income_min": float(stpug["gwr_income_beta"].min()),
        "income_max": float(stpug["gwr_income_beta"].max()),
        "critical_t": critical_t,
        "income_significant_count": int(stpug["gwr_income_significant"].sum()),
    },
    "income_bivariate": {"pearson_r": float(r_value), "p": float(r_p)},
}
(OUTPUT / "stage9a_spatial_results_v3.json").write_text(
    json.dumps(payload, indent=2, default=float) + "\n", encoding="utf-8"
)

# Guard against drift from the independently retained Stage 9A reanalysis.
stage65 = json.loads((SOURCE / "stage9a_results_v3.json").read_text(encoding="utf-8"))
assert np.isclose(gini(tpu_routed["min_tt"]), stage65["place_metrics"]["new_gini_min_tt"])
assert np.isclose(float(bw), stage65["model_details"]["gwr_bandwidth"])
assert np.isclose(float(gwr.R2), stage65["model_details"]["gwr_r2"])
assert int(stpug["gwr_income_significant"].sum()) == stage65["model_details"]["gwr_income_significant_count"]

print(f"Generated {len(OUTPUT_FILES)} Stage 9A outputs in {OUTPUT}")
print(f"TPU Queen islands: {len(queen.islands)}")
for row in spatial_rows:
    print(f"{row['variable']}: Moran I={row['moran_i']:.4f}, p={row['p_permutation']:.3f}")
print(f"GWR bandwidth={bw:.0f}, R2={gwr.R2:.4f}, significant income coefficients={int(stpug['gwr_income_significant'].sum())}")
