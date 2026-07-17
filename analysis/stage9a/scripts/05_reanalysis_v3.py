"""Stage 9A reanalysis using repeated bidirectional-network routing."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import esda
import geopandas as gpd
import libpysal
import mgwr
import numpy as np
import pandas as pd
import scipy
import spreg
import statsmodels
import statsmodels.api as sm
from esda.moran import Moran
from mgwr.gwr import GWR
from mgwr.sel_bw import Sel_BW
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor


warnings.filterwarnings("ignore")
SEED = 42
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "analysis" / "stage9a" / "results"
INPUTS = ROOT / "analysis" / "stage9a" / "inputs"
PRELIMINARY_BASELINE = (
    ROOT / "analysis" / "stage9a" / "reference_inputs" / "preliminary_baseline"
)
OUTPUTS = [
    STAGE / "accessibility_tpu_v3.csv",
    STAGE / "analysis_stpug_v3.csv",
    STAGE / "model_comparison_stpug_v3.csv",
    STAGE / "v19_stage9a_tpu_comparison_v3.csv",
    STAGE / "stage9a_results_v3.json",
    STAGE / "stage9a_reanalysis_report_v3.md",
]
if any(path.exists() for path in OUTPUTS):
    existing = [str(path) for path in OUTPUTS if path.exists()]
    raise FileExistsError(f"Refusing to overwrite Stage 9A outputs: {existing}")

BCPS = ["LW", "LMC", "HG", "SB", "MKT", "HYW"]
THRESHOLDS = [45, 60, 75, 90]


def gini(values: np.ndarray, weights: np.ndarray | None = None) -> float:
    x = np.asarray(values, dtype=float)
    if weights is None:
        weights = np.ones_like(x)
    w = np.asarray(weights, dtype=float)
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[mask], w[mask]
    order = np.argsort(x)
    x, w = x[order], w[order]
    total_xw = np.sum(x * w)
    if total_xw == 0:
        return 0.0
    cum_w = np.insert(np.cumsum(w) / np.sum(w), 0, 0.0)
    cum_xw = np.insert(np.cumsum(x * w) / total_xw, 0, 0.0)
    return float(1 - 2 * np.trapezoid(cum_xw, cum_w))


def accessibility_from_matrix(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    long = pd.read_csv(path)
    long["from_id"] = long["from_id"].astype(str)
    long["to_id"] = long["to_id"].astype(str)
    wide = long.pivot(index="from_id", columns="to_id", values="travel_time_p50")
    missing = sorted(set(BCPS) - set(wide.columns))
    if missing:
        raise ValueError(f"Missing BCP columns in {path}: {missing}")
    six = wide[BCPS]
    result = pd.DataFrame(index=six.index)
    result["min_tt"] = six.min(axis=1, skipna=True)
    valid = ~six.isna().all(axis=1)
    result["nearest_bcp"] = pd.Series(index=six.index, dtype="object")
    result.loc[valid, "nearest_bcp"] = six.loc[valid].idxmin(axis=1, skipna=True)
    for threshold in THRESHOLDS:
        result[f"bcps_within_{threshold}"] = (six <= threshold).sum(axis=1)
    result = result.dropna(subset=["min_tt"]).reset_index().rename(columns={"from_id": "area_id"})
    return result, six


def moran(values: np.ndarray, weights) -> tuple[float, float]:
    np.random.seed(SEED)
    fitted = Moran(np.asarray(values).ravel(), weights, permutations=999)
    return float(fitted.I), float(fitted.p_sim)


def fit_models(gdf: gpd.GeoDataFrame) -> tuple[dict, pd.DataFrame]:
    y = gdf["min_tt"].to_numpy().reshape(-1, 1)
    income_z = stats.zscore(gdf["median_hh_income"].to_numpy())
    density_z = stats.zscore(gdf["pop_density_km2"].to_numpy())
    X = np.column_stack([income_z, density_z])
    names = ["median_hh_income_z", "pop_density_z"]

    queen = libpysal.weights.Queen.from_dataframe(gdf, use_index=False)
    queen.transform = "r"
    coords = np.column_stack([gdf.geometry.centroid.x, gdf.geometry.centroid.y])
    knn5 = libpysal.weights.KNN.from_array(coords, k=5)
    knn5.transform = "r"

    X_sm = sm.add_constant(X)
    ols_sm = sm.OLS(y.ravel(), X_sm).fit()
    ols_hc3 = ols_sm.get_robustcov_results(cov_type="HC3")
    vif = [variance_inflation_factor(X_sm, i) for i in range(X_sm.shape[1])]
    bp = het_breuschpagan(ols_sm.resid, X_sm)

    ols = spreg.OLS(y, X, w=queen, name_y="min_tt", name_x=names, spat_diag=True, moran=True)
    sar = spreg.ML_Lag(y, X, w=queen, name_y="min_tt", name_x=names)
    sem_q = spreg.ML_Error(y, X, w=queen, name_y="min_tt", name_x=names)
    sem_k = spreg.ML_Error(y, X, w=knn5, name_y="min_tt", name_x=names)

    sar_moran = moran(sar.u, queen)
    sem_q_filtered = moran(sem_q.e_filtered, queen)
    sem_k_filtered = moran(sem_k.e_filtered, knn5)

    selector = Sel_BW(
        coords, y, X, kernel="bisquare", fixed=False, spherical=False, n_jobs=1
    )
    bw = selector.search(criterion="AICc")
    gwr = GWR(
        coords, y, X, bw=bw, kernel="bisquare", fixed=False,
        spherical=False, n_jobs=1
    ).fit()
    gwr_moran = moran(gwr.resid_response, queen)
    critical_t = float(gwr.critical_tval())
    income_sig = int((np.abs(gwr.tvalues[:, 1]) >= critical_t).sum())

    details = {
        "n": len(gdf),
        "queen_islands": len(queen.islands),
        "queen_mean_neighbors": float(queen.mean_neighbors),
        "vif_income": float(vif[1]),
        "vif_density": float(vif[2]),
        "breusch_pagan_p": float(bp[1]),
        "ols_r2": float(ols.r2),
        "ols_income_beta": float(ols.betas[1, 0]),
        "ols_income_hc3_p": float(ols_hc3.pvalues[1]),
        "ols_density_beta": float(ols.betas[2, 0]),
        "ols_density_hc3_p": float(ols_hc3.pvalues[2]),
        "ols_residual_moran_i": float(ols.moran_res[0]),
        "ols_residual_moran_p": float(ols.moran_res[2]),
        "lm_lag_p": float(ols.lm_lag[1]),
        "lm_error_p": float(ols.lm_error[1]),
        "robust_lm_lag_p": float(ols.rlm_lag[1]),
        "robust_lm_error_p": float(ols.rlm_error[1]),
        "sar_aic": float(sar.aic),
        "sar_rho": float(sar.rho),
        "sar_residual_moran_i": sar_moran[0],
        "sar_residual_moran_p": sar_moran[1],
        "sem_queen_aic": float(sem_q.aic),
        "sem_queen_lambda": float(sem_q.lam),
        "sem_queen_income_beta": float(sem_q.betas[1, 0]),
        "sem_queen_income_se": float(sem_q.std_err[1]),
        "sem_queen_income_p": float(sem_q.z_stat[1][1]),
        "sem_queen_density_beta": float(sem_q.betas[2, 0]),
        "sem_queen_density_se": float(sem_q.std_err[2]),
        "sem_queen_density_p": float(sem_q.z_stat[2][1]),
        "sem_queen_filtered_moran_i": sem_q_filtered[0],
        "sem_queen_filtered_moran_p": sem_q_filtered[1],
        "sem_knn5_aic": float(sem_k.aic),
        "sem_knn5_lambda": float(sem_k.lam),
        "sem_knn5_income_beta": float(sem_k.betas[1, 0]),
        "sem_knn5_income_se": float(sem_k.std_err[1]),
        "sem_knn5_income_p": float(sem_k.z_stat[1][1]),
        "sem_knn5_density_beta": float(sem_k.betas[2, 0]),
        "sem_knn5_density_se": float(sem_k.std_err[2]),
        "sem_knn5_density_p": float(sem_k.z_stat[2][1]),
        "sem_knn5_filtered_moran_i": sem_k_filtered[0],
        "sem_knn5_filtered_moran_p": sem_k_filtered[1],
        "gwr_bandwidth": float(bw),
        "gwr_r2": float(gwr.R2),
        "gwr_adj_r2": float(gwr.adj_R2),
        "gwr_aicc": float(gwr.aicc),
        "gwr_income_min": float(gwr.params[:, 1].min()),
        "gwr_income_max": float(gwr.params[:, 1].max()),
        "gwr_critical_t": critical_t,
        "gwr_income_significant_count": income_sig,
        "gwr_residual_moran_i": gwr_moran[0],
        "gwr_residual_moran_p": gwr_moran[1],
    }

    table = pd.DataFrame([
        {
            "model": "OLS", "n": len(gdf), "r2_or_pseudo_r2": ols.r2,
            "aic": np.nan, "income_beta": ols.betas[1, 0],
            "income_p": ols_hc3.pvalues[1], "density_beta": ols.betas[2, 0],
            "density_p": ols_hc3.pvalues[2], "spatial_parameter": np.nan,
            "filtered_or_residual_moran_i": ols.moran_res[0],
            "moran_p": ols.moran_res[2],
        },
        {
            "model": "SAR Queen", "n": len(gdf), "r2_or_pseudo_r2": sar.pr2,
            "aic": sar.aic, "income_beta": sar.betas[1, 0],
            "income_p": sar.z_stat[1][1], "density_beta": sar.betas[2, 0],
            "density_p": sar.z_stat[2][1], "spatial_parameter": sar.rho,
            "filtered_or_residual_moran_i": sar_moran[0], "moran_p": sar_moran[1],
        },
        {
            "model": "SEM Queen", "n": len(gdf), "r2_or_pseudo_r2": sem_q.pr2,
            "aic": sem_q.aic, "income_beta": sem_q.betas[1, 0],
            "income_p": sem_q.z_stat[1][1], "density_beta": sem_q.betas[2, 0],
            "density_p": sem_q.z_stat[2][1], "spatial_parameter": sem_q.lam,
            "filtered_or_residual_moran_i": sem_q_filtered[0],
            "moran_p": sem_q_filtered[1],
        },
        {
            "model": "SEM KNN5", "n": len(gdf), "r2_or_pseudo_r2": sem_k.pr2,
            "aic": sem_k.aic, "income_beta": sem_k.betas[1, 0],
            "income_p": sem_k.z_stat[1][1], "density_beta": sem_k.betas[2, 0],
            "density_p": sem_k.z_stat[2][1], "spatial_parameter": sem_k.lam,
            "filtered_or_residual_moran_i": sem_k_filtered[0],
            "moran_p": sem_k_filtered[1],
        },
        {
            "model": "GWR", "n": len(gdf), "r2_or_pseudo_r2": gwr.R2,
            "aic": gwr.aicc, "income_beta": float(gwr.params[:, 1].mean()),
            "income_p": np.nan, "density_beta": float(gwr.params[:, 2].mean()),
            "density_p": np.nan, "spatial_parameter": bw,
            "filtered_or_residual_moran_i": gwr_moran[0], "moran_p": gwr_moran[1],
        },
    ])
    return details, table


# Corrected six-BCP place-based indicators.
tpu_access, tpu_wide = accessibility_from_matrix(STAGE / "travel_time_matrix_tpu_v3.csv")
stpug_access, _ = accessibility_from_matrix(STAGE / "travel_time_matrix_stpug_v3.csv")
tpu_access.to_csv(OUTPUTS[0], index=False)

# STPUG census/model dataset at the matching spatial grain.
census = pd.read_csv(INPUTS / "census_stpug_v3.csv", dtype={"stpug_id": str})
geo = gpd.read_file(INPUTS / "stpug_geography_v3.gpkg")
geo["stpug_id"] = geo["stpug_id"].astype(str)
stpug_access = stpug_access.rename(columns={"area_id": "stpug_id"})
analysis = geo.merge(stpug_access, on="stpug_id", how="inner", suffixes=("", "_route"))
if len(analysis) != len(stpug_access):
    raise ValueError("STPUG route/geography join changed row count")
analysis.drop(columns="geometry").to_csv(OUTPUTS[1], index=False)

model_details, model_table = fit_models(analysis)
model_table.to_csv(OUTPUTS[2], index=False)

# Compare old and corrected TPU matrices on common origins and six BCPs.
old_long = pd.read_csv(PRELIMINARY_BASELINE / "travel_time_matrix_tpu_v2.csv")
old_long["from_id"] = old_long["from_id"].astype(str)
old_long["to_id"] = old_long["to_id"].astype(str)
old_wide = old_long.pivot(index="from_id", columns="to_id", values="travel_time_p50")[BCPS]
old_valid = ~old_wide.isna().all(axis=1)
old_access = pd.DataFrame({
    "old_min_tt": old_wide.min(axis=1, skipna=True),
    "old_nearest_bcp": pd.Series(index=old_wide.index, dtype="object"),
})
old_access.loc[old_valid, "old_nearest_bcp"] = old_wide.loc[old_valid].idxmin(
    axis=1, skipna=True
)
old_access = old_access.dropna(subset=["old_min_tt"])
new_access = tpu_access.set_index("area_id")[["min_tt", "nearest_bcp"]].rename(
    columns={"min_tt": "new_min_tt", "nearest_bcp": "new_nearest_bcp"}
)
common = old_access.join(new_access, how="inner")
common["min_tt_change"] = common["new_min_tt"] - common["old_min_tt"]
common["abs_min_tt_change"] = common["min_tt_change"].abs()
common["nearest_changed"] = common["old_nearest_bcp"] != common["new_nearest_bcp"]
common.reset_index(names="tpu_id").to_csv(OUTPUTS[3], index=False)

old_new_bcp = []
new_wide = tpu_wide.copy()
for bcp in BCPS:
    paired = pd.concat(
        [old_wide[bcp].rename("old"), new_wide[bcp].rename("new")], axis=1
    ).dropna()
    old_new_bcp.append({
        "bcp": bcp,
        "n_paired": len(paired),
        "mean_change_minutes": float((paired["new"] - paired["old"]).mean()),
        "mae_minutes": float((paired["new"] - paired["old"]).abs().mean()),
        "max_abs_change_minutes": float((paired["new"] - paired["old"]).abs().max()),
    })

place_metrics = {
    "old_valid_tpus": int(len(old_access)),
    "new_valid_tpus": int(len(tpu_access)),
    "old_mean_min_tt": float(old_access["old_min_tt"].mean()),
    "new_mean_min_tt": float(tpu_access["min_tt"].mean()),
    "old_gini_min_tt": gini(old_access["old_min_tt"].to_numpy()),
    "new_gini_min_tt": gini(tpu_access["min_tt"].to_numpy()),
    "common_tpus": int(len(common)),
    "common_min_tt_mae": float(common["abs_min_tt_change"].mean()),
    "common_min_tt_max_abs_change": float(common["abs_min_tt_change"].max()),
    "common_nearest_bcp_changed": int(common["nearest_changed"].sum()),
}
place_metrics["submitted_tpus"] = 292
place_metrics["stable_routed_tpus"] = int(len(tpu_access))
place_metrics["omitted_tpus"] = 292 - int(len(tpu_access))
for threshold in THRESHOLDS:
    col = f"bcps_within_{threshold}"
    place_metrics[f"new_mean_{col}"] = float(tpu_access[col].mean())
    place_metrics[f"new_zero_share_{col}"] = float((tpu_access[col] == 0).mean())
    place_metrics[f"new_gini_{col}"] = gini(tpu_access[col].to_numpy())
    observed_zero = int((tpu_access[col] == 0).sum())
    place_metrics[f"observed_zero_count_{col}"] = observed_zero
    place_metrics[f"all_tpu_zero_share_if_omitted_nonreachable_{col}"] = (
        observed_zero + place_metrics["omitted_tpus"]
    ) / 292

stpug_metrics = {
    "total_stpugs": 211,
    "routed_stpugs": int(len(analysis)),
    "population_covered": int(analysis["population"].sum()),
    "population_total": int(census["population"].sum()),
    "population_coverage_share": float(analysis["population"].sum() / census["population"].sum()),
    "mean_min_tt": float(analysis["min_tt"].mean()),
    "population_weighted_mean_min_tt": float(
        np.average(analysis["min_tt"], weights=analysis["population"])
    ),
    "gini_min_tt_equal": gini(analysis["min_tt"].to_numpy()),
    "gini_min_tt_population": gini(
        analysis["min_tt"].to_numpy(), analysis["population"].to_numpy()
    ),
}
for threshold in THRESHOLDS:
    col = f"bcps_within_{threshold}"
    stpug_metrics[f"gini_{col}_equal"] = gini(analysis[col].to_numpy())
    stpug_metrics[f"gini_{col}_population"] = gini(
        analysis[col].to_numpy(), analysis["population"].to_numpy()
    )
    stpug_metrics[f"zero_share_{col}_equal"] = float((analysis[col] == 0).mean())
    stpug_metrics[f"zero_share_{col}_population"] = float(
        analysis.loc[analysis[col] == 0, "population"].sum() / analysis["population"].sum()
    )

old_model = pd.read_csv(PRELIMINARY_BASELINE / "model_comparison_stpug_v2.csv")
old_sem = old_model.loc[old_model["model"] == "SEM Queen"].iloc[0].to_dict()
routing_uncertainty = json.loads(
    (STAGE / "routing_uncertainty_v3.json").read_text(encoding="utf-8")
)

payload = {
    "software": {
        "numpy": np.__version__, "pandas": pd.__version__,
        "geopandas": gpd.__version__, "scipy": scipy.__version__,
        "statsmodels": statsmodels.__version__, "libpysal": libpysal.__version__,
        "spreg": spreg.__version__, "esda": esda.__version__, "mgwr": mgwr.__version__,
    },
    "place_metrics": place_metrics,
    "stpug_metrics": stpug_metrics,
    "model_details": model_details,
    "v19_sem_row": old_sem,
    "routing_uncertainty": routing_uncertainty,
    "bcp_pairwise_comparison": old_new_bcp,
}
OUTPUTS[4].write_text(json.dumps(payload, indent=2, default=float) + "\n", encoding="utf-8")

def p(value: float) -> str:
    return "<0.001" if value < 0.001 else f"{value:.3f}"

report = f"""# Stage 9A Bidirectional-Network Reanalysis Report

