#!/usr/bin/env zsh

# Trains a YOLO26 OBB model and resumes automatically after crashes.
# Requires the bookfinder environment to be active.
#
# Usage: ./train/train.sh [name] [model] [epochs]
#   name    Training run name (default: train4)
#   model   Base model file   (default: yolo26n-obb.pt)
#   epochs  Number of epochs  (default: 200)
#
# Examples:
#   ./train/train.sh                               # train4 with yolo26n-obb.pt, 200 epochs
#   ./train/train.sh train4 yolo26n-obb.pt 100    # train4 with 100 epochs
#   ./train/train.sh train5 yolo26n-obb.pt 200    # train5

cd "${0:A:h}/.."  # always run relative to project root

NAME="${1:-train4}"
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
      "data=datasets/Book spine detection.v2.yolo8-obb/data.yaml" \
      device=mps epochs=$EPOCHS imgsz=320 batch=16 patience=100 \
      lr0=0.005 \
      name="$NAME"
  fi
  [[ $? -eq 0 ]] && break
  echo "Crashed (exit $?), resuming in 5s..."; sleep 5
done
