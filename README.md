# Looking up books

In this project, I attempt to look up all details on books captured in a photo or video stream.

The script first detects images of book spines in a photo (or a video stream). It extracts, corrects and pre-processes these images, then attempts to detect areas with text in each image. It then pre-processes a cropped image of each identified text area and runs OCR on its text. The text is pre-processed and then sent to APIs for looking up book titles. Finally, the result is presented to the user.

# Status
## What works
* Book spines in a photo are recognized using a re-trained YOLO11 OBB model.
* Book spine images are extracted by rotating them until they are higher than wide and rectangular, then cropped from the photo.
* A 180-degree rotated image variant is created to account for texts being upside-down.
* The images are pre-processed to enhance text area detection.
* Text areas are detected using an EAST detection model.
* The bounding boxes of nearby and overlapping text areas are merged using morphological operations.
* Cropped images of these text areas are extracted and further pre-processed for OCR.
* The text in the text area images is extracted using Tesseract.

## What is not there yet
* No cleaning of text, error correction and lookup using a books API.

## What doesn't work so well
* Bounding boxes: 
    * The morphological operations may currently be too aggressive, as multiple words or lines of words are combined in a single bounding box. While that sounds good, it actually makes OCR with tesseract harder.
    * Bounding boxes are detected in an arbitrary order, mixing author and published names with the words in the title. It would be good to sort them left to right, top to bottom.
* OCR:
    * The code currently detects text areas with a single line of text quite well. It fails with multiple lines of text, however. Using a different PSM option in tesseract seems not to improve things a lot. I can't seem to find a setting working well for single and for multiple lines, and no way to reliably detect either (so I could change options). 
    * AI suggests that EasyOCR might actually work better for me. But if I could only produce single work or at least single line, tesseract might be good enough.
* Text area detection: EAST works ok now, but CRAFT for recognizing bounding boxes for individual characters, then combining these using morphological operations may actually work better.

## Next steps
* Clean text, correct errors, maybe detect words.
* Look up books using the cleaned text.

We can always improve text area detection and OCR later on. For now, it's more important to implement the whole pipeline to validate the approach.

Only then I do the following:
* Improve bounding boxes and detection of single words or lines.
* Switch out tesseract (again) with EasyOCR to improve or simplify OCR.