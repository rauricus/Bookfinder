import logging
import os

HOME_DIR = os.getcwd()
MODEL_DIR = os.path.join(HOME_DIR, "models")
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
OUTPUT_DIR = os.path.join(HOME_DIR, "output/predict")

# Supported languages
SUPPORTED_LANGUAGES = ["de"]

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
