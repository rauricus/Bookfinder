# Looking up books

In this project, I attempt to look up all details on books captured in a photo or video stream.

The script first detects images of book spines in a photo (or a video stream). It extracts, corrects and pre-processes these images, then attempts to detect areas with text in each image. It then pre-processes a cropped image of each identified text area and runs OCR on its text. The text is pre-processed and then sent to APIs for looking up book titles. Finally, the result is presented to the user.

# Status
## What works
### Detect book spines
* Book spines in a photo are recognized using a re-trained YOLO11 OBB model.
* Book spine images are extracted by rotating them until they are higher than wide and rectangular, then cropped from the photo.
* A 180-degree rotated image variant is created to account for texts being upside-down.
### Detect text areas
* The images are pre-processed to enhance text area detection.
* Text areas are detected using an EAST detection model.
* The bounding boxes of nearby and overlapping text areas are merged using morphological operations.
* Bounding boxes are sorted from left-to-right, top-to-bottom to keep the "flow" of the text on the book spine.
### OCR on text areas
* Cropped images of these text areas are extracted and further pre-processed for OCR.
* The text in the text area images is extracted using Tesseract.
### Text processing
* Basic processing of texts: only characters and digits of supported languages are accepted, other special chars are removed. Texts are converted to lower case.
* Detected text is then auto-corrected against a word dictionary. 
* Names of authors are preserved by detecting them against a dictionary with author names.
### Match against common book titles
* The text corrected against a word dictionary is then matched with known book titles.
* If a book title actually isn't known, this might lead to over-correction. To avoid this, the script ompares the corrected title with the title matched against the books list. If the matched title is too far off the corrected title, it gets discarded.
### Getting book titles and the names of their authors.
* A script uses a pragrmatic approach to get book titles in a specific language from OpenLibrary: we query common short words in a language; in the resulting list, we remove those where the language of the record does not match the language we are looking for. 
* The meta data of books found like this is stored in a local DB. The book title list exported for SymSpell to use.

## What am I currently working on
* Developing a Web UI that shows the results from the run.

## What is not there yet
-

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
    * The auto-correction of texts is always done with the German dictionary. It really should be language sensitive. (CHECK IF THIS IS STILL CORRECT)
    * The book titles in the book titles dictionary could come from EDITIONS in OpenLibrary, as those titles would be localized. This is due to many entries in OL being stored in English by default, but then their EDITIONS contain the actual, localized title. We can extract this in the future - it's too complex for now.
* Book title lookup:
    * Search in Swisscovery and Lobid GND often returns no results, because the book titles found on book spines often include the author names.
        * We can maybe detect (and remove) author names by comparing them against our authors database.
        * It would be nice to somehow detect author names because of their position and/or grouping on the book spine.

## Next steps
* Improve book title lookup by trying to only look up by title.

We can always improve text area detection and OCR later on. For now, it's more important to implement the whole pipeline to validate the approach.

Only then I do the following:
* Improve text area detection to focus on single words or lines.
* Ensure OCR also knows about the language it's supposed to find. Pass it a "deu" and "eng", for example.
* Switch out tesseract (again) with EasyOCR to improve or simplify OCR.
* Re-train the model using one of the larger book spine training sets using e.g. RoboFlow.

Added a script using a pragrmatic approach to get book titles in a specific language from OpenLibrary: we search for common short words in a language; in the result list, we remove those where the language of the record does not match the language we are looking for. This is due to many entries being stored in English by default, but then their EDITIONS contain the actual, localized title. We can extract this in the future - it's too complex for now.


## Next steps for web app
As soon as we have better detection, better OCR and received better book data:
* Allow to re-detect text on a book spine for a selected variant.
* Allow to re-lookup text for a selected bookspine.
* Allow to select one set of book details as the "correct" book details for a specific bookspine.
* Allow to lookup manually entered text and select that as the "correct" book details, as a way to override automatic text detection and lookup.
