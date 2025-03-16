from PIL import Image

import cv2
import numpy as np

from libs.image_utils import cropImage, preprocess_for_ocr
from libs.text_utils import clean_ocr_text

import pytesseract

import config

def initialize():
    # Add any necessary initialization code here
    pass

def ocr_onImage(image, east_model, debug=0):
    """
    Perform OCR on an image, forcing horizontal text detection.

    Args:
        image_path (str): Path to the image for OCR.
        east_model (cv2.dnn_Net): The pre-trained EAST model

    Returns:
        str: The OCR-detected text.
    """

    # --- Detect text regions ---

    # Detect text regions using EAST
    boxes = detect_text_regions(image, east_model)

    # Visualize all bounding boxes found.
    if debug >= 1:
        showBoundingBoxes(image.copy(), boxes)

    # -- Perform OCR on text areas found ---
    ocr_results = {}

    for i, box in enumerate(boxes):

        # Get cropped image
        cropped_image = cropImage(image, box)
    
        # Apply pre-processing to enable better OCR results
        processed_image = preprocess_for_ocr(cropped_image)

        if (debug >= 1):
            cv2.imshow(f"Processed image {i}", processed_image)

            key = cv2.waitKey(0)
            cv2.destroyAllWindows()
            if key == 27:  # ESC key
                print("ESC key pressed. Aborting execution.")
                return {}

        # Perform OCR on the corrected region
        ocr_text = pytesseract.image_to_string(processed_image, config="--psm 6")

        ocr_results[i] = ocr_text.strip()

    if (debug >= 1):
        cv2.destroyAllWindows()  # Ensure all windows are closed at the end

    return ocr_results


def detect_text_regions(image, east_model, min_confidence=0.5, nms_threshold=0.8):
    """
    Detects text regions in an image using the EAST text detector with debugging.
    """
        # Grab image dimensions
    (H, W) = image.shape[:2]

    # Define the new width and height for the image (must be multiples of 32)
    newW, newH = (W // 32) * 32, (H // 32) * 32
    (rH, rW) = (H / float(newH), W / float(newW))  # Determine scale factors

    # Resize the image to fit the EAST model input
    resized_image = cv2.resize(image, (newW, newH))
    (H, W) = resized_image.shape[:2]

    # Define the two output layer names for the EAST detector model that
    # we are interested -- the first is the output probabilities and the
    # second can be used to derive the bounding box coordinates of text
    layerNames = [
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"]

    # Prepare the input blob for the EAST model
    blob = cv2.dnn.blobFromImage(resized_image, 1.0, (W, H),
                                 (123.68, 116.78, 103.94), swapRB=True, crop=False)

    # Perform a forward pass to get scores and geometry
    east_model.setInput(blob)
    (scores, geometry) = east_model.forward(layerNames)

    # Decode predictions
    (detections, confidences) = decode_bounding_boxes(scores, geometry, min_confidence)

    # Apply non-maxima suppression to suppress weak, overlapping bounding boxes
    indices = cv2.dnn.NMSBoxes(detections, confidences, score_threshold=min_confidence, nms_threshold=nms_threshold)

    if isinstance(indices, tuple):  # Check if indices is a tuple (empty result)
        indices = np.array([])  # Convert it into an empty NumPy array

    # apply morphological operations to merge nearby bounding boxes
    kernel = np.ones((10, 10), np.uint8)
    mask = np.zeros((H, W), dtype=np.uint8)

    # Draw detected boxes onto a mask
    for i in indices.flatten():
        (startX, startY, endX, endY) = detections[i]
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)
        cv2.rectangle(mask, (startX, startY), (endX, endY), 255, -1)

    # Dilate the mask to merge nearby detections
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Find contours from the merged mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Collect the new bounding boxes
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        boxes.append((x, y, x + w, y + h))

    # Sort bounding boxes top-to-bottom, then left-to-right
    boxes = sort_bounding_boxes(boxes, y_tolerance=10)

    return boxes

def sort_bounding_boxes(boxes, y_tolerance=10):
    """
    Sorts bounding boxes first left-to-right while considering slight misalignments in the Y-axis.
    Args:
        boxes (list of tuples): List of bounding boxes (x1, y1, x2, y2).
        y_tolerance (int): Maximum pixel difference in Y to consider boxes on the same line.
    Returns:
        List of sorted bounding boxes.
    """
    if not boxes:
        return []

    # Sort by Y-coordinate first, then X
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))

    # Group bounding boxes by rows
    rows = []
    current_row = [boxes[0]]

    for i in range(1, len(boxes)):
        _, y1, _, y2 = boxes[i]
        _, prev_y1, _, prev_y2 = boxes[i - 1]

        # If the Y difference is within the threshold, consider it the same row
        if abs(y1 - prev_y1) < y_tolerance or abs(y2 - prev_y2) < y_tolerance:
            current_row.append(boxes[i])
        else:
            rows.append(sorted(current_row, key=lambda b: b[0]))  # Sort row by X
            current_row = [boxes[i]]

    # Append the last row
    if current_row:
        rows.append(sorted(current_row, key=lambda b: b[0]))

    # Flatten the sorted rows
    sorted_boxes = [box for row in rows for box in row]

    return sorted_boxes


