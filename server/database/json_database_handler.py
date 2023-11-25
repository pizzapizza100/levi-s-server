"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import json
import logging
from json import JSONDecodeError
from pathlib import Path

import aiofiles as aiofiles
from typing import Any

from server.database.database_exceptions import FileTrailerIsNotValid, DataBaseFileContentInvalid
from server.user.user import User
from server.user.user_permissions import UserPermissions
from server.database.abstract_database_handler import AbstractDataBaseManager
from server.file_handling.file_handler import FileHandler

#   - - - - - Constants - - - - -   #

USERS_KEY = "users"
EMPTY_JSON_DB = {USERS_KEY: {}}


#   - - - - - Classes - - - - -   #

class JSONDataBaseManager(AbstractDataBaseManager):
    def __init__(self, database_path: Path):
        if not database_path.name.endswith(".json"):
            raise FileTrailerIsNotValid("json file_handling must end with a '.json' trailer.")
        self._loaded_data = {}
        super(JSONDataBaseManager, self).__init__(database_path=database_path)

    async def create_new_database(self, new_database_path: Path, use_new_database: bool = True):
        async with self.database_mutex:
            new_database_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(new_database_path, "w") as new_database_file:
                await new_database_file.write(json.dumps(EMPTY_JSON_DB, sort_keys=True, indent=4))

            logging.info(f"Creating new database at {self.database_path}")

            if use_new_database:
                self.database_path = new_database_path
                logging.info(f"Using new database at {self.database_path}")

    async def load(self):
        async with self.database_mutex, aiofiles.open(self.database_path, "r") as database_file:
            try:
                logging.info(f"Loading database, size: {database_file.__sizeof__()}")
                self._loaded_data: dict[Any, Any] = json.loads(await database_file.read())
            except JSONDecodeError:
                raise DataBaseFileContentInvalid()

            await self._verify_files()

    async def get_file(self, file_name: str):
        return await FileHandler(self.file_system_path / Path(file_name)).read_file()

    async def _verify_files(self):
        ...

    async def get_user_permissions(self, user_id) -> UserPermissions:
        ...

    async def update_user_permissions(self, user_id, user_permissions: UserPermissions):
        ...

    async def add_user(self, user: User):
        ...

    async def delete_user(self, user_id):
        ...

    async def save(self, path: Path = None):
        async with aiofiles.open(path if path is not None else self.database_path, "w") as database_file, \
                self.database_mutex:
            await database_file.write(json.dumps(self._loaded_data))
            logging.info(f"Saved database at: {database_file.name}")

#   - - - - - Functions - - - - -   #
