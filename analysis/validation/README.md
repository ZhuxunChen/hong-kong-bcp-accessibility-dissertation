# Validation checks added on 15 August 2026

This folder contains validation and sensitivity checks cited in the dissertation. They
do not modify the frozen Stage 9A results.

## MTR external plausibility check

```bash
python3 analysis/validation/extract_modelled_times_v2.py
```

The script reads station-to-station times from the frozen analytical MTR feed.
The saved comparison table, source log and report are under
`reference_outputs/validation/mtr/`. Two gateway benchmarks come from the Hong
Kong Transport Department; the four non-East-Rail anchors are approximate
secondary sources. This is a small plausibility check, not a full network
validation, and the aggregate accessibility indicators were not re-estimated.

## TPU threshold-margin diagnostic

```bash
python3 analysis/validation/threshold_margin_diagnostic_v2.py
```

The script describes how centroid-based minimum times sit relative to the
60-minute threshold. The saved table, method audit and report are under
`reference_outputs/validation/origin/`. No alternative origins were re-routed;
the diagnostic therefore does not estimate the direction or magnitude of
origin sensitivity.

## Within-TPU origin re-routing

The executable scripts are under `analysis/validation/origin_reroute/`:

```bash
python3 analysis/validation/origin_reroute/01_generate_alternative_origins.py
PROJECT_ROOT=$(pwd) STAGE9A_REPS=5 Rscript analysis/validation/origin_reroute/02_route_alt_origins.R
python3 analysis/validation/origin_reroute/03_aggregate_and_compare.py
```

The check routes 2,051 unweighted interior points and the original centroids
five times under the frozen parameters. The points are a spatial sample, not
population-weighted residential origins. Saved comparison data, summary
statistics and the five final routing matrices are under
`reference_outputs/validation/origin_reroute/`.
