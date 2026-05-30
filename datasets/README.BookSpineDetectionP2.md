# Book Spine Detection P2

Roboflow project: book-spine-detection-p2 (book-detection workspace)

## Downloads

Dataset version **V1**, exported 2026-05-30. Download URLs are stored in `.env`
(`DATASET_P2_OBB_URL`, `DATASET_P2_AABB_URL`) — the training scripts download
automatically if the dataset folder is missing.

To re-export manually from Roboflow:
- Project: https://app.roboflow.com/book-detection/book-spine-detection-p2/1
- OBB export: YOLOv8 OBB, no resize, auto-orient → `datasets/Book spine detection P2.obb/`
- AABB export: YOLOv8 Detection, no resize, auto-orient → `datasets/Book spine detection P2.aabb/`

## Goal

Two models trained from a single shared dataset:
- OBB model (YOLO26n-obb) for OBB refinement on the Raspberry Pi 5
- AABB model (YOLO11n) for on-chip inference on the Raspberry Pi AI Camera (IMX500)

## Structure

One Roboflow project (Instance Segmentation), exported twice in different formats.
Roboflow free tier limit: 10k images — koteitan excluded for this reason.

### Sources (all at original resolution, no resize)
- "book spine" search
  - [Book spine instance segmentation — Harald Varner](https://universe.roboflow.com/harald-varner-xv5u7/book-spine-instance-segmentation) (~1460 images)
  - [Book spine dataset-library — CNU HMLAB SYKO and ASH](https://universe.roboflow.com/cnu-hmlab-syko-and-ash/book-spine-dataset-library) (~312 images)
  - [book spine seg — emptybookslotdetect](https://universe.roboflow.com/emptybookslotdetect/book-spine-seg) (~307 images)
  - [Book Spine Segmentation — Leo Ueno](https://universe.roboflow.com/leo-ueno/book-spine-segmentation) (~193 images)
  - [book-spine-segmentation — airxiechao](https://universe.roboflow.com/airxiechao/book-spine-segmentation-eeyye) (~79 images)
  - [book spine — gj](https://universe.roboflow.com/gj-lhoxn/book-spine-unckc) (~63 images)
- "book" search
  - [book spline detection — books](https://universe.roboflow.com/books-26cz6/book-spline-detection) (~1421 images)
  - [book-seg - temp](https://universe.roboflow.com/temp-qwf82/book-seg-s562a) (~2126 images)
  - [Book Spine Detection — noktahesefe](https://universe.roboflow.com/noktahesefe/book-spine-detection-egfyh) (~1110 images, OD converted to Instance Seg)
    - Originally an Object Detection project with polygon annotations
    - Converted via COCO JSON export → re-imported as Instance Segmentation

Augmentation in Roboflow: Rotation ±15° (produces real OBB rotation), Brightness ±25% (brighten + darken), Blur up to 2px.
Target: ~10k training images after augmentation.

### Exports
- **OBB model (Pi 5):** YOLOv8 OBB, no resize, auto-orient
- **AABB model (IMX500):** YOLOv8 Detection, no resize, auto-orient

## Training

OBB model (Pi 5):    yolo26n-obb.pt, imgsz=640
AABB model (IMX500): yolo11n.pt,     imgsz=320

Both with dynamic augmentation in training config (applied randomly each epoch):
  degrees=15, shear=5, perspective=0.001, hsv_v=0.4

No augmentation baked into the dataset — YOLO's dynamic augmentation is more effective
(random per epoch, 3× faster training than with a 3x augmented dataset).

## Notes

- Unify all class names to "book-spine".
- Train/val/test split: 80/10/10.
