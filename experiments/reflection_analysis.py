#!/usr/bin/env python3
"""
Reflection lines analysis for book cover OCR
Tests various methods for handling white reflection lines

Usage:
python reflection_test.py <image_path>
"""

import sys
import os
import cv2
import numpy as np
import time
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

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

def detect_horizontal_reflections(img):
    """
    Detects horizontal white reflection lines
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Find very bright horizontal structures
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (img.shape[1]//3, 1))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, horizontal_kernel)
    
    # Threshold for reflections
    _, reflection_mask = cv2.threshold(tophat, 20, 255, cv2.THRESH_BINARY)
    
    # Statistics about reflection lines
    reflection_pixels = np.sum(reflection_mask == 255)
    total_pixels = reflection_mask.shape[0] * reflection_mask.shape[1]
    reflection_percentage = (reflection_pixels / total_pixels) * 100
    
    return reflection_mask, reflection_percentage

def remove_reflections_method1(img):
    """
    Method 1: Inpainting - Replace reflection lines with interpolation
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Detect reflection lines
    reflection_mask, _ = detect_horizontal_reflections(img)
    
    # Expand mask slightly for better inpainting
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
    reflection_mask = cv2.morphologyEx(reflection_mask, cv2.MORPH_DILATE, kernel)
    
    # Apply inpainting
    result = cv2.inpaint(gray, reflection_mask, 3, cv2.INPAINT_TELEA)
    
    return result

def remove_reflections_method2(img):
    """
    Method 2: Morphological Opening - Removes thin bright lines
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Morphological opening to remove thin bright lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
    opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    
    return opened

def remove_reflections_method3(img):
    """
    Method 3: Adaptive threshold dampening
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Find local maxima (potential reflections)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Dampen areas that are much brighter than their surroundings
    diff = gray.astype(np.float32) - blurred.astype(np.float32)
    
    # Only dampen very bright areas
    mask = diff > 30
    result = gray.copy().astype(np.float32)
    result[mask] = result[mask] * 0.7  # Darken reflections by 30%
    
    return result.astype(np.uint8)

def apply_current_preprocessing(img):
    """
    Current preprocessing pipeline (reduced)
    """
    if not LIBS_AVAILABLE:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    return unsharp_mask(gray)

def test_ocr_method(img, method_name, save_debug=False):
    """
    Tests OCR on a processed image
    """
    print(f"\n--- {method_name} ---")
    
    start_time = time.time()
    try:
        text = pytesseract.image_to_string(
            img, 
            lang='deu+eng', 
            config='--psm 6'
        ).strip()
        
        processing_time = time.time() - start_time
        
        print(f"✅ Processing time: {processing_time:.2f} seconds")
        print(f"📝 Text length: {len(text)} characters")
        print(f"📖 Detected text: '{text}'")
        
        # Search for known words
        known_words = ['ORHAN', 'PAMUK', 'DIE', 'ROTHAARIGE', 'ROTH']
        found_words = []
        text_upper = text.upper()
        for word in known_words:
            if word in text_upper:
                found_words.append(word)
        
        if found_words:
            print(f"🎯 Detected keywords: {', '.join(found_words)}")
        
        if save_debug:
            debug_filename = f"debug_reflection_{method_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.jpg"
            cv2.imwrite(debug_filename, img)
            print(f"💾 Debug image saved: {debug_filename}")
        
        return {
            'text': text,
            'length': len(text),
            'time': processing_time,
            'method': method_name,
            'keywords': found_words
        }
        
    except Exception as e:
        print(f"❌ OCR failed: {e}")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': method_name,
            'error': str(e),
            'keywords': []
        }

