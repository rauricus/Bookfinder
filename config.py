import logging
import os
import platform
import sys
from dotenv import load_dotenv

from typing import Dict, Any

# Load environment variables from .env file
#   System environment takes precedence; use override=true to force .env values.
load_dotenv()

__all__ = [
    'HOME_DIR',
    'MODEL_DIR',
    'DICT_DIR',
    'OUTPUT_DIR',
    'SUPPORTED_LANGUAGES',
    'CURRENT_PLATFORM',
    'BOOK_SPINE',
    'OCR',
    'get_config'
]

HOME_DIR = os.getcwd()
MODEL_DIR = os.path.join(HOME_DIR, "models")
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
OUTPUT_DIR = os.path.join(HOME_DIR, "output/predict")

# Supported languages
SUPPORTED_LANGUAGES = ["de"]



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

_PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    'generic': {
        'book_spine_detection': {
            'model_file': 'YOLO11-obb-s/detect-book-spines.pt',
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
        'ocr': {
            'model_file': 'EAST/east_text_detection.pb',
            'languages': 'deu+eng',  # German + English covers most cases
            'psm_mode': 6  # Uniform block of text (good for book spines)
        }
    },
    
    'generic-nano-model': {
        'book_spine_detection': {
            'model_file': 'YOLO11-obb-n/train3/weights/best.pt',
            'model_format': 'pytorch',
            'inference_size': (320, 320),  # Matches training size
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
        'ocr': {
            'model_file': 'EAST/east_text_detection.pb',
            'languages': 'deu+eng',  # German + English covers most cases
            'psm_mode': 6  # Uniform block of text (good for book spines)
        }
    },
    
    'rpi-3b-plus': {
        'book_spine_detection': {
            'model_file': 'YOLO11-obb-s/detect-book-spines_rpi-3b-plus_optimized.onnx',
            'model_format': 'onnx',
            'inference_size': (320, 320),  # Smaller input for performance
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
            # }
        },
        'ocr': {
            'model_file': 'EAST/east_text_detection.pb',
            'languages': 'deu+eng',  # German + English covers most cases
            'psm_mode': 6  # Uniform block of text (good for book spines)
        }
    }
    
    # 'macos': {
        # 'book_spine_detection': {
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
        # 'ocr': {
        #     'model_file': 'EAST/east_text_detection.pb',
        #     'languages': 'deu+eng',  # German + English covers most cases
        #     'psm_mode': 6  # Uniform block of text (good for book spines)
        # }
    # },
    
    # 'ai-camera': {
        # 'book_spine_detection': {
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
        # },
        # 'ocr': {
        #     'model_file': 'EAST/east_text_detection.pb',
        #     'languages': 'deu+eng',  # German + English covers most cases
        #     'psm_mode': 6  # Uniform block of text (good for book spines)
        # }
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
    
    if platform not in _PLATFORM_CONFIGS:
        logging.warning(f"Unknown platform '{platform}', falling back to 'generic'")
        platform = 'generic'
    
    config = _PLATFORM_CONFIGS[platform].copy()
    config['platform'] = platform
    config['book_spine_detection']['model_path'] = os.path.join(MODEL_DIR, config['book_spine_detection']['model_file'])
    config['ocr']['model_path'] = os.path.join(MODEL_DIR, config['ocr']['model_file'])
    
    return config

# Active configuration for the current platform, including short aliases
_CURRENT = get_config()
BOOK_SPINE = _CURRENT['book_spine_detection']
OCR = _CURRENT['ocr']

# =============================================================================
# PLATFORM INFO LOGGING
# =============================================================================

def log_platform_info():
    """Log current platform and configuration info."""
    logging.info(f"Platform: {CURRENT_PLATFORM}")
    logging.info(f" Book spin detection:")
    logging.info(f"  Model: {BOOK_SPINE['model_path']}")
    logging.info(f"  Format: {BOOK_SPINE['model_format']}")
    logging.info(f"  Inference size: {BOOK_SPINE['inference_size']}")
    logging.info(f" OCR:")
    logging.info(f"  Model: {OCR['model_path']}")
    
    if BOOK_SPINE.get('crop_from_original'):
        logging.info(" Using original resolution for book spine cropping")

# Log platform info on import
log_platform_info()
