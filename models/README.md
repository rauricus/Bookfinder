# Trained Models

All models detect a single class (`book-spine`) using Oriented Bounding Boxes (OBB).
The active model used in production is **YOLO11-obb-n/detect-book-spines.train2.pt**.

## Overview

| Run | File | Architektur | Dataset | imgsz | Epochen | mAP50 | mAP50-95 | Precision | Recall |
|-----|------|-------------|---------|-------|---------|-------|----------|-----------|--------|
| train1 | `YOLO11-obb-s/detect-book-spines.train1.pt` | YOLO11s-obb | Book_Spine_2 | 640 | 10 | 0.200 | 0.153 | 0.825 | 0.074 |
| **train2** ✓ | **`YOLO11-obb-n/detect-book-spines.train2.pt`** | YOLO11n-obb | Book spine detection v2 | 320 | 100 | **0.972** | **0.807** | **0.963** | **0.940** |
| train3 | `YOLO26-obb-n/detect-book-spines.train3.pt` | YOLO26n-obb | Book spine detection v2 | 320 | 100 | 0.951 | 0.765 | 0.912 | 0.891 |

## Anmerkungen

**train1** — Erster Explorationsrun. Anderes Dataset (`Book_Spine_2`) und grössere Bildgrösse (640). Nach 10 Epochen noch nicht konvergiert; kein fairer Vergleich mit train2/train3.

**train2** — Vollständiges Training auf dem finalen Dataset. Bestes Modell, aktiv in `libs/book_finder.py`. Ergebnisse: `train/train2/`.

**train3** — Test mit YOLO26n-obb (neuere Architektur). Gleiches Dataset und Parameter wie train2, jedoch schlechtere Resultate (−2.1% mAP50). Ergebnisse: `train/train3/` (results.csv enthält nur Epochen 83–100, da Training nach Projektumzug aufgeteilt wurde).
