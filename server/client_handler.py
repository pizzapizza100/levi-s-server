"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import logging
import socket

from typing import Callable

from common.communication.message import Message, MessageType
from common.communication.network_manager import NetworkManager
from server.database.abstract_database_handler import AbstractDataBaseManager


#   - - - - - Constants - - - - -   #

#   - - - - - Classes - - - - -   #
class ClientHandler:
    def __init__(self, client_socket: socket.socket, database_manager: AbstractDataBaseManager):
        self._client_socket = client_socket
        self._database_manager = database_manager
        self._network_manager = NetworkManager(client_socket=client_socket)

    async def handle_client(self):
        while True:
            try:
                request = await self._network_manager.receive_message()
                response: Message = await self._handle_message(request)
                await self._network_manager.send_message(response)

            except ConnectionAbortedError:
                logging.error(f"An established connection was aborted by the software in your host machine")
                break

            except ConnectionResetError:
                break

        logging.info(f"{self._client_socket.getsockname()} has disconnected")

    async def _handle_message(self, request: Message) -> Message:
        functions: dict[MessageType: Callable[[str], Message]] = {
            MessageType.DOWNLOAD_FILE: self._transfer_file
        }

        if request.message_type not in functions.keys():
            logging.warning(f"{self._client_socket} has requested {MessageType(request.message_type).name}"
                            f" with the content {request.content}, without permission!")
            return Message(message_type=MessageType.ACCESS_DENIED,
                           content="You are not allowed to request such an action!".encode("utf-8"))

        return await functions[request.message_type](request.content)

    async def _transfer_file(self, file_name_encoded: bytes) -> Message:
        file_name = file_name_encoded.decode("utf-8")
        logging.info(f"{self._client_socket.getpeername()} has requested to download {file_name}")
        try:
            return Message(message_type=MessageType.OK, content=await self._database_manager.get_file(file_name))
        except FileNotFoundError:
            logging.warning(f"Could not find {file_name}")
            return Message(message_type=MessageType.ERROR, content=f"Could not find {file_name}".encode("utf-8"))


#   - - - - - Functions - - - - -   #
