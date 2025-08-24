#!/usr/bin/env zsh

# Requires: micromamba


CONDA_ENV_FILE='yolo11.condaenv.yml'
CONDA_ENV="yolo11"

MODEL_DIR="models"
MODEL_NAME="east_text_detection.pb"

DICT_DIR="dictionaries"

# === INITIALIZATION ===

# Note that we currently DO NOT initialize homebrew here as fallback after conda.

# Ensure that micromamba is available
# Note that this has to be called even if you have the init code in .zshrc
# because this script might be called from another shell or cron job (i.e. not interactive),
# so we cannot rely on .zshrc being executed.
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$HOME/micromamba}"
if [ -x "$MAMBA_ROOT_PREFIX/bin/micromamba" ]; then
  export MAMBA_EXE="$MAMBA_ROOT_PREFIX/bin/micromamba"
fi

if command -v micromamba >/dev/null 2>&1; then
  eval "$(micromamba shell hook --shell zsh)"
elif [ -n "${MAMBA_EXE:-}" ] && [ -x "$MAMBA_EXE" ]; then
  eval "$($MAMBA_EXE shell hook --shell zsh)"
else
  echo "micromamba not found; install it or set MAMBA_EXE=/full/path/to/micromamba" >&2
  exit 1
fi

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

# --- Download frequency dictionaries for SymSpell ---

# Create the directory if it does not exist
if [ ! -d "$DICT_DIR" ]; then
    echo "Creating dictionary directory: $DICT_DIR"
    mkdir -p "$DICT_DIR"
fi

# Dictionary URLs
declare -A DICTIONARIES
DICTIONARIES=(
    ["en"]="https://raw.githubusercontent.com/wolfgarbe/SymSpell/refs/heads/master/SymSpell.FrequencyDictionary/en-80k.txt"
    ["de"]="https://raw.githubusercontent.com/wolfgarbe/SymSpell/refs/heads/master/SymSpell.FrequencyDictionary/de-100k.txt"
    ["fr"]="https://raw.githubusercontent.com/wolfgarbe/SymSpell/refs/heads/master/SymSpell.FrequencyDictionary/fr-100k.txt"
    ["it"]="https://raw.githubusercontent.com/wolfgarbe/SymSpell/refs/heads/master/SymSpell.FrequencyDictionary/it-100k.txt"
)

# Loop through dictionaries and download only if missing
for lang in "${(@k)DICTIONARIES}"; do
    FILE_PATH="$DICT_DIR/frequency_${lang}.txt"
    if [[ ! -f "$FILE_PATH" ]]; then
        echo "Downloading $lang dictionary..."
        wget -q -O "$FILE_PATH" "${DICTIONARIES[$lang]}"
        if [[ $? -eq 0 ]]; then
            echo "Saved $lang dictionary to $FILE_PATH"
        else
            echo "Failed to download $lang dictionary!"
            rm -f "$FILE_PATH" # Remove partial file if download failed
        fi
    else
        echo "$lang dictionary already exists. Skipping download."
    fi
done

echo "All dictionaries are up to date."

echo
echo

# --- Check if YOLO is installed correctlyv
echo "Running YOLO checks..."
echo

yolo checks

echo
echo "Done."
