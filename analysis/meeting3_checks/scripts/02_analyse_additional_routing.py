#!/usr/bin/env python3
"""Analyse extended route repeats and a seven-gateway HSR sensitivity scenario."""

from itertools import product
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
STAGE = ROOT / "analysis" / "stage9a"
if not (STAGE / "inputs").exists():
    STAGE = ROOT / "reference_outputs" / "stage9a"
RESULTS = ROOT / "analysis" / "meeting3_checks" / "results"
FROZEN = ROOT / "reference_outputs" / "meeting3_checks"


def input_result(name: str) -> Path:
    generated = RESULTS / name
    return generated if generated.exists() else FROZEN / name


def gini(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x) or np.allclose(x.sum(), 0):
        return 0.0
    x = np.sort(x)
    n = len(x)
    return float((2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum())) - (n + 1) / n)


def analyse_repeats():
    raw = pd.read_csv(
        input_result("representative_od_30_runs_raw.csv"),
        dtype={"from_id": str, "to_id": str},
    )
    origins = ["627", "728", "284", "421", "838", "835", "971", "622", "158", "310"]
    destinations = ["LW", "LMC", "HG", "SB", "MKT", "HYW"]
    grid = pd.MultiIndex.from_product(
        [range(1, 31), origins, destinations], names=["run", "from_id", "to_id"]
    ).to_frame(index=False)
    data = grid.merge(raw, on=["run", "from_id", "to_id"], how="left")
    data["valid"] = data["travel_time_p50"].notna()

    rows = []
    for (origin, destination), group in data.groupby(["from_id", "to_id"], sort=False):
        v = group["travel_time_p50"].dropna()
        rows.append({
            "from_id": origin,
            "to_id": destination,
            "valid_runs": int(v.size),
            "valid_share": float(v.size / 30),
            "p50_median_30": float(v.median()) if len(v) else np.nan,
            "p50_sd_30": float(v.std(ddof=1)) if len(v) > 1 else 0.0 if len(v) else np.nan,
            "p50_range_30": float(v.max() - v.min()) if len(v) else np.nan,
            "stable_30_majority": bool(v.size >= 15),
        })
    od = pd.DataFrame(rows)
    od.to_csv(RESULTS / "representative_od_30_run_summary.csv", index=False)

    reference_stable = od.set_index(["from_id", "to_id"])["stable_30_majority"]
    reference_median = od.set_index(["from_id", "to_id"])["p50_median_30"]
    rng = np.random.default_rng(25194655)
    bootstrap = []
    for draw in range(1000):
        selected = rng.choice(np.arange(1, 31), size=5, replace=False)
        sub = data[data["run"].isin(selected)]
        valid = sub.groupby(["from_id", "to_id"])["valid"].sum().reindex(reference_stable.index, fill_value=0)
        stable = valid >= 3
        agreement = float((stable == reference_stable).mean())
        both = stable & reference_stable
        med = sub.groupby(["from_id", "to_id"])["travel_time_p50"].median().reindex(reference_stable.index)
        errors = (med[both] - reference_median[both]).abs().dropna()
        bootstrap.append({
            "draw": draw + 1,
            "classification_agreement": agreement,
            "retained_od_pairs": int(stable.sum()),
            "median_absolute_error_minutes": float(errors.median()) if len(errors) else np.nan,
            "p95_absolute_error_minutes": float(errors.quantile(0.95)) if len(errors) else np.nan,
        })
    boot = pd.DataFrame(bootstrap)
    boot.to_csv(RESULTS / "five_run_rule_bootstrap.csv", index=False)

    convergence = []
    for n in [3, 5, 10, 20, 30]:
        sub = data[data["run"] <= n]
        valid = sub.groupby(["from_id", "to_id"])["valid"].sum().reindex(reference_stable.index, fill_value=0)
        stable = valid >= int(np.ceil(n / 2))
        both = stable & reference_stable
        med = sub.groupby(["from_id", "to_id"])["travel_time_p50"].median().reindex(reference_stable.index)
        errors = (med[both] - reference_median[both]).abs().dropna()
        convergence.append({
            "runs": n,
            "majority_required": int(np.ceil(n / 2)),
            "retained_od_pairs": int(stable.sum()),
            "classification_agreement": float((stable == reference_stable).mean()),
            "median_absolute_error_minutes": float(errors.median()) if len(errors) else np.nan,
            "max_absolute_error_minutes": float(errors.max()) if len(errors) else np.nan,
        })
    convergence = pd.DataFrame(convergence)
    convergence.to_csv(RESULTS / "repeat_run_convergence.csv", index=False)

    summary = {
        "od_pairs": int(len(od)),
        "stable_30_majority": int(od["stable_30_majority"].sum()),
        "median_valid_share": float(od["valid_share"].median()),
        "median_p50_sd_minutes_stable": float(od.loc[od.stable_30_majority, "p50_sd_30"].median()),
        "p95_p50_sd_minutes_stable": float(od.loc[od.stable_30_majority, "p50_sd_30"].quantile(0.95)),
        "bootstrap_mean_classification_agreement": float(boot["classification_agreement"].mean()),
        "bootstrap_p05_classification_agreement": float(boot["classification_agreement"].quantile(0.05)),
        "bootstrap_median_mae_minutes": float(boot["median_absolute_error_minutes"].median()),
        "bootstrap_p95_mae_minutes": float(boot["median_absolute_error_minutes"].quantile(0.95)),
    }
    return summary


