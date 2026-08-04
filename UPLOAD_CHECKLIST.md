# GitHub Upload Checklist

## Verified in this package

- [x] Stage 9A bidirectional-MTR scripts replace Stage 6.5/6.6 scripts.
- [x] Five routing runs and aggregated Stage 9A results are retained.
- [x] Main claims match the frozen Stage 9A results: 209 TPUs, 176 STPUGs, 67.0 minutes, Gini 0.1483 and 0.7780.
- [x] Appendix E robustness and scope checks, scripts and frozen outputs are included.
- [x] Frozen Stage 9A evidence passes the source manifest verifier.
- [x] Python, R and shell syntax checks pass.
- [x] No local absolute paths remain in repository text files.
- [x] No file exceeds GitHub's 100 MB single-file limit.
- [x] Exact post-routing reproduction entry point and full-reroute tolerance checker are included.
- [x] Full clean reroute completed on 17 July 2026; stochastic sample variation is documented.
- [x] Command-level software environment snapshot is included under `docs/`.
- [x] R 4.5.1 and the complete R dependency graph are locked with `renv`.

## Release status

- [x] Create the GitHub repository and insert its URL in the dissertation and documentation.
- [x] Set public visibility after the final repository audit.
- [x] Fill the confirmed student name, Student ID and sole supervisor in the dissertation copy.
- [x] Keep the dissertation document separate from the analytical repository.
- [x] Identify `数据/HK_GTFS/mtr_gtfs.zip` as a non-official project-generated approximation and retain the upstream-rights disclaimer.
- [x] Regenerate `docs/REPOSITORY_MANIFEST.sha256` after the supplementary checks were added.
