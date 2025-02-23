import os
import sys
import cv2
import argparse

# Make "libs" module path available
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs'))

from libs.general_utils import get_next_directory
from libs.image_utils import preprocess_for_text_area_detection, extractAndRotateImage
from libs.ocr_utils import ocr_onImage

from ultralytics import YOLO

HOME_DIR = os.getcwd()
OUTPUT_DIR = get_next_directory(os.path.join(HOME_DIR, "output/predict"))

def main():

    parser = argparse.ArgumentParser(description="Detect and OCR book spines from an image.")
    parser.add_argument("source", type=str, nargs='?', default=os.path.join(HOME_DIR, 'example-files/books/books_00005.png'), help="Path to the source image.")
    args = parser.parse_args()

    # source = 'https://ultralytics.com/images/bus.jpg'
    # source = HOME_DIR+'/example-files/IMG_3688.png'
    # source = HOME_DIR+'/example-files/books'
    # source = HOME_DIR+'/example-files/books.mov'
    source = args.source

    # --- Detect book spines in image ---

    # Load a model
    #model = YOLO("yolo11s.pt", )  # load an official model
    # model = YOLO("yolo11s-seg.pt")  # load an official model (instance segmentation)
    #model = YOLO(HOME_DIR+"/runs/obb/train/weights/best.pt")  # load my custom model (Oriented Bounding Boxes Object Detection)
    #model = YOLO(HOME_DIR+"/runs/segment/train/weights/best.pt")  # load my custom model
    model = YOLO(HOME_DIR+"/models/detect-book-spines.pt")

    # Predict with the model
    results = model.predict(source, conf=0.5)  

    # --- Process and store book spine images ---

    # Create the output directory, if needed
    os.makedirs(os.path.join(OUTPUT_DIR, "book"), exist_ok=True)

    # Get only filename with no directories and no extension
    filename = os.path.splitext(os.path.basename(source))[0]

    # Load the pre-trained EAST model
    print("[INFO] loading EAST text detector...")
    east_model_path = os.path.join(HOME_DIR, "notebooks", "east_text_detection.pb")
    east_model = cv2.dnn.readNet(east_model_path)


    with open(os.path.join(OUTPUT_DIR, "results.json"), "w") as text_file:

        # Process results
        for result in results:

            if len(result) > 0:
                
                print(result.to_json(), file=text_file)
            
                for idx, obb in enumerate(result.obb.xyxyxyxy):

                    # Check if the detection is of the "book" class
                    if result.names[idx] == 'book':

                        print(f"Book {idx} found")

                        # --- Extract and pre-process the detected book spine images ---

                        # Convert the OBB to a rectangle
                        points = obb.cpu().numpy().reshape((-1, 1, 2)).astype(int)
                        rect = cv2.minAreaRect(points)

                        # Rotate the image slightly so that it aligns with the axes.
                        img_cropped = extractAndRotateImage(result.orig_img, rect)

                        # Ensure the image is wider than tall and also return a variant rotated by 180 degrees.
                        img, img_rotated_180 = preprocess_for_text_area_detection(img_cropped)

                        cv2.imwrite(os.path.join(OUTPUT_DIR, "book", f"{filename}_{idx}.jpg"), img)
                        cv2.imwrite(os.path.join(OUTPUT_DIR, "book", f"{filename}_rotated-180_{idx}.jpg"), img_rotated_180)

                        # --- Perform OCR on the book image ---

                        # Perform OCR on all (both) image variants.
                        image_variants = [
                            (img, f"{filename}_{idx}.jpg"),  # Original image
                            (img_rotated_180, f"{filename}_rotated-180_{idx}.jpg")  # 180-degree rotated image
                        ]

                        # Iterate over each variant, process the OCR, and print the result
                        for variant_img, variant_filename in image_variants:
                            
                            detected_texts = ocr_onImage(variant_img, east_model)

                            # Display OCR results
                            print(f"{os.path.join(OUTPUT_DIR, 'book', variant_filename)} ->")
                            for region, text in detected_texts.items():
                                print(f"    {region}: {text}")

                    else:
                        print("Skipping", result.names[idx], '...')

if __name__ == "__main__":
    main()
