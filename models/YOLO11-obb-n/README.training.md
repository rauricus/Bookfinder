# OBB object detection using the Book-spine-detection.v1-fit-within-320x320 dataset
This model was retrained on a yolo11n-obb model using the following command.

```
yolo task=obb mode=train model=yolo11n-obb.pt data=<PROJ_DIR>/datasets/Book-spine-detection.v1-fit-within-320x320.yolov11/data.yaml project=train device=MPS epochs=100 imgsz=320 plots=False workers=4 nms=True conf=0.30 iou=0.65 max_det=200
```

This is supposed to be faster and seems to show NMS warnings less frequently during the val phase in later epochs (AI advice).

## If a training aborts or gets stuck, here's how to resume it.
```
yolo task=obb mode=train model=train/train2/weights/last.pt data=<PROJ_DIR>/datasets/Book-spine-detection.v1-fit-within-320x320.yolov11/data.yaml project=train device=MPS epochs=100 imgsz=320 plots=False workers=4 nms=True conf=0.30 iou=0.65 max_det=200 resume=true
```

## The following is the final, more thorough val round at the end, which also produces plots.
yolo task=obb mode=val model="<path to training results>/weights/best.pt" \
  data="<PROJ_DIR>/datasets/Book-spine-detection.v1-fit-within-320x320.yolov11/data.yaml" device=MPS imgsz=320 \
  nms=True conf=0.10 iou=0.65 max_det=300 plots=True