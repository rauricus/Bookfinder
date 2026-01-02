#!/usr/bin/env python3
"""
Test script for model loading with different formats (PyTorch vs ONNX).
This tests the platform-specific model selection and format handling.
"""

import sys
import os
import time
import argparse
import numpy as np
import cv2
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import configuration
import config

def load_pytorch_model(model_path):
    """Load PyTorch YOLO model."""
    try:
        from ultralytics import YOLO
        
        print(f"Loading PyTorch model: {model_path}")
        model = YOLO(model_path)
        print("✅ PyTorch model loaded successfully")
        return model, 'pytorch'
    except Exception as e:
        print(f"❌ Failed to load PyTorch model: {e}")
        return None, None

def load_onnx_model(model_path):
    """Load ONNX model."""
    try:
        import onnxruntime as ort
        print(f"Loading ONNX model: {model_path}")
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        print("✅ ONNX model loaded successfully")
        
        # Get input/output info
        input_details = session.get_inputs()[0]
        output_details = session.get_outputs()
        
        print(f"Input: {input_details.name} {input_details.shape}")
        print(f"Outputs: {[f'{out.name} {out.shape}' for out in output_details]}")
        
        return session, 'onnx'
    except ImportError:
        print("❌ ONNXRuntime not installed")
        return None, None
    except Exception as e:
        print(f"❌ Failed to load ONNX model: {e}")
        return None, None

def test_model_loading(platform=None):
    """Test model loading for specified platform."""
    cfg = config.get_config(platform)
    
    print(f"\nTesting Model Loading for Platform: {cfg['platform']}")
    print("=" * 60)
    print(f" Model File: {cfg['model_file']}")
    print(f" Format: {cfg['model_format']}")
    print(f" Inference Size: {cfg['inference_size']}")
    print(f" Path: {cfg['model_path']}")
    
    # Check if model file exists
    if not os.path.exists(cfg['model_path']):
        print(f"❌ Model file not found: {cfg['model_path']}")
        return False
    
    print(f" Model Size: {os.path.getsize(cfg['model_path']) / 1024 / 1024:.2f} MB")
    
    # Load model based on format
    start_time = time.time()
    
    if cfg['model_format'] == 'pytorch':
        model, format_type = load_pytorch_model(cfg['model_path'])
    elif cfg['model_format'] == 'onnx':
        model, format_type = load_onnx_model(cfg['model_path'])
    else:
        print(f"❌ Unsupported model format: {cfg['model_format']}")
        return False
    
    if model is None:
        return False
    
    load_time = time.time() - start_time
    print(f"  Load Time: {load_time:.3f} seconds")
    
    return True

def test_inference_sizes():
    """Test different inference sizes and their impact."""
    print(f"\n Testing Inference Sizes")
    print("=" * 60)
    
    # Test with a dummy image
    for platform in config._PLATFORM_CONFIGS.keys():
        cfg = config.get_config(platform)
        inference_size = cfg['inference_size']
        
        # Create dummy image data
        dummy_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        
        # Resize to inference size
        start_time = time.time()
        resized = cv2.resize(dummy_image, inference_size)
        resize_time = time.time() - start_time
        
        # Calculate memory usage
        original_memory = dummy_image.nbytes / 1024 / 1024  # MB
        resized_memory = resized.nbytes / 1024 / 1024  # MB
        
        print(f"{platform}:")
        print(f"   Original: 640x480 ({original_memory:.2f} MB)")
        print(f"   Resized: {inference_size[0]}x{inference_size[1]} ({resized_memory:.2f} MB)")
        print(f"   Resize Time: {resize_time*1000:.3f} ms")
        print(f"   Memory Reduction: {(1 - resized_memory/original_memory)*100:.1f}%")
        print()

def main():
    parser = argparse.ArgumentParser(description='Test model loading and platform configurations')
    parser.add_argument(
        '--platform', '-p',
        choices=list(config._PLATFORM_CONFIGS.keys()) + ['all'],
        default='all',
        help='Platform to test (default: all)'
    )
    parser.add_argument(
        '--sizes', '-s',
        action='store_true',
        help='Test inference size impact'
    )
    
    args = parser.parse_args()
    
    print("🧪 BookFinder Model Loading Test")
    print("=" * 60)
    
    if args.platform == 'all':
        platforms = list(config._PLATFORM_CONFIGS.keys())
    else:
        platforms = [args.platform]
    
    success_count = 0
    for platform in platforms:
        if test_model_loading(platform):
            success_count += 1
    
    print(f"\n✅ Successfully loaded {success_count}/{len(platforms)} models")
    
    if args.sizes:
        test_inference_sizes()
    
    if success_count < len(platforms):
        print("\n💡 Missing models can be created with:")
        print("   python3 models/quantize_model.py --platform <platform-name>")

if __name__ == "__main__":
    main()