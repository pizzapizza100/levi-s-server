"""
Description: 
"""

#   - - - - - Imports - - - - -   #

from enum import Enum, auto

#   - - - - - Constants - - - - -   #

#   - - - - - Classes - - - - -   #


class UserPermissions(Enum):
    ROOT = auto()
    DOWNLOAD_FILE = auto()
    UPLOAD_FILE = auto()
    DELETE_FILE = auto()
    RENAME_FILE = auto()


class User:
    def __init__(self, user_id: str, permissions: set[str | UserPermissions] | list[str | UserPermissions],
                 is_logged_in=False):
        self.user_id = user_id
        self.permissions = set()
        self.is_logged_in = is_logged_in
        for permission in permissions:
            self.permissions.add(permission if isinstance(permission, UserPermissions)
                                 else UserPermissions.__dict__[permission])

    def __str__(self):
        return str({"user_id": self.user_id, "permissions": [permission.name for permission in self.permissions]})

    def __hash__(self):
        return hash(hash(self.user_id) + hash(tuple(self.permissions)))


#   - - - - - Functions - - - - -   #
