import os
import config

from libs.logging import get_logger

# Module-specific logger that uses the module name as prefix for log messages
logger = get_logger(__name__)

def initialize():
    # Add any necessary initialization code here
    pass

def get_next_directory(base_path=config.OUTPUT_DIR):
    """
    Get the next available directory for output.

    Args:
        base_path (str): The base path for the output directory.

    Returns:
        str: The next available directory path.
    """
    # Check if the base directory exists
    if not os.path.exists(base_path):
        return base_path
    else:
        # Find the next available numbered directory
        i = 2
        while os.path.exists(f"{base_path}{i}"):
            i += 1
        return f"{base_path}{i}"

def iso639_1_to_3(language_code):
    """
    Converts ISO 639-1 (2-letter) codes to ISO 639-2 (3-letter) codes.

    Args:
        language_code (str): The ISO 639-1 code (e.g., "de", "en").

    Returns:
        str: The ISO 639-2 code (e.g., "ger", "eng"). Defaults to "ger" if unknown.
    """
    mapping = {
        "de": "ger",
        "en": "eng",
        "fr": "fre",
        "es": "spa",
        "it": "ita",
        "nl": "dut",
        "sv": "swe",
        "no": "nor",
        "da": "dan",
        "fi": "fin",
        "pl": "pol",
        "cs": "cze",
        "ru": "rus",
        "zh": "chi",
        "ja": "jpn",
        "ko": "kor"
    }
    return mapping.get(language_code.lower(), "ger")
