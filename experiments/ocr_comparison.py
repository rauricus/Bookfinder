#!/usr/bin/env python3
"""
OCR Comparison Test: EasyOCR vs Tesseract
Compares different OCR approaches with and without preprocessing

Usage:
python ocr_test.py <image_path>

Example:
python ocr_test.py output/predict110/book/Books_00005_rotated-180_1.jpg
"""

import sys
import os
import cv2
import numpy as np
import time
import argparse
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import OCR libraries
import pytesseract
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Import our preprocessing functions
try:
    from libs.utils.image_utils import unsharp_mask
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False

def apply_current_preprocessing(img):
    """
    Applies the currently used preprocessing pipeline
    """
    if not LIBS_AVAILABLE:
        print("⚠️ libs.utils.image_utils not available - using simple preprocessing")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
        return gray
    
    # The current pipeline from the system
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Unsharp masking for better sharpness
    gray = unsharp_mask(gray)
    
    # Bilateral filter for noise reduction
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    return gray

def test_tesseract_ocr(img, method_name, save_debug=False):
    """
    Tests Tesseract OCR on an image
    """
    print(f"\n--- Tesseract OCR ({method_name}) ---")
    
    start_time = time.time()
    try:
        # OCR with German and English
        text = pytesseract.image_to_string(
            img, 
            lang='deu+eng', 
            config='--psm 6'
        ).strip()
        
        processing_time = time.time() - start_time
        
        print(f"✅ Processing time: {processing_time:.2f} seconds")
        print(f"📝 Text length: {len(text)} characters")
        print(f"📖 Detected text: '{text}'")
        
        if save_debug:
            debug_filename = f"debug_tesseract_{method_name.lower().replace(' ', '_')}.jpg"
            cv2.imwrite(debug_filename, img)
            print(f"💾 Debug image saved: {debug_filename}")
        
        return {
            'text': text,
            'length': len(text),
            'time': processing_time,
            'method': f'Tesseract ({method_name})'
        }
        
    except Exception as e:
        print(f"❌ Tesseract OCR failed: {e}")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': f'Tesseract ({method_name})',
            'error': str(e)
        }

def test_easyocr(img, method_name, reader=None, save_debug=False):
    """
    Tests EasyOCR on an image
    """
    if not EASYOCR_AVAILABLE:
        print(f"\n--- EasyOCR ({method_name}) ---")
        print("❌ EasyOCR not available - installation required")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': f'EasyOCR ({method_name})',
            'error': 'EasyOCR not installed'
        }
    
    print(f"\n--- EasyOCR ({method_name}) ---")
    
    # Create reader if not provided
    if reader is None:
        print("🔄 Initializing EasyOCR Reader...")
        init_start = time.time()
        reader = easyocr.Reader(['de', 'en'], gpu=False)  # GPU=False for better compatibility
        init_time = time.time() - init_start
        print(f"✅ EasyOCR initialized in {init_time:.2f} seconds")
    
    start_time = time.time()
    try:
        # EasyOCR recognition
        results = reader.readtext(img)
        processing_time = time.time() - start_time
        
        # Extract texts and confidence values
        texts = []
        confidences = []
        
        print(f"✅ Processing time: {processing_time:.2f} seconds")
        print(f"📊 Number of detections: {len(results)}")
        
        for i, (bbox, text, confidence) in enumerate(results):
            texts.append(text)
            confidences.append(confidence)
            print(f"  {i+1}. '{text}' (Confidence: {confidence:.3f})")
        
        # Combine full text
        full_text = ' '.join(texts)
        avg_confidence = np.mean(confidences) if confidences else 0
        
        print(f"📝 Text length: {len(full_text)} characters")
        print(f"📈 Average confidence: {avg_confidence:.3f}")
        print(f"📖 Full text: '{full_text}'")
        
        if save_debug:
            debug_filename = f"debug_easyocr_{method_name.lower().replace(' ', '_')}.jpg"
            cv2.imwrite(debug_filename, img)
            print(f"💾 Debug image saved: {debug_filename}")
        
        return {
            'text': full_text,
            'length': len(full_text),
            'time': processing_time,
            'method': f'EasyOCR ({method_name})',
            'confidence': avg_confidence,
            'detections': len(results),
            'reader': reader  # Return reader for reuse
        }
        
    except Exception as e:
        print(f"❌ EasyOCR failed: {e}")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': f'EasyOCR ({method_name})',
            'error': str(e),
            'reader': reader
        }

