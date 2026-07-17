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

STAGE="analysis/stage9a"
REFERENCE="reference_outputs/stage9a"
if [[ -e "$STAGE/inputs" || -e "$STAGE/results" || -e "$STAGE/runs" || -e "$STAGE/network" ]]; then
  echo "Refusing to overwrite an existing Stage 9A run. Use a clean clone." >&2
  exit 3
fi

cp -R "$REFERENCE/inputs" "$STAGE/inputs"
mkdir -p "$STAGE/results"
cp "$REFERENCE/results/travel_time_matrix_tpu_v3.csv" "$STAGE/results/"
cp "$REFERENCE/results/travel_time_matrix_stpug_v3.csv" "$STAGE/results/"
cp "$REFERENCE/results/routing_uncertainty_v3.json" "$STAGE/results/"

MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-dissertation}" "$PYTHON" "$STAGE/scripts/05_reanalysis_v3.py"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-dissertation}" "$PYTHON" "$STAGE/scripts/06_figures_and_outputs_v3.py"

cp "$REFERENCE/results/omitted_origin_audit_tpu_v3.csv" "$STAGE/results/"
cp "$REFERENCE/results/omitted_origin_audit_stpug_v3.csv" "$STAGE/results/"
cp "$REFERENCE/results/omitted_origin_audit_summary_v3.csv" "$STAGE/results/"

"$PYTHON" "$STAGE/scripts/08_stage9a_manifest.py"
"$PYTHON" tools/compare_reproduction.py --strict
