import logging
import os
import platform
import sys
from typing import Dict, Any

HOME_DIR = os.getcwd()
MODEL_DIR = os.path.join(HOME_DIR, "models")
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
OUTPUT_DIR = os.path.join(HOME_DIR, "output/predict")

# Supported languages
SUPPORTED_LANGUAGES = ["de"]

# OCR Settings for Swiss Market
OCR_LANGUAGES = 'deu+eng'  # German + English covers most cases
OCR_PSM_MODE = 6  # Uniform block of text (good for book spines)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Initialise the logging framework
#
#   The log level can be controlled via the LOG_LEVEL environment variable, and the log file
#   name can be set using the LOG_FILE environment variable. By default, the log level is set
#   to INFO, and logs are written to 'app.log'.
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_file = os.getenv("LOG_FILE", "app.log")

# Reset the root logger only if it already has handlers
if logging.root.handlers:
    print("Re-initialising the root logger. To avoid this, try to import the config module right after the system modules.")
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# =============================================================================
# PLATFORM CONFIGURATION
# =============================================================================

# Platform can be set via environment variable or defaults to 'generic'
CURRENT_PLATFORM = os.environ.get('BOOKFINDER_PLATFORM', 'generic')

# =============================================================================
# PLATFORM-SPECIFIC CONFIGURATIONS
# =============================================================================

PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    'generic': {
        'model_file': 'detect-book-spines.pt',
        'model_format': 'pytorch',
        'inference_size': (640, 640),
        # 'device': 'cpu',
        # 'batch_size': 2,
        # 'num_threads': 0,
        # 'memory_limit_mb': 1024,
        # 'use_gpu': False,
        # 'optimization_level': 'balanced',
        # 'preprocessing': {
        #     'resize_method': 'bilinear',
        #     'normalize': True
        # },
        # 'postprocessing': {
        #     'nms_threshold': 0.45,
        #     'confidence_threshold': 0.25
        # }
    },
    
    'rpi-3b-plus': {
        'model_file': 'detect-book-spines_rpi-3b-plus_optimized.onnx',
        'model_format': 'onnx',
        'inference_size': (320, 320),  # Smaller input for performance
        #'crop_from_original': True,    # Extract book spines from original resolution
        # 'device': 'cpu',
        # 'batch_size': 1,  # Single image processing
        # 'num_threads': 4,  # Limited cores on RPi
        # 'memory_limit_mb': 512,  # Conservative memory usage
        # 'use_gpu': False,
        # 'optimization_level': 'performance',
        # 'preprocessing': {
        #     'resize_method': 'nearest',  # Faster on CPU
        #     'normalize': True
        # },
        # 'postprocessing': {
        #     'nms_threshold': 0.5,  # Slightly more conservative
        #     'confidence_threshold': 0.3
        # },
        # 'original_processing': True  # Keep original image for cropping
    },
    
    # 'macos': {
    #     'model_file': 'detect-book-spines.pt',
    #     'model_format': 'pytorch',
    #     'inference_size': (640, 640),
    #     'device': 'cpu',  # or 'mps' if Metal Performance Shaders available
    #     'batch_size': 4,
    #     'num_threads': 0,  # Use all available cores
    #     'memory_limit_mb': 2048,
    #     'use_gpu': False,
    #     'optimization_level': 'balanced',
    #     'preprocessing': {
    #         'resize_method': 'bilinear',
    #         'normalize': True
    #     },
    #     'postprocessing': {
    #         'nms_threshold': 0.45,
    #         'confidence_threshold': 0.25
    #     }
    # },
    
    # 'ai-camera': {
    #     'model_file': 'detect-book-spines_ai-camera.onnx',
    #     'model_format': 'onnx',
    #     'inference_size': (416, 416),  # Optimized for AI accelerator
    #     'device': 'ai-accelerator',
    #     'batch_size': 2,
    #     'num_threads': 2,  # AI accelerator handles heavy lifting
    #     'memory_limit_mb': 256,
    #     'use_gpu': True,  # AI accelerator
    #     'optimization_level': 'speed',
    #     'preprocessing': {
    #         'resize_method': 'bilinear',
    #         'normalize': True
    #     },
    #     'postprocessing': {
    #         'nms_threshold': 0.4,
    #         'confidence_threshold': 0.2  # AI accelerator can handle more detections
    #     },
    #     'remote_processing': True,  # Send results to RPi for text processing
    #     'communication': {
    #         'protocol': 'mqtt',  # or 'http', 'websocket'
    #         'rpi_endpoint': 'localhost:5010'
    #     }
    # }
}

# =============================================================================
# RUNTIME CONFIGURATION
# =============================================================================

def get_config(platform: str = None) -> Dict[str, Any]:
    """
    Get configuration for specified platform or current platform.
    
    Args:
        platform: Platform name or None for auto-detection
        
    Returns:
        Dict containing platform-specific configuration
    """
    if platform is None:
        platform = CURRENT_PLATFORM
    
    if platform not in PLATFORM_CONFIGS:
        logging.warning(f"Unknown platform '{platform}', falling back to 'generic'")
        platform = 'generic'
    
    config = PLATFORM_CONFIGS[platform].copy()
    config['platform'] = platform
    config['model_path'] = os.path.join(MODEL_DIR, config['model_file'])
    
    return config

# Current active configuration
CONFIG = get_config()

# =============================================================================
# PLATFORM-SPECIFIC MODEL PATHS
# =============================================================================

def get_model_path(platform: str = None) -> str:
    """Get the appropriate model path for the platform."""
    config = get_config(platform)
    return config['model_path']

def get_inference_size(platform: str = None) -> tuple:
    """Get the inference input size for the platform."""
    config = get_config(platform)
    return config['inference_size']

# =============================================================================
# PLATFORM INFO LOGGING
# =============================================================================

def log_platform_info():
    """Log current platform and configuration info."""
    logging.info(f"Platform: {CURRENT_PLATFORM}")
    logging.info(f" Model: {CONFIG['model_file']}")
    logging.info(f" Format: {CONFIG['model_format']}")
    logging.info(f" Inference size: {CONFIG['inference_size']}")
    
    if CONFIG.get('crop_from_original'):
        logging.info(" Using original resolution for book spine cropping")

# Log platform info on import
log_platform_info()
