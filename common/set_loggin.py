"""
Description: 
"""

#   - - - - - Imports - - - - -   #

import logging
from colorlog import ColoredFormatter

#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #


#   - - - - - Functions - - - - -   #

def set_logger():
    log_level = logging.DEBUG
    log_format = "%(log_color)s%(asctime)s | %(levelname)-4s | %(message)s%(reset)s"
    logging.root.setLevel(log_level)
    stream = logging.StreamHandler()
    stream.setLevel(log_level)
    stream.setFormatter(ColoredFormatter(log_format))
    logging.basicConfig(handlers=[stream], format=log_format)
