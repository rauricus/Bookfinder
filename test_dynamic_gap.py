#!/usr/bin/env python3
"""
Test script for dynamic gap threshold functionality.
"""

import os
import sys
import cv2
import numpy as np

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

import config
from libs.utils.ocr_utils import ocr_onImage, detect_text_regions
from libs.utils.text_classification import TextRegionSorter
from libs.logging import get_logger

logger = get_logger(__name__)

def test_dynamic_gap_with_image(image_path):
    """Test the dynamic gap functionality with a real image."""
    
    # Load the image
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not load image: {image_path}")
        return
    
    print(f"Testing dynamic gap functionality with: {image_path}")
    print(f"Image dimensions: {image.shape[1]}x{image.shape[0]}")
    
    # Load EAST model for text detection
    try:
        east_model_path = os.path.join(config.MODEL_DIR, 'east_text_detection.pb')
        if not os.path.exists(east_model_path):
            print(f"EAST model not found: {east_model_path}")
            return
            
        east_model = cv2.dnn.readNet(east_model_path)
        print("EAST model loaded successfully")
    except Exception as e:
        print(f"Error loading EAST model: {e}")
        return
    
    # Detect text regions
    print("\n--- Detecting text regions ---")
    boxes = detect_text_regions(image, east_model)
    print(f"Found {len(boxes)} text regions")
    
    if not boxes:
        print("No text regions detected")
        return
    
    # Calculate dynamic gap threshold
    print("\n--- Testing dynamic gap calculation ---")
    boxes_with_centers = []
    for x1, y1, x2, y2 in boxes:
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        height = y2 - y1
        boxes_with_centers.append(((x1, y1, x2, y2), center_x, center_y))
        print(f"Box: ({x1:3d}, {y1:3d}, {x2:3d}, {y2:3d}) Height: {height:2d}px")
    
    # Test the dynamic threshold calculation
    dynamic_threshold = TextRegionSorter._calculate_dynamic_gap_threshold(boxes_with_centers)
    print(f"\nSMART GAP threshold: {dynamic_threshold}px")
    
    # Compare with fixed threshold (old behavior)
    fixed_threshold = 80
    print(f"Fixed gap threshold (old): {fixed_threshold}px")
    print(f"Difference: {dynamic_threshold - fixed_threshold:+d}px")
    
    # Sort boxes and get structure info
    print("\n--- Sorting with SMART GAP ANALYSIS ---")
    sorted_boxes, structure_info = TextRegionSorter.sort_boxes_by_position(boxes)
    
    print(f"Detected columns: {structure_info['total_columns']}")
    print(f"Column boundaries: {structure_info.get('column_boundaries', [])}")
    
    # Show the results
    print("\n--- Running OCR with visualization ---")
    try:
        ocr_results = ocr_onImage(image, east_model, debug=1)
        print(f"\nOCR Results: {len(ocr_results)} text regions processed")
        for i, text in ocr_results.items():
            print(f"Region {i}: '{text}'")
    except KeyboardInterrupt:
        print("\nVisualization interrupted by user")
    except Exception as e:
        print(f"Error during OCR: {e}")

def main():
    """Main function to test smart gap functionality."""
    
    # Test with actual book spine images from previous runs
    test_images = [
        "output/predict32/book/Books_00005_3.jpg",  # This should be the Jaron Lanier case
        "output/predict32/book/Books_00005_0.jpg",
        "output/predict32/book/Books_00005_1.jpg", 
        "output/predict32/book/Books_00005_2.jpg"
    ]
    
    print("Testing SMART GAP ANALYSIS with real book spine extracts...")
    print("=" * 70)
    
    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n{'='*50}")
            test_dynamic_gap_with_image(image_path)
        else:
            print(f"Image not found: {image_path}")
    
    # Also test with the original bus image for comparison
    print(f"\n{'='*50}")
    print("Comparison with bus.jpg:")
    test_image_path = "example-files/bus.jpg"
    if os.path.exists(test_image_path):
        test_dynamic_gap_with_image(test_image_path)
    else:
        print(f"Bus image not found: {test_image_path}")

if __name__ == "__main__":
    main()
