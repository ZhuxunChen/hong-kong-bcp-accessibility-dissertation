#!/usr/bin/env bash
set -euo pipefail

PYTHON_BOOTSTRAP="${PYTHON_BOOTSTRAP:-python3}"
"$PYTHON_BOOTSTRAP" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c 'import esda, geopandas, libpysal, mgwr, spreg, statsmodels; print("Python analysis environment is ready.")'
