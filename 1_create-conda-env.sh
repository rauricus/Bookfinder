#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV_FILE='yolo11.condaenv.yml'
CONDA_ENV="yolo11"

MODEL_DIR="notebooks"
MODEL_NAME="east_text_detection.pb"

# === INITIALIZATION ===

# Note that we currently DO NOT initialize homebrew here as fallback after conda.

# Initialize micromamba
eval "$(micromamba shell hook --shell zsh)"

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

	# This is coming from here:
	#		https://github.com/ZER-0-NE/EAST-Detector-for-text-detection-using-OpenCV
	# Another implementation I used earlier:
	# 		https://github.com/opencv/opencv/blob/master/samples/dnn/text_detection.py
	wget -O EAST-Detector.zip https://github.com/ZER-0-NE/EAST-Detector-for-text-detection-using-OpenCV/archive/refs/heads/master.zip

	mkdir tmp
	unzip -j -d tmp EAST-Detector.zip

	mkdir -p $MODEL_DIR
	mv tmp/frozen_east_text_detection.pb $MODEL_DIR/$MODEL_NAME

	rm -fr tmp
	rm EAST-Detector.zip

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