## Analytical grains

- Stable place-based accessibility: **{len(tpu_access)} of 292 TPUs** with a
  valid p50 route in at least three of five routing runs.
- Socioeconomic models: **{len(analysis)} of 211 STPUGs**, matching the census
  publication grain and using grouped STPUG centroids and EPSG:2326 areas.
- Population coverage of routed STPUGs: **{stpug_metrics['population_coverage_share']:.1%}**.

## Impact relative to the frozen v19 run

| Comparison | v19 | Stage 9A |
|---|---:|---:|
| TPUs with valid minimum p50 | {place_metrics['old_valid_tpus']} | {place_metrics['new_valid_tpus']} |
| Mean minimum time (minutes) | {place_metrics['old_mean_min_tt']:.2f} | {place_metrics['new_mean_min_tt']:.2f} |
| Minimum-time burden Gini | {place_metrics['old_gini_min_tt']:.4f} | {place_metrics['new_gini_min_tt']:.4f} |

Across {place_metrics['common_tpus']} common TPUs, the minimum-time MAE is
**{place_metrics['common_min_tt_mae']:.2f} minutes**, the largest absolute change
is **{place_metrics['common_min_tt_max_abs_change']:.1f} minutes**, and the nearest
BCP changes for **{place_metrics['common_nearest_bcp_changed']} TPUs**.

