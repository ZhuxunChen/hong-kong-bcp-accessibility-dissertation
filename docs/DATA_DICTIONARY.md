# Stage 9A Data Dictionary

All travel times are scheduled public-transport minutes. IDs are strings because composite census units may end in `S`.

## Inputs and routing runs

- `inputs/tpu_origins_v3.csv`: 292 TPU routing origins in WGS84 longitude/latitude.
- `inputs/stpug_origins_v3.csv`: 211 census STPUG routing origins.
- `inputs/stpug_tpu_crosswalk_v3.csv`: unique assignment of 292 TPUs to 211 STPUGs.
- `inputs/census_stpug_v3.csv`: census attributes, projected areas and population densities.
- `inputs/bcp_destinations_v3.csv`: six GTFS-anchored destination coordinates.
- `runs/run_01` to `run_05`: one stochastic r5r routing repetition per directory.
- `travel_time_matrix_*_v3.csv`: long origin-destination matrices with p25, p50 and p75 travel times.

## Final outputs

- `results/accessibility_tpu_v3.csv`: one row per routed TPU, nearest BCP, minimum p50 and threshold counts.
- `results/analysis_stpug_v3.csv`: one row per routed STPUG with census and accessibility variables.
- `results/model_comparison_stpug_v3.csv`: OLS, SAR, Queen/KNN5 SEM and exploratory GWR results.
- `results/routing_uncertainty_v3.json`: per-run coverage and between-run variation.
- `results/omitted_origin_audit_*_v3.csv`: network-snapping evidence for origins absent from stable results.
- `results/figures_and_spatial/inequality_metrics_v3.csv`: equal-place and population-weighted distributional summaries.
- `results/figures_and_spatial/spatial_metrics_v3.csv`: global Moran statistics.
- `results/figures_and_spatial/lisa_assignments_tpu_v3.csv`: raw and FDR-corrected local cluster assignments.
- `results/figures_and_spatial/gwr_local_results_stpug_v3.csv`: exploratory local GWR coefficients.

`min_tt` is the p50 travel time to the nearest of six BCPs. `bcps_within_N` is the number of BCPs reachable within N minutes. Shares are proportions from 0 to 1; income is monthly HKD; area is km2; population density is persons per km2.