def analyze_image(img_path):
    """
    Performs comprehensive OCR analysis
    """
    print(f"🔍 Analyzing image: {img_path}")
    
    # Load image
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"❌ Error: Image {img_path} could not be loaded")
        return
    
    print(f"📏 Image size: {img.shape}")
    
    # Grayscale version for analysis
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    print(f"📊 Image statistics: Mean={mean_val:.1f}, Standard deviation={std_val:.1f}")
    
    # Apply preprocessing
    print("\n🔄 Applying preprocessing...")
    preprocessed = apply_current_preprocessing(img)
    
    results = []
    easyocr_reader = None
    
    # Test 1: Tesseract without preprocessing
    result = test_tesseract_ocr(gray, "without preprocessing", save_debug=True)
    results.append(result)
    
    # Test 2: Tesseract with preprocessing
    result = test_tesseract_ocr(preprocessed, "with preprocessing", save_debug=True)
    results.append(result)
    
    # Test 3: EasyOCR without preprocessing (on original RGB)
    result = test_easyocr(img, "without preprocessing (RGB)", save_debug=True)
    results.append(result)
    if 'reader' in result:
        easyocr_reader = result['reader']
    
    # Test 4: EasyOCR without preprocessing (on grayscale)
    result = test_easyocr(gray, "without preprocessing (Gray)", reader=easyocr_reader, save_debug=True)
    results.append(result)
    if 'reader' in result:
        easyocr_reader = result['reader']
    
    # Test 5: EasyOCR with preprocessing
    result = test_easyocr(preprocessed, "with preprocessing", reader=easyocr_reader, save_debug=True)
    results.append(result)
    
    # Summarize results
    print("\n" + "="*80)
    print("📊 RESULTS SUMMARY")
    print("="*80)
    
    # Sort by text length
    valid_results = [r for r in results if r['length'] > 0]
    valid_results.sort(key=lambda x: x['length'], reverse=True)
    
    print(f"{'Rank':<4} {'Method':<30} {'Chars':<8} {'Time(s)':<8} {'Extra':<15}")
    print("-" * 80)
    
    for i, result in enumerate(valid_results, 1):
        extra = ""
        if 'confidence' in result:
            extra = f"Conf:{result['confidence']:.3f}"
        elif 'error' in result:
            extra = "ERROR"
        
        print(f"{i:<4} {result['method']:<30} {result['length']:<8} {result['time']:<8.2f} {extra:<15}")
    
    # Display best results
    if valid_results:
        best = valid_results[0]
        print(f"\n🏆 BEST METHOD: {best['method']}")
        print(f"📝 Text ({best['length']} characters): '{best['text'][:100]}{'...' if len(best['text']) > 100 else ''}'")
        
        if len(valid_results) > 1:
            second_best = valid_results[1]
            print(f"\n🥈 SECOND BEST: {second_best['method']} ({second_best['length']} characters)")
    else:
        print("\n❌ No successful OCR results")
    
    print("\n💾 Debug images have been saved for manual inspection")

def main():
    parser = argparse.ArgumentParser(description='OCR Comparison Test: EasyOCR vs Tesseract')
    parser.add_argument('image_path', help='Path to the image to analyze')
    parser.add_argument('--no-libs', action='store_true', help='Without libs.utils.image_utils (for minimal preprocessing)')
    
    args = parser.parse_args()
    
    # Validate path
    img_path = Path(args.image_path)
    if not img_path.exists():
        print(f"❌ Error: Image {img_path} does not exist")
        return 1
    
    # Check availability
    print("🔧 Checking availability...")
    print(f"✅ Tesseract: Available")
    print(f"{'✅' if EASYOCR_AVAILABLE else '❌'} EasyOCR: {'Available' if EASYOCR_AVAILABLE else 'Not available'}")
    print(f"{'✅' if LIBS_AVAILABLE else '❌'} libs.utils: {'Available' if LIBS_AVAILABLE else 'Not available'}")
    
    if not EASYOCR_AVAILABLE:
        print("\n⚠️ EasyOCR not available. Install with:")
        print("   pip install easyocr")
        print("   Running test with Tesseract only...\n")
    
    # Perform analysis
    analyze_image(img_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
