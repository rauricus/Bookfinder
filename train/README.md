# Training the book spine detection model

## Directory structure

Each completed training run is stored here:

```
train/
  train1/   YOLO11s-obb, 10 epochs, different dataset (exploration, not production)
  train2/   YOLO11n-obb, 100 epochs — best model, active in book_finder.py
  train3/   YOLO26n-obb, 100 epochs
```

Each run contains: `args.yaml` (hyperparameters), `results.csv` (per-epoch metrics), `weights/best.pt` and `weights/last.pt`.

The production models are also stored under `models/` — see `models/README.md`.

Plots (learning curves, confusion matrix, PR curves) are written by YOLO to `runs/` during training but are **not checked in**, as they can be regenerated at any time:

```bash
yolo task=obb mode=val \
  model=train/train2/weights/best.pt \
  data="datasets/Book spine detection.v2.yolo8-obb/data.yaml" \
  plots=True
```

---

## Starting a new training run

```bash
./train/train.sh              # train4 with yolo26n-obb.pt (next run)
./train/train.sh train4 yolo26s-obb.pt  # with the small variant
```

The script starts a fresh training if no checkpoint exists, resumes automatically after a crash, and exits cleanly once all epochs are done.

After training, manually consolidate `runs/` into `train/trainN/` and copy the model to `models/`.

Key parameters: `imgsz=320` (IMX500 memory limit), `device=mps` (change to `cpu` or `cuda:0` as needed).

### Resuming manually after a crash

```bash
yolo train resume=True model=runs/obb/trainN/weights/last.pt
```

---

## Validation

```bash
# train2 (active model)
yolo task=obb mode=val \
  model=train/train2/weights/best.pt \
  data="datasets/Book spine detection.v2.yolo8-obb/data.yaml"

# train3
yolo task=obb mode=val \
  model=train/train3/weights/best.pt \
  data="datasets/Book spine detection.v2.yolo8-obb/data.yaml"
```

---

## Export for edge deployment

**Track A — NCNN (Pi 5 CPU, ~14–15 FPS at 320×320):**
```bash
yolo export model=train/train2/weights/best.pt format=ncnn imgsz=320
```

**Track B — IMX500 (on-chip inference, OBB support untested):**
```bash
yolo export model=train/train2/weights/best.pt format=imx500 imgsz=320
```

---

## Prediction

```bash
yolo task=obb mode=predict \
  model=train/train2/weights/best.pt \
  conf=0.3 source=example-files/books/Books_00005.png save=True
```
