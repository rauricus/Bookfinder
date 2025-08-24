#!/usr/bin/env python3
"""
Test script to verify Tesseract language support.
This script compares OCR results with and without language support.
"""

import os
import sys
import cv2
import pytesseract

# Add the project root directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config

# List available Tesseract languages
print("Available Tesseract languages:")
try:
    langs = pytesseract.get_languages(config='')
    print(langs)
except Exception as e:
    print(f"Error getting languages: {e}")
print()

# Test images from OCR test directory
import glob

# Get all non-rotated images (to avoid duplicates)
test_images = glob.glob("example-files/ocr_test/*.jpg")
test_images.sort()  # Sort to ensure consistent order

# Limit to first 5 images to avoid too much output
#test_images = test_images[:5]

for img_path in test_images:
    if os.path.exists(img_path):
        print(f"\n{'=' * 80}")
        print(f"TESTING: {os.path.basename(img_path)}")
        print(f"{'=' * 80}")
        
        # Display the image filename and path
        print(f"Image path: {img_path}")
        
        # Load the image
        img = cv2.imread(img_path)
        
        # Define test configurations
        test_configs = [
            ("Default (English only)", None, "--psm 6"),
            ("German only", "deu", "--psm 6"),
            ("German + English", "deu+eng", "--psm 6"),
            (f"Config settings ({config.OCR_LANGUAGES})", config.OCR_LANGUAGES, f"--psm {config.OCR_PSM_MODE}")
        ]
        
        # Run tests for each configuration
        for desc, lang, psm_config in test_configs:
            print(f"\n{'-' * 40}")
            print(f"Configuration: {desc}")
            print(f"{'-' * 40}")
            
            try:
                # Perform OCR
                text = pytesseract.image_to_string(img, lang=lang, config=psm_config)
                
                # Clean up text for display (remove extra whitespace)
                text = ' '.join(text.split())
                
                # Display results
                if text.strip():
                    print(f"Result: {text[:150]}..." if len(text) > 150 else f"Result: {text}")
                    
                    # Count special characters (umlauts, etc.)
                    special_chars = sum(1 for c in text if c in 'äöüÄÖÜß')
                    if special_chars > 0:
                        print(f"Special characters detected: {special_chars} (äöüÄÖÜß)")
                else:
                    print("No text detected")
            except Exception as e:
                print(f"Error: {e}")
    else:
        print(f"Image not found: {img_path}")

# Add a summary section
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("The test compared OCR results using different language configurations:")
print("1. Default (English only) - Tesseract's default behavior")
print("2. German only - Using only German language model")
print("3. German + English - Recommended for Swiss market")
print("4. Config settings - Using settings from config.py")
print("\nKey observations to look for:")
print("- Better recognition of German umlauts (ä, ö, ü, ß) with German language")
print("- Improved word recognition with German + English for Swiss books")
print("- Differences in text segmentation and punctuation")
print("\nTest completed.")