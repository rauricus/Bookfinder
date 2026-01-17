This is a retrained "nano" YOLO11 OBB model. 

For training, I used a V2 of my Bookspine dataset (datasets/Book spine detection.v2.yolo8-obb) 
and 100 epochs. The original model was based on "small" YOLO11 OBB, was trained with a smaller 
dataset and only few epochs (10?).

The goal of using a smaller model, but train it longer, is to be able to make it run smoother
on a Raspberry Pi and maybe even on the AI camera (optimized ONNX), if it should fit.
