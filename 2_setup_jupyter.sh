#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV_FILE='yolo11.condaenv.yml'
CONDA_ENV="yolo11"

KERNEL_DISPLAY_NAME="Python 3 ($CONDA_ENV)"

# === INITIALIZATION ===

# Note that we currently DO NOT initialize homebrew here as fallback after conda.

# --- Initialize micromamba
# 	  The following code is copied from "micromamba shell init"
export MAMBA_EXE='/opt/homebrew/opt/micromamba/bin/micromamba';
export MAMBA_ROOT_PREFIX='/Users/andreas/micromamba';
__mamba_setup="$("$MAMBA_EXE" shell hook --shell zsh --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"  # Fallback on help from mamba activate
fi
unset __mamba_setup
# <<< mamba initialize <<<


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
