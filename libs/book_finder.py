import os
import sys
import argparse
from datetime import datetime

import config  # Do this here to ensure logging is configured early

import cv2
from ultralytics import YOLO

# Make "libs" module path available
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'libs'))

from libs import initialize as initialize_libs
from libs.utils.general_utils import get_next_directory
from libs.utils.image_utils import preprocess_for_text_area_detection, extractAndRotateImage
from libs.utils.text_utils import clean_ocr_text, match_to_words, match_to_titles, select_best_title, compute_validity_score
from libs.utils.ocr_utils import ocr_onImage
from libs.utils.lookup_utils import lookup_book_details
from libs.logging import get_logger

# Module-specific logger that uses the module name as a prefix for log messages
logger = get_logger(__name__)

TIMESTR_FORMAT = "%d.%m.%Y %H:%M"


class BookFinder:
    
    def __init__(self, run, output_dir, debug=0):
        
        self.current_run = run
        self.output_dir = output_dir
        self.debug = debug
        
        self.on_detection = None  # Callback for new detections

        # Initialize all necessary modules
        initialize_libs()

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
        source = source or self.source_default

        # Record the start time of the run
        start_time = datetime.now()

        timeStr = start_time.strftime(TIMESTR_FORMAT)
        logger.info(f"=== Book detection starts at {timeStr} ===")

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

        # Convert source to relative path if it's a local file        
        rel_source = None
        if os.path.isfile(source):
            try:
                rel_source = os.path.relpath(source, config.HOME_DIR)
            except ValueError:
                # If the path is on a different drive or is a URL
                rel_source = source
        rel_output = os.path.relpath(self.output_dir, config.HOME_DIR)

        # Update the run with the input and output paths
        self.current_run.update_paths(input_file=rel_source, output_dir=rel_output)

        # Get only filename with no directories and no extension
        filename = os.path.splitext(os.path.basename(source))[0]

        # Load the pre-trained EAST model
        logger.debug("Loading EAST text detector...")
        east_model_path = os.path.join(config.MODEL_DIR, "east_text_detection.pb")
        east_model = cv2.dnn.readNet(east_model_path)

        books_detected = 0
        with open(os.path.join(self.output_dir, "results.json"), "w") as text_file:

            # Process results
            for result in results:

                if len(result) > 0:
                    logger.debug(result.to_json())
                    for idx, obb in enumerate(result.obb.xyxyxyxy):

                        # Check if the detection is of the "book" class
                        if "book" in result.names.values():
                            books_detected += 1

                            logger.info(f"Book {idx} found")

                            # --- Extract and pre-process the detected book spine images ---

                            # Convert the OBB to a rectangle
                            points = obb.cpu().numpy().reshape((-1, 1, 2)).astype(int)
                            rect = cv2.minAreaRect(points)

                            # Rotate the image slightly so that it aligns with the axes.
                            img_cropped = extractAndRotateImage(result.orig_img, rect)

                            # Ensure the image is wider than tall and also return a variant rotated by 180 degrees.
                            img, img_rotated_180 = preprocess_for_text_area_detection(img_cropped)
                            # Log the bookspine
                            bookspine_id = self.current_run.log_bookspine()
                            
                            # Save the original and rotated images
                            original_image_path = os.path.join(self.output_dir, "book", f"{filename}_{idx}.jpg")
                            rotated_image_path = os.path.join(self.output_dir, "book", f"{filename}_rotated-180_{idx}.jpg")

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

                                logger.info(f"{variant_path} ->")

                                detected_texts = ocr_onImage(variant_img, east_model, self.debug)

                                valid_text_regions = {}
                                for region, detected_text in detected_texts.items():
                                    cleaned_text = clean_ocr_text(detected_text)

                                    # Step 1: Apply word correction
                                    corrected_text = match_to_words(cleaned_text)

                                    # Step 2: Compute validity AFTER correction
                                    corrected_validity_score = compute_validity_score(corrected_text)

                                    logger.debug(f"    {region}: '{cleaned_text}' -> '{corrected_text}' (Rating: {corrected_validity_score:.2f} [ignored])")

                                    valid_text_regions[region] = corrected_text

                                    # Only keep high-validity text
                                    #if corrected_validity_score > 0.3:  # Threshold (adjust as needed)
                                    #    valid_text_regions[region] = corrected_text
                                    #else:
                                    #    logger.info(f"    ❌ Discarding low-confidence OCR result {cleaned_text}.")


                                corrected_text = ' '.join(valid_text_regions.values()).strip()
                                logger.debug(f"    corrected title: {corrected_text}")

                                matched_title = match_to_titles(corrected_text)
                                logger.debug(f"    matched title: {matched_title}")

                                best_title = select_best_title(corrected_text, matched_title)
                                logger.info(f"📚 Best title: {best_title}")

                                # Retrieve book details
                                source, book_details = lookup_book_details(best_title)
                                
                                # Log the variant and get the variant ID
                                variant_id = self.current_run.log_bookspine_variant(bookspine_id, variant_path, best_title)
                                
                                # Store book lookup results if found
                                if book_details:
                                    # Extract the raw response if available
                                    raw_response = None
                                    if "_raw_response" in book_details:
                                        raw_response = book_details.pop("_raw_response")
                                    
                                    # Log only basic fields, not the full details
                                    basic_info = {
                                        'title': book_details.get('title'),
                                        'authors': book_details.get('authors', book_details.get('author'))
                                    }
                                    logger.info(f"📖 Book details found in {source}: {basic_info}")
                                    
                                    # Store the lookup results in the database
                                    lookup_id = self.current_run.log_book_lookup(
                                        bookspine_variant_id=variant_id,
                                        source=source,
                                        book_details=book_details,
                                        raw_response=raw_response
                                    )
                                    logger.debug(f"Stored book lookup with ID {lookup_id} from source {source}")
                                
                                # Send data to the callback if registered
                                if self.on_detection:
                                    bookspine_data = {
                                        'id': bookspine_id,
                                        'image_path': variant_path,
                                        'title': best_title,
                                        'book_details': book_details,
                                        'source': source if book_details else None
                                    }
                                    self.on_detection(bookspine_data)

                        else:
                            logger.info("Skipping ", result.names[idx], '...')

        # Record the end time of the run
        end_time = datetime.now()
        # Update the run statistics and report end of detection run
        self.current_run.update_statistics(end_time.isoformat(), books_detected)
        
        timeStr = end_time.strftime(TIMESTR_FORMAT)
        logger.info(f"=== Book detection concludes at {timeStr}. #Books detected: {books_detected}. ===")
