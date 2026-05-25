# Training the book spine detection model

## Current model: YOLO26n-obb (train3)

Training migrated from YOLO11n-obb to YOLO26n-obb in May 2026. YOLO26 is 43% faster on CPU,
NMS-free (simpler edge export), and supports OBB. Requires `ultralytics 8.4.*`.

### Train (with automatic resume on crash)

Use the included script from the project root:

```bash
./train/train.sh              # train3 with yolo26n-obb.pt (defaults)
./train/train.sh train4       # next run, same model
./train/train.sh train4 yolo26s-obb.pt  # next run with the small variant
```

The script starts a fresh training if no checkpoint exists, resumes automatically after
a crash, and exits cleanly once all epochs are done. See [train.sh](train.sh)
for the full implementation.

Key parameters: `imgsz=320` (IMX500 memory limit), `device=mps` (change to `cpu` or
`cuda:0` as needed).

Note: in ultralytics 8.4, `project=train name=train3` saves to `runs/obb/train/train3/`
(not `train/train3/` as in 8.3). This is expected behaviour.

### Resume manually after crash

```bash
yolo resume model=runs/obb/train/train3/weights/last.pt
```

### Validate (benchmark against train2 baseline)

```bash
# YOLO26 (new)
yolo task=obb mode=val \
  model=runs/obb/train/train3/weights/best.pt \
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
yolo export model=runs/obb/train/train3/weights/best.pt format=ncnn imgsz=320
```
Produces `best_ncnn_model/` with `.param` and `.bin` files. Runs without ultralytics on the Pi.

**Track B — IMX500 (on-chip inference, OBB support untested):**
```bash
yolo export model=runs/obb/train/train3/weights/best.pt format=imx500 imgsz=320
```
If OBB ops are unsupported by the Sony converter, fall back to Track A or retrain as
standard detection (`task=detect`) for IMX500.

### Predict

```bash
yolo task=obb mode=predict \
  model=runs/obb/train/train3/weights/best.pt \
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
