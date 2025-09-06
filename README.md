# Book Recognition & Lookup System

Recognition and lookup of books in photos or video streams.

## Overview

This code recognizes book spines in images, extracts text via OCR, and looks up those texts in various library databases to help you identify the books.

### Pipeline
1. **Book Spine Detection** → YOLO11 OBB Model
2. **Text Area Detection** → EAST Model  
3. **OCR** → Tesseract
4. **Text Correction** → SymSpell + Dictionaries
5. **Library Lookup** → Swisscovery, Google Books, DNB, lobid GND, OpenLibrary

## Help wanted

**Contributions are very welcome!**

I know a bit of everything, but not enough currently to make this work truly great. This is a truly interdisciplinary project that requires expertise in several fields and topics - which is why I started it in the first place!

Ping me, if you believe you can help with improving image processing, text detection, data lookup or the AI model. Or with whatever you think needs improvement.

## Quick Start

Note that his been developed on macOS. I'm not sure to what extend the Bookfinder runs on other OSes, though I've taken some effort to keep it portable and to make sure it's easy to install.

```bash
Install Mamba for managing all dependencies.

# Prepare environment using included (zsh) script
./1_create-conda-env.sh

# Activate environment
mamba activate yolo11

# Run the Bookfinder server
python3 app.py

# Perform a book detection & lookup using one of the included example photos.
Point your browser at http://localhost:5010
Supply a photo, e.g. example-files/books/Books_00005.png
Click on "run"

# To run tests, e.g.
python3 tests/test_lookup_utils.py
```

## Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - Some technical details & guidelines
- **[Training Guide](docs/README.training.md)** - Model training documentation
- **[Roo Code Setup](docs/Roo%20Code%20setup.md)** - Development environment setup (experimental)
- **[Workflow Diagram](docs/workflow.planned.png)** - Visual overview of the built-in and planned workflow

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
* A script uses a pragmatic approach to get book titles in a specific language from OpenLibrary: we query common short words in a language; in the resulting list, we remove those where the language of the record does not match the language we are looking for. 
* The meta data of books found like this is stored in a local DB. The book title list exported for SymSpell to use.
* However, as this lead to many misses, an algorithm matching detected texts to works in the titles and author names DB has been disabled again.

## What am I currently working on
* I'm currently porting the Bookfinder server to Raspberry Pi OS.
* The goal is to get this to run on a Raspberry Pi 3B+ with AI camera as I want to run this on a portable device.
* The current state here is that Bookfinder installs and runs on Raspberry Pi OS right away.
    * When starting a detection run, we get some 400 - bad request error at the beginning, but initialisation then finishes.
    * Attempting a detection run results eventually in segmentation fault (see below). I'll have to investigate this.
    * I'll also try to get my bookspine detection model to run on the IMX500 of the AI camera.


