import logging
import os

from . import general_utils
from . import image_utils
from . import text_utils
from . import ocr_utils
from . import lookup_utils

def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "app.log")

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def initialize():
    
    setup_logging()
    
    general_utils.initialize()
    image_utils.initialize()
    text_utils.initialize()
    ocr_utils.initialize()
    lookup_utils.initialize()
