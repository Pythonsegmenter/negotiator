import logging
import os
import sys
from datetime import datetime
from typing import Optional


def setup_logging(console_log_level: Optional[int] = None) -> logging.Logger:
    """Sets up logging configuration.

    Creates a directory for logs based on the current date and configures
    the logger to write logs to a file and optionally to the console.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Define the base log directory
    base_log_dir = "logs"
    if not os.path.exists(base_log_dir):
        os.makedirs(base_log_dir)

    # Create a directory structure for logs
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%Hh-%Mmin-%Ssec")

    # Create a folder for the current date if it doesn't exist
    date_folder = os.path.join(base_log_dir, current_date)
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)

    # Configure the logger
    log_file_path = os.path.join(date_folder, f"{current_time}.log")
    logger = logging.getLogger("main_logger")

    # Prevent adding multiple handlers if logger already has handlers
    if not logger.hasHandlers():
        file_handler = logging.FileHandler(log_file_path)
        stream_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        if (
            console_log_level is not None
        ):  # This will determine which logs are shown in the console
            stream_handler.setLevel(console_log_level)
            logger.addHandler(stream_handler)

        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)

    return logger


# Ensure the module is uniquely identified so that it is not created multiple times
# Explanation:
# This situation can occur if:
# 1. The module is imported using different relative paths in different parts of the code.
#    Example: In your project, 'logging_config' might be imported as:
#    - 'from app.log_manager.logging_config import logger' in 'app/__init__.py'
#    - 'from log_manager.logging_config import logger' in 'app/application.py'
#    This can lead to the module being loaded twice under different names.
# 2. The module is symlinked in the filesystem and imported using different paths.
# 3. The module is part of a package that is imported using different package structures.
# 4. The module is reloaded using importlib.reload() but with a different module name.
current_module_path = os.path.abspath(__file__)
# Iterate over all loaded modules
for module in sys.modules.values():
    # Check if the module has a '__file__' attribute and it's not None
    if module and hasattr(module, "__file__") and module.__file__ is not None:
        # Compare the absolute path of the current module with the path of each loaded module
        if (
            os.path.abspath(module.__file__) == current_module_path
            and module.__name__ != __name__
        ):
            # If the paths match but the module names differ, raise an ImportError
            raise ImportError(
                "logging_config is being imported via multiple paths:"
                f" '{module.__name__}' and '{__name__}'. Are you sure you used the full"
                " path like this: 'from app.log_manager.logging_config import logger'."
            )


# Set the desired console log level here
# Logging levels hierarchy (from most to least severe):
# CRITICAL: 50 - A very serious error, indicating that the program itself may be unable to continue running.
# ERROR: 40 - Due to a more serious problem, the software has not been able to perform some function.
# WARNING: 30 - An indication that something unexpected happened, or indicative of some problem in the near future.
# INFO: 20 - Confirmation that things are working as expected.
# DEBUG: 10 - Detailed information, typically of interest only when diagnosing problems.
# NOTSET: 0 - When a logger is created, the level is set to NOTSET (which means all messages are processed).
LOGGER_CONSOLE_LEVEL = (
    logging.INFO
)  # Change to logging.INFO, logging.WARNING, etc., as needed
# Initialize logging once
logger = setup_logging(console_log_level=LOGGER_CONSOLE_LEVEL)
