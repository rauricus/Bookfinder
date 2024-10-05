#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV="yolo11"
NOTEBOOK_DIR="$HOME/Documents/Projekte/Objekterkennung.$CONDA_ENV/notebooks"

# === INITIALIZATION ===

# Note that we currently DO NOT initialize homebrew here as fallback after conda as well.

# --- Initialize micromamba
#     The following code is copied from "micromamba shell init"
export MAMBA_EXE="/opt/homebrew/bin/micromamba";
export MAMBA_ROOT_PREFIX="/Users/andreas/micromamba";
__mamba_setup="$('/opt/homebrew/bin/micromamba' shell hook --shell zsh --prefix '/Users/andreas/micromamba' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    if [ -f "/Users/andreas/micromamba/etc/profile.d/micromamba.sh" ]; then
        . "/Users/andreas/micromamba/etc/profile.d/micromamba.sh"
    else
        export  PATH="/Users/andreas/micromamba/bin:$PATH"  # extra space after export prevents interference from conda init
    fi
fi
unset __mamba_setup


# === MAIN ===

micromamba activate $CONDA_ENV

mkdir -p $NOTEBOOK_DIR

jupyter notebook \
    --notebook-dir=$NOTEBOOK_DIR --ip='*' --port=8888 \
    --no-browser --allow-root
