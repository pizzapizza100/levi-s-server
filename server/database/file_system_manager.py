"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import logging

import asyncio
import os

from glob import glob
from pathlib import Path

from common.file_handling.directory_handler import DirectoryHandler
from common.file_handling.file_handler import FileHandler


#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #

class FileSystemManager:
    def __init__(self, root: Path):
        self._root = root
        self._files: dict[Path, [FileHandler, DirectoryHandler]] = {}

    async def scan_existing_files(self):
        files = [Path(y) for x in os.walk(self._root) for y in glob(os.path.join(x[0], '*'))]
        logging.info(f"Scanning database files... ({len(files)} files)")
        for file_path in files:
            if os.path.isfile(file_path):
                self._files[file_path] = FileHandler(file_path)
            elif os.path.isdir(file_path):
                self._files[file_path] = DirectoryHandler(file_path)
        logging.info(f"Scan Done.")

    async def _get_file_handler(self, file_path: Path) -> FileHandler:
        try:
            return self._files[self._root / file_path]
        except KeyError:
            raise FileNotFoundError()

    async def get_file(self, file_path: Path) -> bytes:
        return await (await self._get_file_handler(file_path)).read_file()

    async def save_file(self, file_path: Path, file_data: bytes):
        file_handler = FileHandler(self._root / file_path)
        await file_handler.write_file(file_data)
        self._files[self._root / file_path] = file_handler

    async def delete_file(self, file_path: Path):
        await (await self._get_file_handler(file_path)).delete_file()

    async def move_file(self, source_file_path: Path, destination_file_path: Path):
        await (await self._get_file_handler(source_file_path)).move_file(destination_file_path=destination_file_path)
#   - - - - - Functions - - - - -   #
