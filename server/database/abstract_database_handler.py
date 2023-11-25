"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import logging

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from server.database.database_exceptions import DataBaseFileNotFound
from server.file_handling.file_handler import FileHandler

#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #
from server.user.user import User
from server.user.user_permissions import UserPermissions


class AbstractDataBaseManager(ABC):
    def __init__(self, database_path: Path):
        self.database_mutex = asyncio.Lock()
        self.database_path: Path = database_path
        self.file_system_path: Path = database_path.parent

    async def create(self, database_path: Path = None, override_exiting: bool = False,
                     create_if_missing: bool = False) -> "AbstractDataBaseManager":
        if database_path is None:
            database_path = self.database_path

        if database_path.exists():
            if override_exiting:
                logging.warning(f"Overriding database at {self.database_path}")
                await self.create_new_database(database_path)
            else:
                logging.info(f"Found database at {self.database_path}")
        elif create_if_missing:
            await self.create_new_database(database_path, use_new_database=True)
        else:
            raise DataBaseFileNotFound()

        return self

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
    @abstractmethod
    async def get_file(self, file: str):
        ...
    # --- users' functions --- #

    @abstractmethod
    async def get_user_permissions(self, user_id):
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
