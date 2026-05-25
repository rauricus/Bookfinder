#!/usr/bin/env zsh

# Trains a YOLO26 OBB model and resumes automatically after crashes.
# Requires the bookfinder environment to be active.
#
# Usage: ./train/train.sh [name] [model]
#   name   Training run name (default: train3)
#   model  Base model file   (default: yolo26n-obb.pt)
#
# Examples:
#   ./train/train.sh                          # train3 with yolo26n-obb.pt
#   ./train/train.sh train4                   # train4 with yolo26n-obb.pt
#   ./train/train.sh train4 yolo26s-obb.pt    # train4 with the small variant

cd "${0:A:h}/.."  # always run relative to project root

NAME="${1:-train3}"
MODEL="${2:-yolo26n-obb.pt}"
EPOCHS=100

WEIGHTS="runs/obb/train/${NAME}/weights/last.pt"
RESULTS="runs/obb/train/${NAME}/results.csv"

epochs_done() { [[ -f "$RESULTS" ]] && echo $(( $(wc -l < "$RESULTS") - 1 )) || echo 0; }

while true; do
  if [[ $(epochs_done) -ge $EPOCHS ]]; then
    echo "Training complete ($(epochs_done)/$EPOCHS epochs)."
    break
  elif [[ -f "$WEIGHTS" ]]; then
    yolo resume model="$WEIGHTS"
  else
    yolo task=obb mode=train \
      model="$MODEL" \
      "data=datasets/Book spine detection.v2.yolo8-obb/data.yaml" \
      device=mps epochs=$EPOCHS imgsz=320 batch=16 patience=100 \
      project=train name="$NAME"
  fi
  [[ $? -eq 0 ]] && break
  echo "Crashed (exit $?), resuming in 5s..."; sleep 5
done
