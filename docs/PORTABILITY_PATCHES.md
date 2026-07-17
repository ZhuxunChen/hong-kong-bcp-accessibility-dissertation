# Portability Patches Applied Before Packaging

Two non-analytical clean-run defects were fixed on 17 July 2026:

1. `01_prepare_spatial_inputs_v3.R` no longer reads the legacy `analysis/data_prepared/census_clean.csv` merely to populate an audit sentence. Census attributes are read directly from the retained 2021 workbook.
2. `05_reanalysis_v3.py` reads the two preliminary comparison files from the explicitly labelled `analysis/stage9a/reference_inputs/preliminary_baseline/` directory instead of the superseded Stage 6.5 workspace.

The patches do not change routing, model fitting, figures or the numerical results reported in v27. The pre-patch 78-file manifest is preserved under `reference_outputs/stage9a/provenance/`; the corrected 82-file manifest is the current source record.
