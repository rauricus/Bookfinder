#!/usr/bin/env zsh

# Trains a YOLO11n AABB detection model (IMX500) and resumes automatically after crashes.
# Requires the bookfinder environment to be active.
#
# Usage: ./train/aabb/train_aabb.sh [name] [model] [epochs]
#   name    Training run name (default: train1)
#   model   Base model file   (default: yolo11n.pt)
#   epochs  Number of epochs  (default: 200)
#
# Examples:
#   ./train/aabb/train_aabb.sh                            # train1, 200 epochs
#   ./train/aabb/train_aabb.sh train1 yolo11n.pt 200

cd "${0:A:h}/../.."  # always run relative to project root

# Load environment variables
[[ -f .env ]] && source .env

# Download dataset if not present
DATASET_DIR="datasets/Book spine detection P2.aabb"
if [[ ! -d "$DATASET_DIR" ]]; then
  echo "Dataset not found, downloading from Roboflow..."
  [[ -z "$DATASET_P2_AABB_URL" ]] && echo "Error: DATASET_P2_AABB_URL not set in .env" && exit 1
  curl -L "$DATASET_P2_AABB_URL" -o /tmp/dataset_p2_aabb.zip
  mkdir -p "$DATASET_DIR"
  unzip /tmp/dataset_p2_aabb.zip -d "$DATASET_DIR"
  rm /tmp/dataset_p2_aabb.zip
  echo "Dataset ready."
fi

NAME="${1:-train1}"
MODEL="${2:-yolo11n.pt}"
EPOCHS="${3:-200}"

WEIGHTS="runs/detect/${NAME}/weights/last.pt"
RESULTS="runs/detect/${NAME}/results.csv"

epochs_done() { [[ -f "$RESULTS" ]] && echo $(( $(wc -l < "$RESULTS") - 1 )) || echo 0; }

while true; do
  if [[ $(epochs_done) -ge $EPOCHS ]]; then
    echo "Training complete ($(epochs_done)/$EPOCHS epochs)."
    break
  elif [[ -f "$WEIGHTS" ]]; then
    micromamba run -n bookfinder yolo train resume=True model="$WEIGHTS"
  else
    micromamba run -n bookfinder yolo task=detect mode=train \
      model="$MODEL" \
      "data=datasets/Book spine detection P2.aabb/data.yaml" \
      device=mps epochs=$EPOCHS imgsz=320 batch=16 patience=50 \
      lr0=0.01 \
      degrees=15 shear=5 perspective=0.001 hsv_v=0.4 \
      name="$NAME"
  fi
  [[ $? -eq 0 ]] && break
  echo "Crashed (exit $?), resuming in 5s..."; sleep 5
done
