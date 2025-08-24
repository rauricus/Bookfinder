# Book Recognition & Lookup System

Automatic recognition and lookup of books from photos or video streams.

## 🎯 Overview

This project recognizes book spines in photos, extracts text via OCR, and looks up book details in various library databases.

### Pipeline
1. **Book Spine Detection** → YOLO11 OBB Model
2. **Text Area Detection** → EAST Model  
3. **OCR** → Tesseract
4. **Text Correction** → SymSpell + Dictionaries
5. **Library Lookup** → Swisscovery, Google Books, DNB, lobid GND, OpenLibrary

## 🚀 Quick Start

```bash
# Activate environment
micromamba activate yolo11

# Run book recognition
python3 app.py

# Run tests
python3 tests/test_lookup_utils.py
```

## 📚 Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Technical details & API documentation
- **[Training Guide](docs/README.training.md)** - Model training documentation
- **[Roo Code Setup](docs/Roo%20Code%20setup.md)** - Development environment setup (experimental)
- **[Workflow Diagram](docs/workflow.planned.png)** - Visual project workflow overview

## 🎯 Status
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
* Determining where titles, subtitles and authors are located most of the time. The goal is to get a better detection of titles and subtitles, author names, publisher names and logos, and possibly additional book info.
  * The original idea was to train a object detection model to help identify the text areas, but that doesn't work: object detection is not good in this: text is a different type of beast.
  * The properly annotated Roboflow dataset (bookspine-text-blocks) can still be used to calculate, where titles and author names are typically located. This is what the script analysis/analyze_coco_textblocks.py does.
* The plan is now to 1) keep identifying text blocks using the existing means (using EAST and OCR), but then 2) use the calculated, typical locations to help with classify text blocks as titles and authors, then 3) look up those.
  * This can't be a 100% perfect match, but it should especially help on avoiding publisher names and book infos in lookups.

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
