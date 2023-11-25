"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import json
from typing import Any
from server.user.user_permissions import UserPermissions

#   - - - - - Constants - - - - -   #

USER_NAME_KEY = "username"
PASSWORD_KEY = "password"
USER_PERMISSIONS_KEY =  "user_permissions"

#   - - - - - Classes - - - - -   #

class User:
    def __init__(self, raw_user_data: str):
        user_data: dict[str: Any] = json.loads(raw_user_data)
        username: str = user_data[USER_NAME_KEY]
        password: str = user_data[PASSWORD_KEY]
        permissions = UserPermissions(user_data[USER_PERMISSIONS_KEY])

#   - - - - - Functions - - - - -   #
