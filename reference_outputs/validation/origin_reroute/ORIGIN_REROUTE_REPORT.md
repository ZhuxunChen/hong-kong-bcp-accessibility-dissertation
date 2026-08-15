# Within-TPU Origin Re-routing Sensitivity Report

**Date:** 15 August 2026  
**Status:** Completed five-repetition r5r re-routing check. The frozen Stage 9A runs and results were not modified.

## 1. Question

This check asks how the centroid-based estimate that 66.0% of 209 stable-routed TPUs cannot reach any of the six BCPs within 60 minutes changes when origins are moved within each TPU.

The alternative origins are an **unweighted spatial sample**, not population-weighted residential origins. The check therefore diagnoses sensitivity to origin placement; it does not estimate population exposure.

## 2. Environment and routing specification

- R 4.5.1; r5r 2.4.0; Java 21.0.11.
- Cached Stage 9A R5 network: `analysis/stage9a/network/network.dat`.
- Monday 29 June 2026 at 08:00, Asia/Hong_Kong.
- WALK + TRANSIT; six BCP destinations.
- Maximum trip duration 120 minutes; maximum walk time 20 minutes.
- 30-minute departure window; five draws per minute; p25/p50/p75.
- Five repetitions; an OD p50 is retained in at least three runs and aggregated by its cross-run median.

## 3. Origin construction

The generator created:

- 2,051 unweighted alternative points across all 292 TPU polygons: one representative interior point plus up to nine interior grid points, after duplicate removal;
- 292 frozen centroid points, re-routed as a simulation-consistency guard;
- 2,343 routing points in total.

Among the 209 TPUs in the frozen accessibility baseline, there were 1,509 unweighted alternative points (3-10 per TPU).

## 4. Execution and audit trail

The first five routing runs covered the 2,051 alternative points. An audit then identified that a sampled best-case should also include the original centroid as a guard candidate. The original five matrices were preserved under `analysis/stage9a/alt_origin_runs/attempt_01_without_frozen_centroid/`. Five additional runs routed the 292 centroids, and each centroid component was combined with the corresponding alternative-point run. Both subsets used identical routing parameters, and all components and logs are retained. The pooled matrices do not assume that batch-level random-number sequences would be identical to a single joint call; stability is instead assessed through the same five-run 3-of-5 rule.

Run-level combined row counts were 9,700, 9,694, 9,702, 9,702 and 9,698. Each run contained unique `(from_id, to_id)` pairs. Across the five runs, 9,531 OD pairs met the 3-of-5 p50 stability rule.

All 48 files under the frozen `analysis/stage9a/runs/` and `analysis/stage9a/results/` trees retained their original SHA-256 hashes.

## 5. Results

| Measure | Result | Interpretation |
|---|---:|---|
| Frozen centroid zero-access share | 138/209 = **66.0%** | Dissertation baseline |
| Re-routed frozen centroid share | 137/209 = **65.6%** | Repetition-consistency check |
| TPU-equal mean sampled-point zero-access share | **68.9%** | Mean of each TPU's unweighted point-level zero-access proportion |
| Sampled best-case zero-access share | 105/209 = **50.2%** | Optimistic scenario using the best routed candidate in each TPU |
| TPUs whose censored mean minimum time exceeds 60 minutes | 157/209 = **75.1%** | Secondary diagnostic; no-route points coded at the 120-minute cap |
| Spearman: frozen vs re-routed centroid | **0.999** | Near-identical ranking |
| Spearman: frozen vs sampled best-case | **0.930** | Strongly preserved territorial ranking |
| Spearman: frozen vs censored mean time | **0.856** | Broad ranking remains similar but less stable |

The re-routed centroid differed from the frozen minimum time by a mean absolute 0.19 minutes (median 0; maximum 2 minutes). This confirms that the new five-run execution reproduces the frozen centroid baseline closely.

Under the sampled best-case, 33 of the 138 baseline zero-access TPUs moved to at least one BCP within 60 minutes; no baseline-accessible TPU became zero-access. The mean sampled best-case minimum time was 60.6 minutes, compared with 67.0 minutes at the frozen centroid.

For TPU 622, the frozen centroid minimum was 52 minutes, the re-routed centroid was 53, the sampled best-case was 46, and the censored alternative-point mean was 90.2. This confirms substantial within-zone variation while preserving the earlier finding that the frozen centroid is not itself zero-access.

## 6. Interpretation

The result is not simply "robust" or "not robust":

- Re-running the same centroids reproduces the 66.0% estimate almost exactly.
- Averaging point-level zero-access status within each TPU gives 68.9%, also close to the centroid estimate.
- Selecting the most favourable sampled point in every TPU reduces the share to 50.2%, so the exact threshold statistic is sensitive to systematically favourable origin placement.
- Spearman rho of 0.930 shows that the broad territorial ordering remains strong even under the optimistic sampled best-case.

The 50.2% figure is an **optimistic sampled scenario**, not an expected population value and not a strict mathematical bound over every possible location. The 68.9% mean-case is also not population-weighted. The coarse grid, unequal number of valid points per polygon, network snapping and 120-minute censoring remain limitations.

## 7. Suggested dissertation wording

> A within-TPU re-routing check used 2,051 unweighted interior points and five repeated r5r runs. The TPU-equal mean of sampled point-level zero-access shares was 68.9%, close to the 66.0% centroid estimate, while an optimistic sampled best-case fell to 50.2%. Minimum-time rankings remained strongly correlated with the centroid baseline (Spearman rho = 0.930). The territorial pattern is therefore broadly preserved, but the exact 60-minute share is sensitive to systematically favourable within-TPU origin placement. Because the points are spatial rather than population weighted, the best-case should not be interpreted as expected resident accessibility.

This paragraph can replace the current statement that the direction and magnitude of origin sensitivity are unknown.

## 8. Deliverables

- `01_generate_alternative_origins.py`
- `02_route_alt_origins.R`
- `03_aggregate_and_compare.py`
- `01_generate_alternative_origins.log`
- `02_route_alt_origins_complete.log`
- `03_aggregate_and_compare.log`
- `tpu_alt_origins_v3.csv`
- `origin_reroute_comparison.csv`
- `origin_reroute_summary.json`
- `ENVIRONMENT_LOG.txt`
- `VALIDATION_CHECKS.log`
- `MANIFEST.sha256`
