# Training the book spine detection model

## Directory structure

```
train/
  obb/         OBB model (YOLO26n-obb) — Pi 5 refinement
    train1/    YOLO11s-obb, 10 epochs (exploration)
    train2/    YOLO11n-obb, 100 epochs, mAP50=0.972 — previous best
    train3/    YOLO26n-obb, 100 epochs, mAP50=0.951
    train4/    YOLO26n-obb, 200 epochs, mAP50=0.959
    train5/    YOLO26n-obb, P2 dataset — current
    train_obb.sh
  aabb/        AABB model (YOLO11n) — IMX500 on-chip inference
    train1/    YOLO11n-detect, P2 dataset, 200 epochs, mAP50=0.959 — current
    train_aabb.sh
```

Each run contains: `args.yaml` (hyperparameters), `results.csv` (per-epoch metrics), `weights/best.pt` and `weights/last.pt`.

Production models are stored under `models/obb/` and `models/aabb/` — see `models/README.md`.

---

## Starting a training run

**OBB model (Pi 5, YOLO26n-obb, imgsz=640):**
```bash
./train/obb/train_obb.sh              # train5, 200 epochs
./train/obb/train_obb.sh train5 yolo26n-obb.pt 200
```

**AABB model (IMX500, YOLO11n-detect, imgsz=320):**
```bash
./train/aabb/train_aabb.sh            # train1, 200 epochs
./train/aabb/train_aabb.sh train1 yolo11n.pt 200
```

Both scripts start fresh if no checkpoint exists, resume automatically after a crash, and exit cleanly when done. After training, consolidate `runs/` into the appropriate `trainN/` folder and copy the model to `models/`.

### Resuming manually after a crash
```bash
yolo train resume=True model=runs/obb/train5/weights/last.pt
yolo train resume=True model=runs/detect/train1/weights/last.pt
```

---

## Validation

```bash
# OBB (train5)
yolo task=obb mode=val \
  model=train/obb/train5/weights/best.pt \
  "data=datasets/Book spine detection P2.obb/data.yaml"

# AABB (train1)
yolo task=detect mode=val \
  model=train/aabb/train1/weights/best.pt \
  "data=datasets/Book spine detection P2.aabb/data.yaml"
```

---

## Export for edge deployment

**OBB model → NCNN (Pi 5 CPU):**
```bash
yolo export model=train/obb/train5/weights/best.pt format=ncnn imgsz=640
```

**AABB model → IMX500:**
```bash
yolo export model=train/aabb/train1/weights/best.pt format=imx500 imgsz=320
```

---

## Prediction

```bash
yolo task=obb mode=predict \
  model=train/obb/train5/weights/best.pt \
  conf=0.3 source=example-files/books/Books_00005.png save=True
```
