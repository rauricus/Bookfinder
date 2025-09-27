#!/usr/bin/env python3
"""
Script to optimize YOLO model for different platform deployments.
Supports ONNX export with platform-specific optimizations for Raspberry Pi and other devices.

Usage: python3 models/quantize_model.py [options]
Run from project root directory.
"""

import argparse
import os
import sys
from pathlib import Path

import torch
from ultralytics import YOLO
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_model(model_path, output_path=None, platform=None, further_optimize=False):
    """
    Optimize YOLO model for specific platforms using ONNX export
    
    Args:
        model_path: Path to the original .pt model
        output_path: Path where to save the optimized model (optional)
        platform: Target platform ('rpi-3b-plus', 'generic', etc.)
        further_optimize: Apply additional optimizations (nms, simplify)
    """
    
    # Check if input model exists
    if not os.path.exists(model_path):
        logger.error(f"❌ Model file not found: {model_path}")
        return False
    
    # Generate output path if not provided
    if output_path is None:
        model_dir = os.path.dirname(model_path)
        model_name = os.path.splitext(os.path.basename(model_path))[0]
        suffix = f"_{platform}" if platform else "_optimized"
        output_path = os.path.join(model_dir, f"{model_name}{suffix}.onnx")
    
    logger.info(f"🔄 Loading model from: {model_path}")
    logger.info(f"🎯 Target platform: {platform or 'generic'}")
    logger.info(f"⚡ Further optimization: {'enabled' if further_optimize else 'disabled'}")
    
    try:
        # Load the model
        model = YOLO(model_path)
        
        logger.info(f"✅ Model loaded successfully")
        logger.info(f"📊 Original model size: {os.path.getsize(model_path) / 1024 / 1024:.2f} MB")
        
        # Set export parameters based on platform
        export_params = {
            'format': 'onnx',
            'device': 'cpu'
        }
        
        if platform == 'rpi-3b-plus':
            logger.info("🔄 Applying Raspberry Pi 3B+ optimizations...")
            export_params.update({
                'half': True,      # FP16 precision for smaller model
                'optimize': True   # ONNX graph optimization
            })
            
            if further_optimize:
                logger.info("⚡ Applying further optimizations (NMS, simplify)...")
                export_params.update({
                    'nms': True,      # Include NMS in the model
                    'simplify': True  # Simplify ONNX graph
                })
        
        elif platform == 'generic':
            logger.info("🔄 Applying generic optimizations...")
            export_params.update({
                'optimize': True
            })
            
            if further_optimize:
                export_params.update({
                    'simplify': True
                })
        
        logger.info("🔄 Starting model optimization...")
        logger.info(f"📋 Export parameters: {export_params}")
        
        # Export the model
        optimized_path = model.export(**export_params)
        
        # Move the optimized model to the desired output path if different
        if optimized_path != output_path:
            import shutil
            shutil.move(optimized_path, output_path)
        
        logger.info(f"✅ Optimized model saved to: {output_path}")
        logger.info(f"📊 Optimized model size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
        
        # Calculate compression ratio
        original_size = os.path.getsize(model_path)
        optimized_size = os.path.getsize(output_path)
        compression_ratio = original_size / optimized_size
        
        logger.info(f"🎯 Compression ratio: {compression_ratio:.2f}x")
        logger.info(f"💾 Size reduction: {(1 - optimized_size/original_size) * 100:.1f}%")
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Error during optimization: {str(e)}")
        return False

def validate_onnx_model(onnx_path, test_image_path=None):
    """
    Validate that the ONNX model works correctly
    
    Args:
        onnx_path: Path to the ONNX model
        test_image_path: Path to a test image for validation
    """
    
    logger.info("🔍 Validating ONNX model...")
    
    try:
        # Try to load with ONNX Runtime if available
        try:
            import onnxruntime as ort
            
            # Create inference session
            session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
            
            logger.info("✅ ONNX model loaded successfully with ONNXRuntime")
            
            # Get input details
            input_details = session.get_inputs()[0]
            logger.info(f"📊 Input shape: {input_details.shape}")
            logger.info(f"📊 Input type: {input_details.type}")
            
            # If test image is provided, run inference
            if test_image_path and os.path.exists(test_image_path):
                logger.info(f"🔄 Running test inference on: {test_image_path}")
                
                import cv2
                import numpy as np
                
                # Load and preprocess image
                img = cv2.imread(test_image_path)
                if img is None:
                    logger.error(f"❌ Could not load test image: {test_image_path}")
                    return False
                    
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_resized = cv2.resize(img_rgb, (640, 640))  # Standard YOLO input size
                img_array = img_resized.astype(np.float32) / 255.0
                img_array = np.transpose(img_array, (2, 0, 1))  # HWC to CHW
                img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
                
                # Run inference
                input_name = session.get_inputs()[0].name
                outputs = session.run(None, {input_name: img_array})
                
                logger.info("✅ Test inference completed successfully")
                logger.info(f"📊 Output shapes: {[output.shape for output in outputs]}")
            
        except ImportError:
            logger.warning("⚠️ ONNXRuntime not available, trying with PyTorch...")
            
            # Fallback to torch.onnx if ONNXRuntime is not available
            import onnx
            
            # Load and check the ONNX model
            onnx_model = onnx.load(onnx_path)
            onnx.checker.check_model(onnx_model)
            
            logger.info("✅ ONNX model structure is valid")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during validation: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Optimize YOLO model for different platform deployments')
    parser.add_argument(
        '--model', 
        default='models/detect-book-spines.pt',
        help='Path to the original YOLO model (default: models/detect-book-spines.pt)'
    )
    parser.add_argument(
        '--output',
        help='Output path for optimized model (default: auto-generated)'
    )
    parser.add_argument(
        '--platform',
        choices=['rpi-3b-plus', 'generic'],
        default='generic',
        help='Target platform for optimization (default: generic)'
    )
    parser.add_argument(
        '--further',
        action='store_true',
        help='Apply further optimizations (nms, simplify)'
    )
    parser.add_argument(
        '--test-image',
        default='example-files/books/Books_00005.png',
        help='Test image for validation (default: example-files/books/Books_00005.png)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate the optimized model after creation'
    )
    
    args = parser.parse_args()
    
    logger.info("📘 YOLO Model Optimization Script")
    logger.info("="*50)
    logger.info(f"📁 Working directory: {os.getcwd()}")
    
    # Validate that we're running from project root
    if not os.path.exists('models') or not os.path.exists('example-files'):
        logger.error("❌ Please run this script from the project root directory")
        logger.error("   Example: python3 models/quantize_model.py")
        sys.exit(1)
    
    # Optimize the model
    result = optimize_model(args.model, args.output, args.platform, args.further)
    
    if not result:
        logger.error("❌ Model optimization failed")
        sys.exit(1)
    
    # Validate if requested
    if args.validate:
        output_path = result if isinstance(result, str) else args.output
        if output_path is None:
            model_dir = os.path.dirname(args.model)
            model_name = os.path.splitext(os.path.basename(args.model))[0]
            suffix = f"_{args.platform}" if args.platform else "_optimized"
            output_path = os.path.join(model_dir, f"{model_name}{suffix}.onnx")
        
        validate_onnx_model(output_path, args.test_image)
    
    logger.info("🎉 Model optimization completed successfully!")
    logger.info("💡 You can now use the optimized ONNX model for inference")
    logger.info(f"📂 Optimized model location: {result if isinstance(result, str) else output_path}")

if __name__ == "__main__":
    main()