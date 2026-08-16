#!/usr/bin/env python3
"""Verify the final explanatory figures and their frozen Stage 9A values."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image


parser = argparse.ArgumentParser()
parser.add_argument(
    "--directory",
    type=Path,
    default=Path(__file__).resolve().parent / "results",
    help="Figure directory to verify (default: generated results).",
)
args = parser.parse_args()
ROOT = args.directory.resolve()
SOURCE = ROOT / "source_data"
STEMS = [
    "figure_B_workflow",
    "figure_C_sample_retention",
    "figure_D_cumulative_access",
    "figure_E_bcp_profile",
    "figure_F_moran_scatter",
    "figure_G_model_transition",
]


def close(value: float, expected: float, tolerance: float = 1e-9) -> None:
    if not np.isclose(value, expected, atol=tolerance, rtol=0):
        raise AssertionError(f"Expected {expected}, found {value}")


for stem in STEMS:
    for suffix in ("png", "pdf", "svg"):
        path = ROOT / f"{stem}.{suffix}"
        if not path.exists() or path.stat().st_size == 0:
            raise AssertionError(f"Missing or empty export: {path.name}")
    image = Image.open(ROOT / f"{stem}.png").convert("RGB")
    if image.width < 2400 or image.height < 1500:
        raise AssertionError(f"Insufficient PNG dimensions: {stem} {image.size}")
    sample = np.asarray(image.resize((160, 100)))
    if sample.std() < 5:
        raise AssertionError(f"Visually blank PNG: {stem}")

retention = pd.read_csv(SOURCE / "figure_C_sample_retention.csv")
assert int(retention.query("grain == 'TPU' and status == 'Stable route'")["n"].iloc[0]) == 209
assert int(retention.query("grain == 'STPUG' and status == 'Stable route'")["n"].iloc[0]) == 176

curve = pd.read_csv(SOURCE / "figure_D_cumulative_access.csv").set_index("threshold_minutes")
close(curve.loc[60, "tpu_equal_share"], 71 / 209)
close(curve.loc[60, "covered_population_share"], 0.3323457188032912)

profile = pd.read_csv(SOURCE / "figure_E_bcp_profile.csv").set_index("bcp")
close(profile.loc["LW", "nearest_share_all_stable_tpus"], 174 / 209)
assert int(profile.loc["LW", "valid_od_n"]) == 206

moran = pd.read_csv(SOURCE / "figure_F_moran_scatter.csv")
assert len(moran) == 418 and moran["TPU"].nunique() == 209

coef = pd.read_csv(SOURCE / "figure_G_model_coefficients.csv")
close(coef.query("model == 'OLS (HC3)' and term == 'Income'")["beta"].iloc[0], 4.249530986607331)
close(coef.query("model == 'SEM Queen' and term == 'Income'")["beta"].iloc[0], 0.053212522010333885)
close(coef.query("model == 'SEM KNN5' and term == 'Population density'")["beta"].iloc[0], -4.353390788749872)

residual = pd.read_csv(SOURCE / "figure_G_residual_moran.csv").set_index("display")
close(residual.loc["SEM Queen", "filtered_or_residual_moran_i"], -0.09196091717480362)
close(residual.loc["SEM KNN5", "moran_p"], 0.484)

print("Final figure verification passed: 6/6 figures and all frozen-value assertions.")
