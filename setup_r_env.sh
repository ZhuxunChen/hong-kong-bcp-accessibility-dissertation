#!/usr/bin/env bash
set -euo pipefail

if ! command -v Rscript >/dev/null 2>&1; then
  echo "Rscript is required. Install R 4.5.1, then rerun this script." >&2
  exit 2
fi

# Install the project manager outside the activated project when necessary.
Rscript --vanilla -e 'if (!requireNamespace("renv", quietly = TRUE)) install.packages("renv", repos = "https://cloud.r-project.org")'
Rscript -e 'renv::restore(prompt = FALSE); renv::status()'
