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

from server.database.abstract_database_handler import AbstractDataBaseManager
from server.database.database_exceptions import DataBaseFileTrailerIsNotValid, DataBaseFileContentInvalid
from common.user.user import User, UserPermissions

#   - - - - - Constants - - - - -   #

USERS_KEY = "users"
FILES_KEY = "files"
EMPTY_JSON_DB = {
    FILES_KEY: {

    },
    USERS_KEY: {
        User(user_id="Root user", permissions={UserPermissions.ROOT}),
        User(user_id="Testing user", permissions={UserPermissions.DOWNLOAD_FILE, UserPermissions.UPLOAD_FILE,
                                                  UserPermissions.DELETE_FILE, UserPermissions.RENAME_FILE}),
        User(user_id="No permissions user", permissions=set()),
    }
}


#   - - - - - Classes - - - - -   #
class JSONDataBaseManager(AbstractDataBaseManager):
    def __init__(self, database_path: Path):
        if not database_path.name.endswith(".json"):
            raise DataBaseFileTrailerIsNotValid("json file_handling must end with a '.json' trailer.")
        self._loaded_data: dict[Any, Any] = {}
        super(JSONDataBaseManager, self).__init__(database_path=database_path)

    async def create_new_database(self, new_database_path: Path, use_new_database: bool = True):
        async with self._database_mutex:
            new_database_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(new_database_path, "w") as new_database_file:
                await new_database_file.write(json.dumps(EMPTY_JSON_DB, sort_keys=True, indent=4,
                                                         default=lambda obj: list(obj)
                                                         if isinstance(obj, set) else str(obj)))

            logging.info(f"Creating new database at {self._database_path}")

            if use_new_database:
                self._database_path = new_database_path
                logging.info(f"Using new database at {self._database_path}")

    async def load(self):
        async with self._database_mutex, aiofiles.open(self._database_path, "r") as database_file:
            try:
                logging.info(f"Loading database, size: {database_file.__sizeof__()}")
                raw_loaded_data = json.loads(await database_file.read())
                users = set()
                for user_data in raw_loaded_data[USERS_KEY]:
                    users.add(User(**eval(user_data)))

                logging.info(f"Loaded {len(users)} users.")
                self._loaded_data[USERS_KEY] = users
            except JSONDecodeError:
                raise DataBaseFileContentInvalid()

            await self._file_system_manager.scan_existing_files()

    # --- users' functions --- #
    async def get_user(self, user_id: str) -> User:
        return self._loaded_data[USERS_KEY][user_id]

    async def update_user_permissions(self, user_id, user_permissions: UserPermissions):
        ...

    async def add_user(self, user: User):
        ...

    async def delete_user(self, user_id):
        ...

    async def save(self, path: Path = None):
        async with aiofiles.open(path if path is not None else self._database_path, "w") as database_file, \
                self._database_mutex:
            await database_file.write(json.dumps(self._loaded_data))
            logging.info(f"Saved database at: {database_file.name}")

#   - - - - - Functions - - - - -   #