def analyze_reflections(img_path):
    """
    Performs comprehensive reflection lines analysis
    """
    print(f"🔍 Analyzing reflection lines in: {img_path}")
    
    # Load image
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"❌ Error: Image {img_path} could not be loaded")
        return
    
    print(f"📏 Image size: {img.shape}")
    
    # Reflection analysis
    print("\n🔬 Reflection lines analysis...")
    reflection_mask, reflection_percentage = detect_horizontal_reflections(img)
    print(f"📊 Reflection percentage: {reflection_percentage:.2f}% of image area")
    
    # Save reflection mask
    cv2.imwrite("debug_reflection_mask.jpg", reflection_mask)
    print("💾 Reflection mask saved: debug_reflection_mask.jpg")
    
    # Grayscale original
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    results = []
    
    # Test 1: Original without preprocessing
    result = test_ocr_method(gray, "Original (without preprocessing)", save_debug=True)
    results.append(result)
    
    # Test 2: Current preprocessing (only Unsharp Mask)
    current_processed = apply_current_preprocessing(img)
    result = test_ocr_method(current_processed, "Current (Unsharp Mask)", save_debug=True)
    results.append(result)
    
    # Test 3: Reflection removal Method 1 (Inpainting)
    method1 = remove_reflections_method1(img)
    method1_sharpened = unsharp_mask(method1) if LIBS_AVAILABLE else method1
    result = test_ocr_method(method1_sharpened, "Inpainting + Unsharp", save_debug=True)
    results.append(result)
    
    # Test 4: Reflection removal Method 2 (Morphological)
    method2 = remove_reflections_method2(img)
    method2_sharpened = unsharp_mask(method2) if LIBS_AVAILABLE else method2
    result = test_ocr_method(method2_sharpened, "Morphological + Unsharp", save_debug=True)
    results.append(result)
    
    # Test 5: Reflection removal Method 3 (Adaptive dampening)
    method3 = remove_reflections_method3(img)
    method3_sharpened = unsharp_mask(method3) if LIBS_AVAILABLE else method3
    result = test_ocr_method(method3_sharpened, "Adaptive Dampening + Unsharp", save_debug=True)
    results.append(result)
    
    # Summarize results
    print("\n" + "="*80)
    print("📊 REFLECTION LINES TEST RESULTS")
    print("="*80)
    
    # Sort by number of detected keywords
    results.sort(key=lambda x: len(x.get('keywords', [])), reverse=True)
    
    print(f"{'Rank':<4} {'Method':<35} {'Chars':<8} {'Time(s)':<8} {'Keywords':<20}")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        keywords = ', '.join(result.get('keywords', []))
        if not keywords:
            keywords = "none"
        
        print(f"{i:<4} {result['method']:<35} {result['length']:<8} {result['time']:<8.2f} {keywords:<20}")
    
    # Best method for keyword recognition
    best_for_keywords = results[0]
    print(f"\n🏆 BEST METHOD FOR KEYWORDS: {best_for_keywords['method']}")
    if best_for_keywords.get('keywords'):
        print(f"🎯 Detected keywords: {', '.join(best_for_keywords['keywords'])}")
    print(f"📝 Full text: '{best_for_keywords['text']}'")
    
    # Visualisierung erstellen
    create_visualization(img, reflection_mask, method1, method2, method3)

def create_visualization(original, reflection_mask, method1, method2, method3):
    """
    Erstellt eine Visualisierung der verschiedenen Methoden
    """
    try:
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Original
        axes[0,0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        axes[0,0].set_title("Original")
        axes[0,0].axis('off')
        
        # Reflexionsmaske
        axes[0,1].imshow(reflection_mask, cmap='gray')
        axes[0,1].set_title("Erkannte Reflexionslinien")
        axes[0,1].axis('off')
        
        # Graustufen Original
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        axes[0,2].imshow(gray, cmap='gray')
        axes[0,2].set_title("Original Graustufen")
        axes[0,2].axis('off')
        
        # Methode 1: Inpainting
        axes[1,0].imshow(method1, cmap='gray')
        axes[1,0].set_title("Inpainting")
        axes[1,0].axis('off')
        
        # Methode 2: Morphologisch
        axes[1,1].imshow(method2, cmap='gray')
        axes[1,1].set_title("Morphological Opening")
        axes[1,1].axis('off')
        
        # Method 3: Adaptive dampening
        axes[1,2].imshow(method3, cmap='gray')
        axes[1,2].set_title("Adaptive Dampening")
        axes[1,2].axis('off')
        
        plt.tight_layout()
        plt.savefig("reflection_analysis_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("\n📊 Visualization saved: reflection_analysis_comparison.png")
        
    except Exception as e:
        print(f"⚠️ Visualization failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='Reflection lines analysis for book cover OCR')
    parser.add_argument('image_path', help='Path to the image to analyze')
    
    args = parser.parse_args()
    
    # Validate path
    img_path = Path(args.image_path)
    if not img_path.exists():
        print(f"❌ Error: Image {img_path} does not exist")
        return 1
    
    # Check availability
    print("🔧 Checking availability...")
    print(f"✅ Tesseract: Available")
    print(f"{'✅' if LIBS_AVAILABLE else '❌'} libs.utils: {'Available' if LIBS_AVAILABLE else 'Not available'}")
    
    # Perform analysis
    analyze_reflections(img_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