def analyse_hsr():
    raw = pd.read_csv(input_result("west_kowloon_5_runs_raw.csv"), dtype={"from_id": str})
    hsr = raw.groupby("from_id").agg(
        hsr_runs_present=("travel_time_p50", "count"),
        hsr_p50=("travel_time_p50", "median"),
        hsr_run_sd=("travel_time_p50", "std"),
        hsr_run_range=("travel_time_p50", lambda x: x.max() - x.min()),
    ).reset_index().rename(columns={"from_id": "area_id"})
    hsr.loc[hsr["hsr_runs_present"] < 3, "hsr_p50"] = np.nan

    main_matrix = pd.read_csv(
        STAGE / "results" / "travel_time_matrix_tpu_v3.csv",
        dtype={"from_id": str, "to_id": str},
    )
    main = main_matrix.groupby("from_id").agg(
        min_tt_6=("travel_time_p50", "min"),
        gateways_60_6=("travel_time_p50", lambda x: int((x <= 60).sum())),
    ).reset_index().rename(columns={"from_id": "area_id"})
    origins = pd.read_csv(STAGE / "inputs" / "tpu_origins_v3.csv", dtype={"id": str}).rename(columns={"id": "area_id"})
    out = origins.merge(main, on="area_id", how="left").merge(hsr, on="area_id", how="left")
    out["min_tt_7"] = out[["min_tt_6", "hsr_p50"]].min(axis=1, skipna=True)
    out["gateways_60_7"] = out["gateways_60_6"].fillna(0) + out["hsr_p50"].le(60).astype(int)
    out["stable_6"] = out["min_tt_6"].notna()
    out["stable_7"] = out["min_tt_7"].notna()
    out["hsr_is_nearest"] = out["hsr_p50"].notna() & (
        out["min_tt_6"].isna() | out["hsr_p50"].lt(out["min_tt_6"])
    )
    out["time_reduction"] = out["min_tt_6"] - out["min_tt_7"]
    out.to_csv(RESULTS / "accessibility_tpu_7gateway_hsr_sensitivity.csv", index=False)

    matched = out[out["stable_6"]].copy()
    summary = {
        "stable_six_origins": int(out["stable_6"].sum()),
        "stable_seven_origins": int(out["stable_7"].sum()),
        "matched_n": int(len(matched)),
        "mean_min_tt_6": float(matched["min_tt_6"].mean()),
        "mean_min_tt_7": float(matched["min_tt_7"].mean()),
        "gini_min_tt_6": gini(matched["min_tt_6"]),
        "gini_min_tt_7": gini(matched["min_tt_7"]),
        "zero_within_60_6_share": float(matched["gateways_60_6"].eq(0).mean()),
        "zero_within_60_7_share": float(matched["gateways_60_7"].eq(0).mean()),
        "gini_gateway_count_6": gini(matched["gateways_60_6"]),
        "gini_gateway_count_7": gini(matched["gateways_60_7"]),
        "hsr_nearest_count_matched": int(matched["hsr_is_nearest"].sum()),
        "median_reduction_if_improved": float(matched.loc[matched["time_reduction"] > 0, "time_reduction"].median()),
        "max_reduction": float(matched["time_reduction"].max()),
    }
    return summary


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    repeat = analyse_repeats()
    hsr = analyse_hsr()
    payload = {"extended_repeat_check": repeat, "hsr_sensitivity": hsr}
    (RESULTS / "meeting3_additional_routing_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
