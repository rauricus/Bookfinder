#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV="yolo11"
NOTEBOOK_DIR="$HOME/Documents/Projekte/Objekterkennung.$CONDA_ENV/notebooks"

# === INITIALIZATION ===

# Note that we currently DO NOT initialize homebrew here as fallback after conda as well.

# Initialize micromamba
eval "$(micromamba shell hook --shell zsh)"


# === MAIN ===

micromamba activate $CONDA_ENV

mkdir -p $NOTEBOOK_DIR

jupyter notebook \
    --notebook-dir=$NOTEBOOK_DIR --ip='*' --port=8888 \
    --no-browser --allow-root
