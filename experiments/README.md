# Experiments / Experimental Scripts

This directory contains experimental scripts and trials used for developing and testing various approaches. These differ from the actual unit tests in the `tests/` directory.

## Included Scripts:

### `ocr_comparison.py`
Compares different OCR approaches (EasyOCR vs Tesseract) with and without preprocessing.
```bash
python experiments/ocr_comparison.py <image_path>
```

### `dynamic_gap.py`
Experimental script for dynamic gap threshold functionality in text recognition.

### `ocr_languages.py`
Tests and compares Tesseract language support for different languages.

### `reflection_analysis.py`
Analyzes various methods for handling white reflection lines on book covers.
```bash
python experiments/reflection_analysis.py <image_path>
```

## Difference from Unit Tests

- **Unit Tests** (`tests/`): Automated tests for validating functionality
- **Experiments** (`experiments/`): Experimental scripts for trying out and comparing approaches

## Usage

These scripts are primarily intended for development purposes and help with:
- Testing different OCR parameters
- Trying out new algorithms  
- Performing performance comparisons
- Evaluating preprocessing techniques
