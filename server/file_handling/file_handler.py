"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import logging

import asyncio
from pathlib import Path

import aiofiles

#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #

class FileHandler:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self.file_mutex = asyncio.Lock()

    async def read_file(self):
        async with aiofiles.open(self._file_path, "rb") as file:
            logging.info(f"Reading file: {self._file_path}")
            return await file.read()


#   - - - - - Functions - - - - -   #