def decode_bounding_boxes(scores, geometry, scoreThresh):
    """
    Decodes the bounding box predictions from the EAST model.
    """

    # ASSERT dimensions and shapes of geometry and scores #
    assert len(scores.shape) == 4, "Incorrect dimensions of scores"
    assert len(geometry.shape) == 4, "Incorrect dimensions of geometry"
    assert scores.shape[0] == 1, "Invalid dimensions of scores"
    assert geometry.shape[0] == 1, "Invalid dimensions of geometry"
    assert scores.shape[1] == 1, "Invalid dimensions of scores"
    assert geometry.shape[1] == 5, "Invalid dimensions of geometry"
    assert scores.shape[2] == geometry.shape[2], "Invalid dimensions of scores and geometry"
    assert scores.shape[3] == geometry.shape[3], "Invalid dimensions of scores and geometry"

    detections = []
    confidences = []

    (numRows, numCols) = scores.shape[2:4]

    for y in range(0, numRows):

        # Extract data from scores. The geometrical data is used to derive 
        # potential bounding box coordinates that surround text.
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        for x in range(0, numCols):
            score = scoresData[x]

            # If score is lower than threshold score, move to next x
            if (score < scoreThresh):
                continue

            # Calculate offset
            (offsetX, offsetY) = (x * 4.0, y * 4.0)


            # Extract the rotation angle for the prediction and then
            # compute the sin and cosine.
            angle = anglesData[x]
            (cos, sin) = (np.cos(angle), np.sin(angle))

            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # Compute both the starting and ending (x, y)-coordinates for
            # the text prediction bounding box.
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)
            
            # Add the bounding box coordinates and probability score to
            # our respective lists.
            detections.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    return (detections, confidences)


def showBoundingBoxes(image, boxes):
    """
    Visualizes the bounding boxes on the input image.
    """

    # Check if vertices are empty
    if boxes is None or len(boxes) == 0:
        print("No bounding boxes to display.")
        return
    
    # Show bounding boxes
    for i, (startX, startY, endX, endY) in enumerate(boxes):

        # Draw the lines
        cv2.rectangle(image, (startX, startY), (endX, endY), color=(0, 255, 0), thickness=2)

        # Add the index label
        text_x, text_y = startX+10, startY+40
        cv2.putText(image, f"{i}", (text_x, text_y),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.2,
                    color=(0, 255, 0), thickness=2)

    # Display the image with bounding boxes
    cv2.imshow("Bounding boxes", image)
    key = cv2.waitKey(0)
    cv2.destroyAllWindows()
    if key == 27:  # ESC key
        print("ESC key pressed. Aborting execution.")
        return

