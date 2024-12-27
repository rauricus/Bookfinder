#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV_FILE='yolo11.condaenv.yml'
CONDA_ENV="yolo11"

MODEL_DIR="notebooks"
MODEL_NAME="east_text_detection.pb"

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

echo
echo

# --- Download model used for text area detection

if [ ! -f "$MODEL_DIR/$MODEL_NAME" ]; then
	
	echo "Downloading the EAST model for text area detection..."
	echo

	# This is coming from the OpenCV sample for text detection available here:
	# 		https://github.com/opencv/opencv/blob/master/samples/dnn/text_detection.py
	wget -O frozen_east_text_detection.tar.gz "https://www.dropbox.com/s/r2ingd0l3zt8hxs/frozen_east_text_detection.tar.gz?dl=1"
	tar -xvf frozen_east_text_detection.tar.gz
	rm frozen_east_text_detection.tar.gz

	mkdir -p $MODEL_DIR
	mv frozen_east_text_detection.pb $MODEL_DIR/$MODEL_NAME

	echo
	echo "Model downloaded and saved in '$MODEL_DIR'."
else
  echo "EAST model for text detection '$MODEL_DIR/$MODEL_NAME' already downloaded."
fi

echo
echo

# --- Check if YOLO is installed correctlyv
echo "Running YOLO checks..."
echo

yolo checks

echo
echo "Done."
