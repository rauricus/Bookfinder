# To train object detection using the LibVision dataset

yolo task=detect mode=train model=yolo11s.pt data=/Users/andreas/Projekte/Objekterkennung.yolo11/datasets/data.yaml device=MPS epochs=10 imgsz=640 plots=True

yolo task=detect mode=predict model=/Users/andreas/Projekte/Objekterkennung.yolo11/runs/detect/train/weights/best.pt conf=0.25 source=/Users/andreas/Projekte/Objekterkennung.yolo11/datasets/test/images save=True

# To train instance segmentation using the Book_Spine_2 dataset

yolo task=segment mode=train model=yolo11s-seg.pt data=/Users/andreas/Projekte/Objekterkennung.yolo11/datasets/Book_Spine_2/data.yaml device=MPS epochs=10 imgsz=640 plots=True

yolo task=segment mode=predict model=/Users/andreas/Projekte/Objekterkennung.yolo11/runs/segment/train/weights/best.pt conf=0.25 source=/Users/andreas/Projekte/Objekterkennung.yolo11/datasets/Book_spine_2/test/images save=True 


# To train OBB object detection using the Book_Spine_2 dataset

yolo task=obb mode=train model=yolo11s-obb.pt data=/Users/andreas/Projekte/Objekterkennung.yolo11/datasets/Book_Spine_2/data.yaml device=MPS epochs=10 imgsz=640 plots=True

yolo task=obb mode=predict model=/Users/andreas/Projekte/Objekterkennung.yolo11/runs/obb/train/weights/best.pt conf=0.25 source=/Users/andreas/Projekte/Objekterkennung.yolo11/example-files/books/Books_00005.png save=True