## Corrected threshold metrics (TPU equal)

| Threshold | Mean reachable BCPs | Zero-access share | Gini |
|---:|---:|---:|---:|
"""
for threshold in THRESHOLDS:
    col = f"bcps_within_{threshold}"
    report += (
        f"| {threshold} min | {place_metrics[f'new_mean_{col}']:.3f} | "
        f"{place_metrics[f'new_zero_share_{col}']:.1%} | "
        f"{place_metrics[f'new_gini_{col}']:.4f} |\n"
    )

report += "\n### Denominator sensitivity\n\n"
report += "If every omitted TPU is treated as unable to reach a BCP within the stated threshold:\n\n"
report += "| Threshold | Stable-sample zero share | All-292 zero share |\n|---:|---:|---:|\n"
for threshold in THRESHOLDS:
    col = f"bcps_within_{threshold}"
    report += (
        f"| {threshold} min | {place_metrics[f'new_zero_share_{col}']:.1%} | "
        f"{place_metrics[f'all_tpu_zero_share_if_omitted_nonreachable_{col}']:.1%} |\n"
    )

report += f"""

## Stage 9A STPUG spatial models

| Weights | Income beta (p) | Density beta (p) | Lambda | AIC | Filtered Moran I (p) |
|---|---:|---:|---:|---:|---:|
| Queen | {model_details['sem_queen_income_beta']:.3f} ({p(model_details['sem_queen_income_p'])}) | {model_details['sem_queen_density_beta']:.3f} ({p(model_details['sem_queen_density_p'])}) | {model_details['sem_queen_lambda']:.3f} | {model_details['sem_queen_aic']:.1f} | {model_details['sem_queen_filtered_moran_i']:.3f} ({p(model_details['sem_queen_filtered_moran_p'])}) |
| KNN5 | {model_details['sem_knn5_income_beta']:.3f} ({p(model_details['sem_knn5_income_p'])}) | {model_details['sem_knn5_density_beta']:.3f} ({p(model_details['sem_knn5_density_p'])}) | {model_details['sem_knn5_lambda']:.3f} | {model_details['sem_knn5_aic']:.1f} | {model_details['sem_knn5_filtered_moran_i']:.3f} ({p(model_details['sem_knn5_filtered_moran_p'])}) |

