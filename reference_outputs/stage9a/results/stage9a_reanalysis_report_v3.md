# Stage 9A Bidirectional-Network Reanalysis Report

## Analytical grains

- Stable place-based accessibility: **209 of 292 TPUs** with a
  valid p50 route in at least three of five routing runs.
- Socioeconomic models: **176 of 211 STPUGs**, matching the census
  publication grain and using grouped STPUG centroids and EPSG:2326 areas.
- Population coverage of routed STPUGs: **91.9%**.

## Impact relative to the frozen v19 run

| Comparison | v19 | Stage 9A |
|---|---:|---:|
| TPUs with valid minimum p50 | 209 | 209 |
| Mean minimum time (minutes) | 67.81 | 67.00 |
| Minimum-time burden Gini | 0.1506 | 0.1483 |

Across 208 common TPUs, the minimum-time MAE is
**1.11 minutes**, the largest absolute change
is **15.0 minutes**, and the nearest
BCP changes for **1 TPUs**.

## Corrected threshold metrics (TPU equal)

| Threshold | Mean reachable BCPs | Zero-access share | Gini |
|---:|---:|---:|---:|
| 45 min | 0.278 | 87.1% | 0.9137 |
| 60 min | 0.789 | 66.0% | 0.7780 |
| 75 min | 2.120 | 29.7% | 0.4951 |
| 90 min | 3.971 | 9.6% | 0.2820 |

### Denominator sensitivity

If every omitted TPU is treated as unable to reach a BCP within the stated threshold:

| Threshold | Stable-sample zero share | All-292 zero share |
|---:|---:|---:|
| 45 min | 87.1% | 90.8% |
| 60 min | 66.0% | 75.7% |
| 75 min | 29.7% | 49.7% |
| 90 min | 9.6% | 35.3% |


## Stage 9A STPUG spatial models

| Weights | Income beta (p) | Density beta (p) | Lambda | AIC | Filtered Moran I (p) |
|---|---:|---:|---:|---:|---:|
| Queen | 0.053 (0.949) | -3.978 (<0.001) | 0.822 | 1338.9 | -0.092 (0.048) |
| KNN5 | 0.025 (0.975) | -4.353 (<0.001) | 0.841 | 1317.8 | -0.010 (0.484) |

Queen islands: 6. VIFs are
1.06 (income) and 1.06
(density). Breusch-Pagan p = 0.000.

GWR is retained as exploratory: bandwidth = 47,
R-squared = 0.785, adjusted R-squared =
0.744, and residual Moran's I =
0.173 (p =
0.001).

## Routing uncertainty

- Five routing repetitions were aggregated by the median p50.
- OD pairs were retained when p50 was available in at least three runs.
- TPU p50 run-SD median: 0.447 minutes.
- TPU p50 run-SD 95th percentile: 0.894 minutes.
- STPUG p50 run-SD median: 0.447 minutes.
- STPUG p50 run-SD 95th percentile: 1.095 minutes.

## Decision rule

Stage 9A replaces the one-direction MTR feed with validated bidirectional
services and aggregates five stochastic routing runs. If any reported v19
estimate changes materially, Chapters 3-6 and all dependent figures must be
versioned before final assembly.
