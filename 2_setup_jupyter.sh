#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV_FILE='yolo11.condaenv.yml'
CONDA_ENV="yolo11"

KERNEL_DISPLAY_NAME="Python 3 ($CONDA_ENV)"

# === INITIALIZATION ===

# Note that we currently explicitely DO NOT initialize homebrew here as fallback after conda.

# Initialize micromamba
eval "$(micromamba shell hook --shell zsh)"


# === MAIN ===

# Activate conda env and check if Yolo is ok.
micromamba activate $CONDA_ENV  

echo "Installing ipykernel for '$CONDA_ENV' ..."
echo

python -m ipykernel install --user --name $CONDA_ENV --display-name $KERNEL_DISPLAY_NAME

echo
echo "Done."
echo
echo "=== Make sure you select kernel '${KERNEL_DISPLAY_NAME}' when executing a notebook. ==="
