#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${PYTHON_BOOTSTRAP:-}" ]]; then
  candidates=("$PYTHON_BOOTSTRAP")
else
  candidates=(
    python3.13
    python3.12
    /opt/homebrew/opt/python@3.12/bin/python3.12
    /usr/local/opt/python@3.12/bin/python3.12
    python3
  )
fi

PYTHON_BOOTSTRAP=""
for candidate in "${candidates[@]}"; do
  if command -v "$candidate" >/dev/null 2>&1 &&
    "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
    PYTHON_BOOTSTRAP="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BOOTSTRAP" ]]; then
  echo "Python 3.12 or newer is required by requirements.txt." >&2
  echo "Install it (for example: brew install python@3.12), or set PYTHON_BOOTSTRAP." >&2
  exit 2
fi

if [[ -x .venv/bin/python ]] &&
  ! .venv/bin/python -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
  echo "The existing .venv uses Python older than 3.12." >&2
  echo "Remove .venv and rerun this script." >&2
  exit 3
fi

"$PYTHON_BOOTSTRAP" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c 'import esda, geopandas, libpysal, mgwr, spreg, statsmodels; print("Python analysis environment is ready.")'
