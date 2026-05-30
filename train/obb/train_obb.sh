#!/usr/bin/env zsh

# Trains a YOLO26n OBB model (Pi 5) and resumes automatically after crashes.
# Requires the bookfinder environment to be active.
#
# Usage: ./train/obb/train_obb.sh [name] [model] [epochs]
#   name    Training run name (default: train5)
#   model   Base model file   (default: yolo26n-obb.pt)
#   epochs  Number of epochs  (default: 200)
#
# Examples:
#   ./train/obb/train_obb.sh                            # train5, 200 epochs
#   ./train/obb/train_obb.sh train5 yolo26n-obb.pt 200

cd "${0:A:h}/../.."  # always run relative to project root

NAME="${1:-train5}"
MODEL="${2:-yolo26n-obb.pt}"
EPOCHS="${3:-200}"

WEIGHTS="runs/obb/${NAME}/weights/last.pt"
RESULTS="runs/obb/${NAME}/results.csv"

epochs_done() { [[ -f "$RESULTS" ]] && echo $(( $(wc -l < "$RESULTS") - 1 )) || echo 0; }

while true; do
  if [[ $(epochs_done) -ge $EPOCHS ]]; then
    echo "Training complete ($(epochs_done)/$EPOCHS epochs)."
    break
  elif [[ -f "$WEIGHTS" ]]; then
    yolo train resume=True model="$WEIGHTS"
  else
    yolo task=obb mode=train \
      model="$MODEL" \
      "data=datasets/Book spine detection P2.obb/data.yaml" \
      device=mps epochs=$EPOCHS imgsz=640 batch=8 patience=50 \
      lr0=0.01 \
      degrees=15 shear=5 perspective=0.001 hsv_v=0.4 blur=0.01 \
      name="$NAME"
  fi
  [[ $? -eq 0 ]] && break
  echo "Crashed (exit $?), resuming in 5s..."; sleep 5
done
