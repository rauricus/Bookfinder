# Training the book spine detection model

## Current model: YOLO26n-obb (train3)

Training migrated from YOLO11n-obb to YOLO26n-obb in May 2026. YOLO26 is 43% faster on CPU,
NMS-free (simpler edge export), and supports OBB. Requires `ultralytics 8.4.*`.

### Train

```bash
yolo task=obb mode=train \
  model=yolo26n-obb.pt \
  data="datasets/Book spine detection.v2.yolo8-obb/data.yaml" \
  device=mps epochs=100 imgsz=320 batch=16 patience=100 \
  project=train name=train3
```

Key parameters:
- `imgsz=320`: kept at 320 to fit within IMX500's ~8 MB weight memory limit
- `device=mps`: Apple Silicon GPU; change to `cpu` or `cuda:0` as needed
- No `dfl` loss weight — DFL is removed in YOLO26

### Validate (benchmark against train2 baseline)

```bash
# YOLO26 (new)
yolo task=obb mode=val \
  model=train/train3/weights/best.pt \
  data="datasets/Book spine detection.v2.yolo8-obb/data.yaml"

# YOLO11 baseline (train2) — target to beat
yolo task=obb mode=val \
  model=models/YOLO11-obb-n/detect-book-spines.train2.pt \
  data="datasets/Book spine detection.v2.yolo8-obb/data.yaml"
```

Baseline (train2): mAP50 = 0.972, mAP50-95 = 0.807, precision = 0.963, recall = 0.939

### Export for edge deployment

**Track A — NCNN (Pi 5 CPU, ~14–15 FPS at 320×320):**
```bash
yolo export model=train/train3/weights/best.pt format=ncnn imgsz=320
```
Produces `best_ncnn_model/` with `.param` and `.bin` files. Runs without ultralytics on the Pi.

**Track B — IMX500 (on-chip inference, OBB support untested):**
```bash
yolo export model=train/train3/weights/best.pt format=imx500 imgsz=320
```
If OBB ops are unsupported by the Sony converter, fall back to Track A or retrain as
standard detection (`task=detect`) for IMX500.

### Predict

```bash
yolo task=obb mode=predict \
  model=train/train3/weights/best.pt \
  conf=0.3 source=example-files/books/Books_00005.png save=True
```

---

## Previous model: YOLO11n-obb (train2)

Kept for reference. Model weights: `models/YOLO11-obb-n/detect-book-spines.train2.pt`

```bash
# Train (YOLO11, for reference only)
yolo task=obb mode=train \
  model=yolo11n-obb.pt \
  data="datasets/Book spine detection.v2.yolo8-obb/data.yaml" \
  device=mps epochs=100 imgsz=320 batch=16 \
  project=train name=train2

# Predict
yolo task=obb mode=predict \
  model=models/YOLO11-obb-n/detect-book-spines.train2.pt \
  conf=0.3 source=example-files/books/Books_00005.png save=True
```
