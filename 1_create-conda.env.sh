#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV_FILE='yolo11.condaenv.yml'
CONDA_ENV="yolo11"

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


# Function to check, if a specific conda environment exists
#    See: https://stackoverflow.com/questions/70597896/check-if-conda-env-exists-and-create-if-not-in-bash
conda_env_exists() {
    micromamba env | grep "${@}" >/dev/null 2>/dev/null
}


# === MAIN ===

# --- Create or update my conda environment for AI
if conda_env_exists ".*$CONDA_ENV.*" ; then
	echo "Updating conda environment '$CONDA_ENV'..."
	echo
	micromamba update -n $CONDA_ENV --file $CONDA_ENV_FILE --prune
	echo
	echo "Conda environment '$CONDA_ENV' updated."
else
	echo "Creating conda environment '$CONDA_ENV'..."
	echo
	micromamba create -n $CONDA_ENV -f $CONDA_ENV_FILE
fi

# Activate conda env and check if Yolo is ok.
micromamba activate $CONDA_ENV  

echo "Running YOLO checks..."
echo

yolo checks

echo
echo "Done."
