import os
import sys
import argparse
import logging
from datetime import datetime

import config  # Do this here to ensure logging is configured early

import cv2
from ultralytics import YOLO

# Make "libs" module path available
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs'))

from libs import initialize as initialize_libs
from libs.general_utils import get_next_directory
from libs.image_utils import preprocess_for_text_area_detection, extractAndRotateImage
from libs.text_utils import clean_ocr_text, match_to_words, match_to_titles, select_best_title, compute_validity_score
from libs.ocr_utils import ocr_onImage
from libs.lookup_utils import lookup_book_details

from libs.database_manager import DatabaseManager

TIMESTR_FORMAT = "%d.%m.%Y %H:%M"


class BookFinder:
    
    def __init__(self, debug=0, log_handler=None, db_manager=None):
        
        self.debug = debug
        self.log_handler = log_handler
        self.on_detection = None  # Callback für neue Detections

        # Set debug level for logging
        if self.debug >= 1:
            logging.getLogger().setLevel(logging.DEBUG)

        # Add the provided log handler, if any
        if self.log_handler:
            logging.getLogger().addHandler(self.log_handler)
            logging.info("A handler has been added to the logger.")

        # Initialize all necessary modules
        initialize_libs()

        # Initialize or use provided DatabaseManager
        if db_manager:
            self.db_manager = db_manager
        else:
            # Fallback: Create new DatabaseManager if none provided
            self.DB_PATH = os.path.join(config.HOME_DIR, "bookshelves.db")
            self.db_manager = DatabaseManager(self.DB_PATH)

        # Set default source
        # source_default = 'https://ultralytics.com/images/bus.jpg'
        # source_default = config.HOME_DIR+'/example-files/IMG_3688.png'
        # source_default = config.HOME_DIR+'/example-files/books'
        # source_default = config.HOME_DIR+'/example-files/books.mov'
        self.source_default = os.path.join(config.HOME_DIR, 'example-files/books/books_00005.png')


    def findBooks(self, source):
        """
        Execute the book detection and lookup process.
        """
        run_id = None
        books_detected = 0

        # Use default source if not provided
        source = source or self.source_default

        # Record the start time of the run and log it in the database
        start_time = datetime.now()
        run_id = self.db_manager.log_run_start(start_time.isoformat())

        timeStr = start_time.strftime(TIMESTR_FORMAT)
        logging.info(f"=== Book detection starts at {timeStr} ===")

        # --- Detectbook spines in image ---

        # Load a model
        # model = YOLO("yolo11s.pt", )  # load an official model
        # model = YOLO("yolo11s-seg.pt")  # load an official model (instance segmentation)
        # model = YOLO(config.HOME_DIR+"/runs/obb/train/weights/best.pt")  # load my custom model (Oriented Bounding Boxes Object Detection)
        # model = YOLO(config.HOME_DIR+"/runs/segment/train/weights/best.pt")  # load my custom model
        model = YOLO(os.path.join(config.MODEL_DIR, "detect-book-spines.pt"))

        # Predict with the model
        results = model.predict(source, conf=0.5)

        # --- Process and store book spine images ---

        # Create the output directory, if needed
        output_dir = get_next_directory(config.OUTPUT_DIR)
        os.makedirs(os.path.join(output_dir, "book"), exist_ok=True)

        # Get only filename with no directories and no extension
        filename = os.path.splitext(os.path.basename(source))[0]

        # Load the pre-trained EAST model
        logging.debug("Loading EAST text detector...")
        east_model_path = os.path.join(config.MODEL_DIR, "east_text_detection.pb")
        east_model = cv2.dnn.readNet(east_model_path)

        with open(os.path.join(output_dir, "results.json"), "w") as text_file:

            # Process results
            for result in results:

                if len(result) > 0:
                    
                    logging.debug(result.to_json())  # Entferne file=text_file
                
                    for idx, obb in enumerate(result.obb.xyxyxyxy):

                        # Check if the detection is of the "book" class
                        if "book" in result.names.values():
                            books_detected += 1

                            logging.info(f"Book {idx} found")

                            # --- Extract and pre-process the detected book spine images ---

                            # Convert the OBB to a rectangle
                            points = obb.cpu().numpy().reshape((-1, 1, 2)).astype(int)
                            rect = cv2.minAreaRect(points)

                            # Rotate the image slightly so that it aligns with the axes.
                            img_cropped = extractAndRotateImage(result.orig_img, rect)

                            # Ensure the image is wider than tall and also return a variant rotated by 180 degrees.
                            img, img_rotated_180 = preprocess_for_text_area_detection(img_cropped)

                            # Generate a unique detection ID for this detection within the run
                            detection_id = f"{idx}"

                            # Log the detection in the detections table
                            detection_id = self.db_manager.log_detection_entry(run_id)

                            # Calculate the image paths once
                            original_image_path = os.path.join(output_dir, "book", f"{filename}_{idx}.jpg")
                            rotated_image_path = os.path.join(output_dir, "book", f"{filename}_rotated-180_{idx}.jpg")

                            cv2.imwrite(original_image_path, img)
                            cv2.imwrite(rotated_image_path, img_rotated_180)


                            # --- Perform OCR on the book image ---

                            # Perform OCR on all (both) image variants.
                            image_variants = [
                                (img, original_image_path),  # Original image
                                (img_rotated_180, rotated_image_path)  # 180-degree rotated image
                            ]

                            # Iterate over each variant, process the OCR, and print the result
                            for variant_img, variant_path in image_variants:

                                logging.info(f"{variant_path} ->")

                                detected_texts = ocr_onImage(variant_img, east_model, self.debug)

                                valid_text_regions = {}
                                for region, detected_text in detected_texts.items():
                                    cleaned_text = clean_ocr_text(detected_text)

                                    # Step 1: Apply word correction
                                    corrected_text = match_to_words(cleaned_text)

                                    # Step 2: Compute validity AFTER correction
                                    corrected_validity_score = compute_validity_score(corrected_text)

                                    logging.debug(f"    {region}: '{cleaned_text}' -> '{corrected_text}' (Bewertung: {corrected_validity_score:.2f} [ignored])")

                                    valid_text_regions[region] = corrected_text

                                    # Only keep high-validity text
                                    #if corrected_validity_score > 0.3:  # Threshold (adjust as needed)
                                    #    valid_text_regions[region] = corrected_text
                                    #else:
                                    #    logging.info(f"    ❌ Discarding low-confidence OCR result {cleaned_text}.")


                                corrected_text = ' '.join(valid_text_regions.values()).strip()
                                logging.debug(f"    corrected title: {corrected_text}")

                                matched_title = match_to_titles(corrected_text)
                                logging.debug(f"    matched title: {matched_title}")

                                best_title = select_best_title(corrected_text, matched_title)
                                logging.info(f"📚 Best title: {best_title}")

                                # Buchdetails abrufen
                                book_details = lookup_book_details(best_title)
                                if book_details:
                                    logging.info(f"📖 Gefundene Buchdetails: {book_details}")

                                # Log the title we've associated with this variant.
                                self.db_manager.log_detection_variant(detection_id, variant_path, best_title)

                                # Sende Detection-Event über den Callback
                                if self.on_detection:
                                    detection_data = {
                                        'id': detection_id,
                                        'image_path': variant_path,
                                        'title': best_title,
                                        'book_details': book_details
                                    }
                                    self.on_detection(detection_data)

                        else:
                            logging.info("Skipping ", result.names[idx], '...')

        # Record the end time of the run
        end_time = datetime.now()
        # Update the run statistics in the database
        self.db_manager.update_run_statistics(run_id, end_time.isoformat(), books_detected)

        timeStr = end_time.strftime(TIMESTR_FORMAT)
        logging.info(f"=== Book detection concludes at {timeStr}. #Books detected: {books_detected}. ===")
