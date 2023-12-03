"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from server.database.database_exceptions import DataBaseFileNotFound
from server.database.file_system_manager import FileSystemManager
from common.user.user import User, UserPermissions


#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #

class AbstractDataBaseManager(ABC):
    def __init__(self, database_path: Path):
        self._database_path: Path = database_path
        self._database_mutex = asyncio.Lock()
        self._file_system_manager = FileSystemManager(database_path.parent)

    async def create(self, database_path: Path = None, override_exiting: bool = False,
                     create_if_missing: bool = False):
        if database_path is None:
            database_path = self._database_path

        if database_path.exists():
            if override_exiting:
                logging.warning(f"Overriding database at {self._database_path}")
                await self.create_new_database(database_path)
            else:
                logging.info(f"Found database at {self._database_path}")
        elif create_if_missing:
            await self.create_new_database(database_path, use_new_database=True)
        else:
            raise DataBaseFileNotFound()

    # --- database's functions --- #

    @abstractmethod
    async def create_new_database(self, path: Path, use_new_database: bool = True):
        ...

    @abstractmethod
    async def load(self):
        ...

    @abstractmethod
    async def save(self, path: Path = None):
        ...

    # --- files' functions --- #
    async def get_file(self, file_name: Path):
        return await self._file_system_manager.get_file(file_path=file_name)

    async def save_file(self, file_path: Path, file_data: bytes):
        await self._file_system_manager.save_file(file_path=file_path, file_data=file_data)

    async def delete_file(self, file_path: Path):
        await self._file_system_manager.delete_file(file_path=file_path)

    async def move_file(self, source_file_path: Path, destination_file_path: Path):
        await self._file_system_manager.move_file(source_file_path=source_file_path,
                                                  destination_file_path=destination_file_path)

    # --- users' functions --- #

    @abstractmethod
    async def get_user(self, user_id: str) -> User:
        ...

    @abstractmethod
    async def update_user_permissions(self, user_id, user_permissions: UserPermissions):
        ...

    @abstractmethod
    async def add_user(self, user: User):
        ...

    @abstractmethod
    async def delete_user(self, user_id):
        ...

#   - - - - - Functions - - - - -   #
