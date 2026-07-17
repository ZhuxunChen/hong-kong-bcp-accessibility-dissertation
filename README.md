# Spatial Inequality in Public Transport Accessibility to Hong Kong's Operational Land Boundary Control Points

Reproducibility package for an MSc Urban Spatial Science dissertation at the UCL Centre for Advanced Spatial Analysis. This v27 package implements the corrected Stage 9A bidirectional-MTR workflow and supersedes the archived preliminary packages.

Repository: https://github.com/ZhuxunChen/hong-kong-bcp-accessibility-dissertation

## Study scope and final analytical grains

The study estimates scheduled public-transport accessibility from Hong Kong residential planning units to six operational passenger land boundary control points. The final repeated-routing aggregation contains 209 routed Tertiary Planning Units (TPUs). Socioeconomic models contain 176 routed Small Tertiary Planning Unit Groups (STPUGs), covering 91.9% of the 2021 census population represented by the retained workbook.

## Repository structure

```text
analysis/stage9a/scripts/             Nine authoritative Stage 9A scripts
analysis/stage9a/reference_inputs/    Two small preliminary files used only for correction comparisons
reference_outputs/stage9a/            Frozen inputs, five routing runs, results, figures and checksums
docs/                                 Data dictionary, provenance and upload audit
tools/                                Portable verification utilities
renv.lock, renv/                      Locked R 4.5.1 package environment and bootstrap
数据/                                  Nine frozen third-party/project-generated inputs
```

The preliminary baseline files do not define the final results. They are retained only because the reanalysis report quantifies the impact of correcting the one-direction feed.

## Software

- R 4.5.1
- Java 21.0.11
- r5r 2.4.0 / R5 engine 7.5.1
- Python 3.12.13

The complete R environment is locked in `renv.lock`; `R-packages.txt` is a
human-readable summary of the principal R and Java dependencies. Exact Python
package versions are listed in `requirements.txt`.
The captured command-level software record is retained at
`docs/software_environment_snapshot.txt`.

## Reproduction modes

### 1. Exact post-routing reproduction

This is the recommended check of the numbers reported in the dissertation. It
uses the checksum-verified five-run aggregate as the routing input and reruns
the spatial models, inequality measures and figures:

```bash
./setup_python_env.sh
./run_analysis_from_reference.sh
```

The included comparator requires the headline values to match the frozen v27
results at machine precision.

### 2. Full network rerouting

Create the locked Python and R environments, ensure Java 21 is active, and run:

```bash
./setup_python_env.sh
./setup_r_env.sh
./run_pipeline.sh
```

The routing script performs five repetitions. Each origin-destination pair is retained when a valid p50 travel time is present in at least three runs, and the reported p50 is the median across those runs. Generated R5 caches (`network.dat`, MapDB files and logs) are intentionally excluded.

R5 frequency-based routing is stochastic and r5r 2.4.0 does not expose a
random-seed argument for `travel_time_matrix()`. A full reroute is therefore
expected to reproduce the magnitude and inferential conclusions within the
documented tolerances, rather than reproduce every value byte for byte. In an
independent clean run on 17 July 2026, the stable sample was 209 TPUs and 175
STPUGs (rather than 176); mean travel time was 66.96 minutes and the income and
density conclusions were unchanged. `tools/compare_reproduction.py` checks
these tolerances and substantive invariants.

The scripts refuse to overwrite existing analytical outputs. Run either mode
in a clean clone. Frozen results are kept under `reference_outputs/`, separate
from the executable `analysis/stage9a/` workspace.

## Verify the frozen evidence

```bash
python3 tools/verify_reference_outputs.py
shasum -a 256 -c docs/REPOSITORY_MANIFEST.sha256
Rscript -e 'renv::status()'
```

## Main results reported in v27

- Mean minimum scheduled travel time across 209 routed TPUs: 67.0 minutes.
- Minimum-travel-time Gini: 0.1483.
- Zero-access share within 60 minutes: 66.0% (138/209 routed TPUs).
- 60-minute reachable-BCP Gini: 0.7780.
- Global Moran's I for minimum travel time: 0.8399.
- Socioeconomic model sample: 176 STPUGs.
- Area income is not significant under Queen or KNN5 spatial-error specifications.
- Population density has a significant negative association under both specifications.

## Data and release status

Third-party sources and attribution are documented in `docs/THIRD_PARTY_DATA.md`. This repository is prepared as a non-commercial academic reproducibility archive. The project-generated `数据/HK_GTFS/mtr_gtfs.zip` is an analytical approximation rather than an official MTR timetable, and inclusion does not transfer rights in upstream information. No commercial reuse licence is granted. The dissertation PDF is intentionally omitted until the final Form A screening details have been confirmed; the final submission copy can be added afterwards without changing the analytical package.
