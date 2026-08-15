# Data and Code Availability

The analysis scripts, frozen reference results, manifests and input snapshots are published as an academic reproducibility archive at https://github.com/ZhuxunChen/hong-kong-bcp-accessibility-dissertation.

The executable Stage 9A workflow is under `analysis/stage9a/scripts/`. Frozen outputs are under `reference_outputs/stage9a/`, and their source-workspace checksums are verified by `tools/verify_reference_outputs.py`. The Appendix E checks are under `analysis/meeting3_checks/`, with frozen outputs under `reference_outputs/meeting3_checks/`. Validation and within-TPU origin-sensitivity scripts are under `analysis/validation/`, with retained reports, comparison tables and routing matrices under `reference_outputs/validation/`. Large generated R5 caches are omitted because they are reconstructed from the retained OSM and GTFS inputs.

The pre-portability 78-file manifest is retained as provenance, while
`docs/REPOSITORY_MANIFEST.sha256` covers the current complete upload package. The
software command snapshot is `docs/software_environment_snapshot.txt`.

The deposited five-run aggregate supports exact post-routing reproduction of
the reported statistics and figures. Full network rerouting is stochastic
because r5r 2.4.0 does not expose a random-seed argument for the routing
function; fresh reroutes are therefore assessed against documented numerical
tolerances and inferential invariants using `tools/compare_reproduction.py`.

The custom MTR input is a project-generated analytical approximation, not an official MTR timetable. It is included with construction and validation evidence for academic reproducibility. Publication does not transfer or replace rights and conditions attached to upstream information.
