"""
Description:
"""

#   - - - - - Imports - - - - -   #
from dataclasses import dataclass
from enum import Enum, auto


#   - - - - - Constants - - - - -   #


#   - - - - - Classes - - - - -   #
from typing import Any


class MessageType(Enum):
    # access
    OK = auto()
    ERROR = auto()
    ACCESS_DENIED = auto()

    # authorization
    LOGIN = auto()
    LOGOUT = auto()

    # file_handling
    DOWNLOAD_FILE = auto()  
    UPLOAD_FILE = auto()
    DELETE_FILE = auto()
    RENAME_FILE = auto()



class Message:
    def __init__(self, message_type: MessageType, content: bytes):
        self.message_type: MessageType = message_type
        self.length: int = len(content)
        self.content: bytes = content

    def __str__(self):
        return str(self.__dict__)

    async def to_dict(self):
        return self.__dict__
