#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="${PYTHON_FALLBACK:-python3}"
fi
if ! "$PYTHON" -c 'import esda, geopandas, libpysal, mgwr, spreg, statsmodels' 2>/dev/null; then
  echo "Python analysis dependencies are missing." >&2
  echo "Run ./setup_python_env.sh, then rerun this script." >&2
  exit 2
fi

if ! Rscript -e 'packages <- c("r5r", "sf", "tidyverse", "data.table", "readxl", "tmap", "viridis"); quit(status = if (all(vapply(packages, requireNamespace, logical(1L), quietly = TRUE))) 0L else 1L)' 2>/dev/null; then
  echo "Locked R analysis dependencies are missing." >&2
  echo "Run ./setup_r_env.sh, then rerun this script." >&2
  exit 2
fi

Rscript analysis/stage9a/scripts/01_prepare_spatial_inputs_v3.R
Rscript analysis/stage9a/scripts/02_build_mtr_gtfs_bidirectional_v3.R
"$PYTHON" analysis/stage9a/scripts/03_validate_mtr_gtfs_v3.py
Rscript analysis/stage9a/scripts/04_route_repeated_v3.R
"$PYTHON" analysis/stage9a/scripts/05_aggregate_repeated_routes_v3.py
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-dissertation}" "$PYTHON" analysis/stage9a/scripts/05_reanalysis_v3.py
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-dissertation}" "$PYTHON" analysis/stage9a/scripts/06_figures_and_outputs_v3.py
Rscript analysis/stage9a/scripts/07_audit_omitted_origins_v3.R
"$PYTHON" analysis/stage9a/scripts/08_stage9a_manifest.py
"$PYTHON" tools/compare_reproduction.py
