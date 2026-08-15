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

## Additional robustness and scope checks

- `reference_outputs/meeting3_checks/representative_od_30_runs_raw.csv`: 30 repeated R5 calls for 10 TPU origins by six BCPs.
- `reference_outputs/meeting3_checks/repeat_run_convergence.csv`: majority-retention agreement for nested run counts.
- `reference_outputs/meeting3_checks/five_run_rule_bootstrap.csv`: 1,000 random five-run subsets compared with the 30-run majority.
- `reference_outputs/meeting3_checks/accessibility_tpu_7gateway_hsr_sensitivity.csv`: six-BCP baseline combined with a West Kowloon terminal-access scenario.
- `reference_outputs/meeting3_checks/minimal_distance_benchmark_tpu.csv`: fixed-speed straight-line benchmark and network-model errors for 209 routed TPUs.
- `reference_outputs/meeting3_checks/gwr_local_case_evidence.csv`: frozen accessibility, local GWR and nearest-stop evidence for the selected STPUG examples.
- `reference_outputs/meeting3_checks/lo_wu_adjacent_tpu_spatial_audit.csv`: projected boundary and origin distances from Lo Wu for the ten nearest TPU polygons, joined to frozen route summaries.
- `reference_outputs/meeting3_checks/lo_wu_tpu622_nearest_stops.csv`: nearest official-feed stops to the TPU 622 analytical origin.
- `reference_outputs/meeting3_checks/lo_wu_route51b_frequency_windows.csv`: route 51B frequency windows intersecting 08:00-08:30.

The supplementary routing files use the same p50 definition as Stage 9A. The West Kowloon scenario measures access to the terminal only and is not a complete cross-boundary journey.

## Validation and within-TPU origin sensitivity

- `reference_outputs/validation/mtr/`: selected external journey-time anchors and analytical-feed comparisons.
- `reference_outputs/validation/origin/`: descriptive threshold-margin diagnostic for the frozen centroid results.
- `reference_outputs/validation/origin_reroute/tpu_alt_origins_v3.csv`: 292 frozen centroids and 2,051 unweighted interior points; the interior points are not population weighted.
- `reference_outputs/validation/origin_reroute/runs/`: five final alternative-origin routing matrices used by the 3-of-5 aggregation.
- `reference_outputs/validation/origin_reroute/origin_reroute_comparison.csv`: TPU-level frozen, re-routed centroid, sampled best-case and sampled mean-case comparison.
