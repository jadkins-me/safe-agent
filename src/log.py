"""
===============================================================================
Title : log.py

Description : Shared log writer usable by all modules

===============================================================================
"""

import logging
import os
import time
import constants

class LogWriter:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LogWriter, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_to_file=False, log_file_path=constants.LOG_FILE_PATH):
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger('LogWriter')
            self.logger.setLevel(logging.DEBUG)

            # Custom time function to get UTC time
            logging.Formatter.converter = time.gmtime

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt=constants.DATE_FORMAT)
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)

            # File handler
            if log_to_file:
                if not os.path.exists(os.path.dirname(log_file_path)):
                    try:
                        os.makedirs(os.path.dirname(log_file_path))
                    except Exception as e:
                        print(f"Error creating log directory: {e}")
                        log_to_file = False
                if log_to_file:
                    file_handler = logging.FileHandler(log_file_path)
                    file_handler.setLevel(logging.DEBUG)
                    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt=constants.DATE_FORMAT)
                    file_handler.setFormatter(file_format)
                    self.logger.addHandler(file_handler)
            self.initialized = True

    def log(self, message, level=logging.INFO):
        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.INFO:
            self.logger.info(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)
