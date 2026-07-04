#!/usr/bin/env zsh

# Exports the AABB book-spine detector to Sony IMX500 format inside an x86_64 Linux container.
#
# WHY: Ultralytics `format=imx` export is Linux + x86_64 only, so it cannot run on the arm64 Mac
# or the arm64 Pi. This wraps the whole toolchain in a linux/amd64 container (emulated on Apple
# Silicon). Works with any `docker`-compatible CLI (Docker Desktop, Colima, etc.).
#
# Usage: ./deploy/imx500/export_imx500.sh [model] [data] [imgsz] [fraction]
#   model     .pt model to export   (default: models/aabb/YOLO11-n/detect-book-spines.train1.pt)
#   data      calibration data.yaml (default: datasets/Book spine detection P2.aabb/data.yaml)
#   imgsz     export input size     (default: 320 — matches training; fits the sensor budget)
#   fraction  calibration subset    (default: 0.5 — ~535 of the 1069 val images for INT8 PTQ;
#             Sony recommends >300. Calibration = forward passes to size the int8 ranges, no labels.)
#
# Output: an Ultralytics "<model_stem>_imx_model/" directory next to the model file, containing
# packerOut.zip, labels.txt, model_imx.onnx and the memory report.

set -e
cd "${0:A:h}/../.."  # always run relative to project root

MODEL="${1:-models/aabb/YOLO11-n/detect-book-spines.train1.pt}"
DATA="${2:-datasets/Book spine detection P2.aabb/data.yaml}"
IMGSZ="${3:-320}"
FRACTION="${4:-0.5}"

IMAGE="bookfinder-imx500-export"

# A docker-compatible CLI is required (Docker Desktop or Colima both provide `docker`).
if ! command -v docker >/dev/null 2>&1; then
  echo "Error: no 'docker' CLI found. Install a linux/amd64-capable runtime first," >&2
  echo "       e.g. Colima:  brew install colima docker && colima start --arch x86_64" >&2
  exit 1
fi

echo "==> Building export image (${IMAGE}, linux/amd64)…"
docker build --platform linux/amd64 -t "$IMAGE" -f deploy/imx500/Dockerfile deploy/imx500

echo "==> Running IMX500 export…"
echo "    model=$MODEL  imgsz=$IMGSZ  fraction=$FRACTION"
EXPORT_DIR="${MODEL%.pt}_imx_model"
# Bind-mount the repo so the container sees the model + dataset and writes results back to the host.
# Clear any stale (root-owned) export dir first — the container runs as root and can remove it.
docker run --rm --platform linux/amd64 \
  -v "$PWD":/workspace \
  -w /workspace \
  "$IMAGE" \
  bash -c "rm -rf '$EXPORT_DIR' && yolo export model='$MODEL' format=imx data='$DATA' imgsz='$IMGSZ' fraction='$FRACTION'"

echo "==> Done. Look for '<model>_imx_model/' next to: $MODEL"