```
2025-08-24 22:16:40,550 - INFO - 📘 Bookfinder Server started and listening for requests on http://0.0.0.0:5010
192.168.178.172 - - [24/Aug/2025 22:18:08] code 400, message Bad request version ('Qª\\x00"\\x13\\x01\\x13\\x03\\x13\\x02À+À/Ì©Ì¨À,À0À')
192.168.178.172 - - [24/Aug/2025 22:18:08] "\x16\x03\x01\x07h\x01\x00\x07d\x03\x03Ê×À· Ï¹Í­(ï5\x14³\x82¦ÎóðrÚ\x85Ú+dï aî\x08±Y $û»r\x92a\x1aç\x94¼«àô§)Ï\x9d\x90\x80òÌQ+Vº©Iª\x98 Qª\x00"\x13\x01\x13\x03\x13\x02À+À/Ì©Ì¨À,À0À" 400 -
192.168.178.172 - - [24/Aug/2025 22:18:08] code 400, message Bad request syntax ('\\x16\\x03\\x01\\x02\\x97\\x01\\x00\\x02\\x93\\x03\\x03\\x96@«Îîæ')
192.168.178.172 - - [24/Aug/2025 22:18:08] "\x16\x03\x01\x02\x97\x01\x00\x02\x93\x03\x03\x96@«Îîæ" 400 -
2025-08-24 22:20:54,478 - INFO - ✅ Loaded 80000 words for 'en'
2025-08-24 22:20:54,887 - INFO - ✅ Loaded 100000 words for 'de'
2025-08-24 22:20:54,888 - INFO - ✅ Loaded 100000 words for 'fr'
2025-08-24 22:20:54,889 - INFO - ✅ Loaded 100000 words for 'it'
2025-08-24 22:20:54,911 - ERROR - Dictionary file not found at /home/pi/Bookfinder/dictionaries/names.de.txt.
2025-08-24 22:20:54,914 - ERROR - ❌ Failed to load dictionary: /home/pi/Bookfinder/dictionaries/names.de.txt
2025-08-24 22:20:54,928 - ERROR - ❌ Failed to load name dictionary for 'de'
2025-08-24 22:20:54,943 - ERROR - Dictionary file not found at /home/pi/Bookfinder/dictionaries/book_titles.de.txt.
2025-08-24 22:20:54,944 - ERROR - ❌ Failed to load dictionary: /home/pi/Bookfinder/dictionaries/book_titles.de.txt
2025-08-24 22:20:54,944 - ERROR - ❌ Failed to load book title dictionary for 'de'
2025-08-24 22:20:54,952 - INFO - 🔍 Starting book detection...
2025-08-24 22:20:54,971 - INFO - === Book detection starts at 24.08.2025 22:20 ===

image 1/1 /home/pi/Bookfinder/example-files/books/Books_00003.png: 480x640 None6063.4ms
Speed: 172.2ms preprocess, 6063.4ms inference, 133.5ms postprocess per image at shape (1, 3, 480, 640)
Segmentation fault
```



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
    * Swisscovery would be ideal as our data source, but I can't properly search it using the SRU API: I have to know if a text is a "title" or "author", "any" queries do not seem to be supported.
    * I have added Google Books as data source right after Swisscovery as a result of the above. Currently, most matches are coming from there. Those matches are often very good, but also sometimes just plain wrong. Still, this is a lot better than before and allows me to focus on the pipeline.

## Ideas on how to improve the book title lookup
### Validate found books against detected texts
We could use the data from the analysis to classify some texts as likely to be the title or the author name, then do the lookup accordingly. I doubt this will lead to better matches as it probably causes a lot of misses. It would be better to e.g. have an "any" search in Swisscovery and a better analysis of its results.

Only then will I focus on the following:
* Improve text area detection to focus on single words or lines.
* Ensure OCR also knows about the language it's supposed to find. Pass it a "deu" and "eng", for example.
* Maybe switch out tesseract (again) with EasyOCR to improve or simplify OCR.
* Re-train the bookspine detection model using one of the larger book spine training sets using e.g. RoboFlow.

### Validate found books against detected texts
* Some book lookups lead to entirely wrong results.
  * We should check if the found book actually contains or otherwise matches the previously detected text.
  * If not, we should continue our lookup with the next data source.

### Better search of Swisscovery
* As mentioned elsewhere, the current Swisscovery lookup leads to almost no results, though the data looks very promsing.
* Can we improve the lookup given the API means we have (i.e. no "any" lookups)?

### Classify detected texts to improve the lookup
* Determining where titles, subtitles and authors are located most of the time. The goal is to get a better detection of titles and subtitles, author names, publisher names and logos, and possibly additional book info.
  * The original idea was to train a object detection model to help identify the text areas, but that doesn't work: object detection is not good in this: text is a different type of beast.
  * The properly annotated Roboflow dataset (bookspine-text-blocks) can still be used to calculate, where titles and author names are typically located. This is what the script analysis/analyze_coco_textblocks.py does.
* The plan is now to 1) keep identifying text blocks using the existing means (using EAST and OCR), but then 2) use the calculated, typical locations to help with classify text blocks as titles and authors, then 3) look up those.
  * This can't be a 100% perfect match, but it should especially help on avoiding publisher names and book infos in lookups.

I'm not sure this is a good approach, though, as - similarly to using words from book titles and author names to correct detected texts -, this may lead to lots of misses. A more powerful search would probably help more.

## Next steps for web app
As soon as we have better detection, better OCR and received better book data:
* Allow to re-detect text on a book spine for a selected variant.
* Allow to re-lookup text for a selected bookspine.
* Allow to select one set of book details as the "correct" book details for a specific bookspine.
* Allow to lookup manually entered text and select that as the "correct" book details, as a way to override automatic text detection and lookup.
