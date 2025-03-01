# Looking up books

In this project, I attempt to look up all details on books captured in a photo or video stream.

The script first detects images of book spines in a photo (or a video stream). It extracts, corrects and pre-processes these images, then attempts to detect areas with text in each image. It then pre-processes a cropped image of each identified text area and runs OCR on its text. The text is pre-processed and then sent to APIs for looking up book titles. Finally, the result is presented to the user.

# Status
## What works
### Detect book spinges
* Book spines in a photo are recognized using a re-trained YOLO11 OBB model.
* Book spine images are extracted by rotating them until they are higher than wide and rectangular, then cropped from the photo.
* A 180-degree rotated image variant is created to account for texts being upside-down.
### Detect text areas
* The images are pre-processed to enhance text area detection.
* Text areas are detected using an EAST detection model.
* The bounding boxes of nearby and overlapping text areas are merged using morphological operations.
### OCR on text areas
* Cropped images of these text areas are extracted and further pre-processed for OCR.
* The text in the text area images is extracted using Tesseract.
### Text processing
* Basic processing of texts: only characters and digits of supported languages are accepted, other special chars are removed. Texts are converted to lower case.
* Auto-correction of texts: uses SymSpell to auto-correct texts found.

## What is not there yet
* No lookup using a books API.
* No consolidation and presentation of results.

## What doesn't work so well
* Bounding boxes: 
    * The morphological operations may currently be too aggressive, as multiple words or lines of words are combined in a single bounding box. While that sounds good, it actually makes OCR _with tesseract_ harder.
    * Bounding boxes are detected in an arbitrary order, mixing author and published names with the words in the title. It would be good to sort them left to right, top to bottom.
* OCR:
    * The code currently detects text areas with a single line of text quite well. It fails with multiple lines of text, however. Using a different PSM option in tesseract seems not to improve things a lot. I can't seem to find a setting working well for single and for multiple lines, and no way to reliably detect either (so I could change options). 
    * AI suggests that EasyOCR might actually work better for me. But if I could only produce single work or at least single line, tesseract might be good enough.
* Text area detection: 
    * EAST works ok now, but CRAFT for recognizing bounding boxes for individual characters, then combining these using morphological operations may actually work better.
    * Am I maybe combining too many boxes here, creating multiple line boxes, where single line ones would be better? Here's an approach (see last comment) that may work better:
        https://stackoverflow.com/questions/20831612/getting-the-bounding-box-of-the-recognized-words-using-python-tesseract
    Maybe it's already enough to rule out bounding boxes with confidence -1, as these are "corresponding to _boxes_ of text".
* Text processing:
    * The basic text processing is inefficient: the set of accepted characters is computed several times.
    * The auto-correction of texts is always done with the English dictionary, which is wrong most of the time.
    * The auto-correction of texts also falsely corrects some words, especially names.

## Next steps
* Clean text, correct errors, maybe detect words.
* Look up books using the cleaned text.

We can always improve text area detection and OCR later on. For now, it's more important to implement the whole pipeline to validate the approach.

Only then I do the following:
* Improve text area detection to focus on single words or lines.
* Order bounding boxes to get text in a typical reading order.
* Ensure OCR also knows about the language it's supposed to find. Pass it a "deu" and "eng", for example.
* Switch out tesseract (again) with EasyOCR to improve or simplify OCR.
* Re-train the model using one of the larger book spine training sets using e.g. RoboFlow.

