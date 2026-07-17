#!/usr/bin/env python3
"""Compare a fresh Stage 9A run with the frozen results reported in v27."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRESH = ROOT / "analysis" / "stage9a" / "results"
REFERENCE = ROOT / "reference_outputs" / "stage9a" / "results"


def load(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict", action="store_true",
        help="Require machine-precision equality for exact post-routing reproduction.",
    )
    args = parser.parse_args()

    fresh = load(FRESH / "stage9a_results_v3.json")
    reference = load(REFERENCE / "stage9a_results_v3.json")
    fresh_spatial = load(FRESH / "figures_and_spatial" / "stage9a_spatial_results_v3.json")
    reference_spatial = load(
        REFERENCE / "figures_and_spatial" / "stage9a_spatial_results_v3.json"
    )

    observed = {
        "tpu_n": fresh["place_metrics"]["stable_routed_tpus"],
        "stpug_n": fresh["stpug_metrics"]["routed_stpugs"],
        "mean_min_tt": fresh["place_metrics"]["new_mean_min_tt"],
        "min_tt_gini": fresh["place_metrics"]["new_gini_min_tt"],
        "gini_60": fresh["place_metrics"]["new_gini_bcps_within_60"],
        "zero_60": fresh["place_metrics"]["new_zero_share_bcps_within_60"],
        "moran_i": fresh_spatial["spatial_tpu"]["min_tt"]["moran_i"],
        "income_beta": fresh["model_details"]["sem_queen_income_beta"],
        "income_p": fresh["model_details"]["sem_queen_income_p"],
        "density_beta": fresh["model_details"]["sem_queen_density_beta"],
        "density_p": fresh["model_details"]["sem_queen_density_p"],
        "sem_lambda": fresh["model_details"]["sem_queen_lambda"],
        "sem_aic": fresh["model_details"]["sem_queen_aic"],
        "gwr_bandwidth": fresh["model_details"]["gwr_bandwidth"],
        "gwr_r2": fresh["model_details"]["gwr_r2"],
        "gwr_income_significant_count": fresh["model_details"]["gwr_income_significant_count"],
    }
    expected = {
        "tpu_n": reference["place_metrics"]["stable_routed_tpus"],
        "stpug_n": reference["stpug_metrics"]["routed_stpugs"],
        "mean_min_tt": reference["place_metrics"]["new_mean_min_tt"],
        "min_tt_gini": reference["place_metrics"]["new_gini_min_tt"],
        "gini_60": reference["place_metrics"]["new_gini_bcps_within_60"],
        "zero_60": reference["place_metrics"]["new_zero_share_bcps_within_60"],
        "moran_i": reference_spatial["spatial_tpu"]["min_tt"]["moran_i"],
        "income_beta": reference["model_details"]["sem_queen_income_beta"],
        "income_p": reference["model_details"]["sem_queen_income_p"],
        "density_beta": reference["model_details"]["sem_queen_density_beta"],
        "density_p": reference["model_details"]["sem_queen_density_p"],
        "sem_lambda": reference["model_details"]["sem_queen_lambda"],
        "sem_aic": reference["model_details"]["sem_queen_aic"],
        "gwr_bandwidth": reference["model_details"]["gwr_bandwidth"],
        "gwr_r2": reference["model_details"]["gwr_r2"],
        "gwr_income_significant_count": reference["model_details"]["gwr_income_significant_count"],
    }

    if args.strict:
        checks = {
            key: abs(float(observed[key]) - float(value)) <= 1e-12
            for key, value in expected.items()
        }
        label = "exact post-routing reproduction"
    else:
        checks = {
            "tpu_n": observed["tpu_n"] == 209,
            "stpug_n": observed["stpug_n"] in {175, 176},
            "mean_min_tt": abs(observed["mean_min_tt"] - expected["mean_min_tt"]) <= 0.25,
            "min_tt_gini": abs(observed["min_tt_gini"] - expected["min_tt_gini"]) <= 0.005,
            "gini_60": abs(observed["gini_60"] - expected["gini_60"]) <= 0.02,
            "zero_60": abs(observed["zero_60"] - expected["zero_60"]) <= 0.02,
            "moran_i": abs(observed["moran_i"] - expected["moran_i"]) <= 0.01,
            "income_non_significant": observed["income_p"] > 0.05,
            "density_negative_significant": (
                observed["density_beta"] < 0 and observed["density_p"] < 0.01
            ),
        }
        label = "full stochastic reroute"

    print(json.dumps({"mode": label, "observed": observed, "checks": checks}, indent=2))
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise SystemExit(f"Reproduction checks failed: {failed}")
    print(f"Reproduction checks passed: {len(checks)}/{len(checks)} ({label}).")


if __name__ == "__main__":
    main()
