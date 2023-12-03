"""
Description: 
"""

#   - - - - - Imports - - - - -   #

from pathlib import Path
from common.file_handling.file_handler import FileHandler

#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #


class DirectoryHandler:
    def __init__(self, file_path: Path):
        self._file_path = file_path

#   - - - - - Functions - - - - -   #
