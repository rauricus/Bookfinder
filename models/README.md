# Trained Models

All models detect a single class (`book-spine`).
- **OBB models** (Pi 5 refinement): active model is **YOLO11-obb-n/detect-book-spines.train2.pt**
- **AABB models** (IMX500 on-chip inference): active model is **YOLO11-n/detect-book-spines.train1.pt**

## OBB Models (`models/obb/`)

| Run | File | Architecture | Dataset | imgsz | Epochs | mAP50 | mAP50-95 | Precision | Recall |
|-----|------|--------------|---------|-------|--------|-------|----------|-----------|--------|
| train1 | `YOLO11-obb-s/detect-book-spines.train1.pt` | YOLO11s-obb | Book_Spine_2 | 640 | 10 | 0.200 | 0.153 | 0.825 | 0.074 |
| **train2** ✓ | **`YOLO11-obb-n/detect-book-spines.train2.pt`** | YOLO11n-obb | Book spine detection v2 | 320 | 100 | **0.972** | **0.807** | **0.963** | **0.940** |
| train3 | `YOLO26-obb-n/detect-book-spines.train3.pt` | YOLO26n-obb | Book spine detection v2 | 320 | 100 | 0.951 | 0.765 | 0.912 | 0.891 |
| train4 | `YOLO26-obb-n/detect-book-spines.train4.pt` | YOLO26n-obb | Book spine detection v2 | 320 | 200 | 0.959 | 0.791 | 0.928 | 0.908 |

## AABB Models (`models/aabb/`)

| Run | File | Architecture | Dataset | imgsz | Epochs | mAP50 | mAP50-95 | Precision | Recall |
|-----|------|--------------|---------|-------|--------|-------|----------|-----------|--------|
| **train1** ✓ | **`YOLO11-n/detect-book-spines.train1.pt`** | YOLO11n-detect | Book spine detection P2 (aabb) | 320 | 200 | **0.959** | **0.810** | **0.949** | **0.932** |

## Notes — OBB

**obb/train1** — Initial exploration run. Different dataset (`Book_Spine_2`) and larger image size (640). Not converged after 10 epochs; not directly comparable to train2–4.

**obb/train2** — Full training on the final dataset. Best OBB model overall, active in `libs/book_finder.py`. Results: `train/obb/train2/`.

**obb/train3** — First YOLO26n-obb run. Same dataset and parameters as train2 (lr0=0.01, 100 epochs). Underperformed train2 by −2.1% mAP50, likely due to premature plateau. Results: `train/obb/train3/`.

**obb/train4** — YOLO26n-obb with lower learning rate (lr0=0.005) and 200 epochs. Improved over train3 (+0.7% mAP50, +2.6% mAP50-95) but still below train2 (−1.4% mAP50). Results: `train/obb/train4/`.

## Notes — AABB

**aabb/train1** — First AABB model (YOLO11n-detect) trained on P2 dataset for IMX500 on-chip inference. 200 epochs, imgsz=320, lr0=0.01. Best mAP50=0.9588 at epoch 146. Results: `train/aabb/train1/`.
