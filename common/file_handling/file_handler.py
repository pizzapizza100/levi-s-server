"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import logging
import os

import asyncio
from pathlib import Path

import aiofiles

#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #

class FileHandler:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._file_mutex = asyncio.Lock()

    async def read_file(self) -> bytes:
        async with self._file_mutex, aiofiles.open(self._file_path, "rb") as file:
            logging.info(f"Reading file: {self._file_path}")
            file_data = await file.read()
            logging.info(f"Done reading file.")
        return file_data

    async def write_file(self, data: bytes):
        async with self._file_mutex, aiofiles.open(self._file_path, "wb+") as file:
            logging.info(f"Writing file: {self._file_path}")
            await file.write(data)
            logging.info(f"Done writing file.")

    async def delete_file(self):
        async with self._file_mutex:
            os.remove(self._file_path)
            logging.info(f"Deleted file {self._file_path}")

    async def move_file(self, destination_file_path: Path):
        async with self._file_mutex:
            os.rename(src=self._file_path, dst=destination_file_path, src_dir_fd=None, dst_dir_fd=None)

#   - - - - - Functions - - - - -   #