Queen islands: {model_details['queen_islands']}. VIFs are
{model_details['vif_income']:.2f} (income) and {model_details['vif_density']:.2f}
(density). Breusch-Pagan p = {model_details['breusch_pagan_p']:.3f}.

GWR is retained as exploratory: bandwidth = {model_details['gwr_bandwidth']:.0f},
R-squared = {model_details['gwr_r2']:.3f}, adjusted R-squared =
{model_details['gwr_adj_r2']:.3f}, and residual Moran's I =
{model_details['gwr_residual_moran_i']:.3f} (p =
{p(model_details['gwr_residual_moran_p'])}).

## Routing uncertainty

- Five routing repetitions were aggregated by the median p50.
- OD pairs were retained when p50 was available in at least three runs.
- TPU p50 run-SD median: {routing_uncertainty['tpu']['p50_run_sd_median']:.3f} minutes.
- TPU p50 run-SD 95th percentile: {routing_uncertainty['tpu']['p50_run_sd_p95']:.3f} minutes.
- STPUG p50 run-SD median: {routing_uncertainty['stpug']['p50_run_sd_median']:.3f} minutes.
- STPUG p50 run-SD 95th percentile: {routing_uncertainty['stpug']['p50_run_sd_p95']:.3f} minutes.

## Decision rule

Stage 9A replaces the one-direction MTR feed with validated bidirectional
services and aggregates five stochastic routing runs. If any reported v19
estimate changes materially, Chapters 3-6 and all dependent figures must be
versioned before final assembly.
"""
OUTPUTS[5].write_text(report, encoding="utf-8")
print(report)
