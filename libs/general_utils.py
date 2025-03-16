import os

import config

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

