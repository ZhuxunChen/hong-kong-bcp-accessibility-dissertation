# Reproducibility Test - 17 July 2026

## Full clean reroute

The complete Stage 9A workflow was run in a new temporary directory using only
the packaged scripts and raw inputs. All nine stages completed, including five
r5r routing repetitions, aggregation, spatial models, figures, omitted-origin
audit and manifest generation.

| Measure | Frozen v27 | Fresh full reroute |
|---|---:|---:|
| Routed TPUs | 209 | 209 |
| Routed STPUGs | 176 | 175 |
| Mean minimum time | 67.000 | 66.962 |
| Minimum-time Gini | 0.14833 | 0.14799 |
| 60-minute BCP Gini | 0.77802 | 0.77431 |
| 60-minute zero-access share | 0.66029 | 0.65550 |
| Minimum-time Moran's I | 0.83994 | 0.83915 |
| Queen SEM income beta (p) | 0.053 (0.949) | -0.210 (0.786) |
| Queen SEM density beta (p) | -3.978 (<0.001) | -3.690 (<0.001) |

The full-reroute comparator passed 9/9 checks. The headline magnitudes and
inferential conclusions were reproduced. The one-unit STPUG difference is
caused by STPUG 720 having valid p50 routes in two of five fresh runs versus
three of five frozen runs. r5r 2.4.0 does not expose a seed argument for
`travel_time_matrix()`, so this edge-of-threshold variation cannot be removed
with R's `set.seed()`.

The two R5 GTFS messages were low-priority `agency_url` parsing warnings in the
retained government feed. They did not concern routes, stops, trip direction,
stop sequences or service calendars.

## Exact post-routing reproduction

`run_analysis_from_reference.sh` was then run in a second clean directory. It
used the checksum-verified five-run aggregate and regenerated all models,
inequality statistics and figures. The strict comparator passed every checked
value at machine precision, including 209 TPUs, 176 STPUGs, accessibility
metrics, Moran's I, Queen SEM coefficients/diagnostics and exploratory GWR
summary values.

## Interpretation

The repository supports exact computational reproduction from the deposited
five-run routing aggregate and tolerance-based end-to-end reproduction from
the raw network inputs. The latter is correctly described as stochastic
robustness rather than byte-identical rerouting.
