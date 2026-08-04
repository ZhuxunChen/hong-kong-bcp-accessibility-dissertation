# Additional robustness and scope checks

These scripts reproduce the supplementary checks reported in Appendix E and the revised local interpretation in Chapters 5-6. They do not replace the Stage 9A primary analysis.

## Frozen evidence

The checked outputs are stored in `reference_outputs/meeting3_checks/`. They include:

- a 30-run diagnostic for 10 TPU origins by six BCPs;
- 1,000 five-run subset checks of the three-of-five retention rule;
- a West Kowloon HSR gateway sensitivity;
- a fixed-speed straight-line benchmark;
- the study-area and MTR-overlay figures;
- reproducible evidence for TPU 622 and the STPUG 634/757 GWR examples.

## Reproduce from frozen Stage 9A files

From the repository root:

```bash
python3 analysis/meeting3_checks/scripts/02_analyse_additional_routing.py
python3 analysis/meeting3_checks/scripts/03_minimal_distance_benchmark.py
Rscript analysis/meeting3_checks/scripts/04_plot_minimal_distance_benchmark.R
Rscript analysis/meeting3_checks/scripts/05_enhance_study_area_map.R
python3 analysis/meeting3_checks/scripts/06_map_min_time_with_mtr.py
python3 analysis/meeting3_checks/scripts/07_audit_feedback_local_cases.py
```

Generated files are written to `analysis/meeting3_checks/results/`. Script 02 uses the frozen 30-run and HSR routing outputs when newly generated raw files are absent.

## Repeat the additional R5 routing

After installing the locked R environment and Java 21, run:

```bash
Rscript analysis/meeting3_checks/scripts/01_additional_routing_checks.R
python3 analysis/meeting3_checks/scripts/02_analyse_additional_routing.py
```

R5 frequency routing is stochastic, so rerouted travel times need not be byte-identical. The frozen files preserve the evidence used in the dissertation.

The Shenzhen polygon is used only as a light contextual background in Figure 3.1; it is not used in routing or statistical analysis.
