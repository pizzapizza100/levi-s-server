"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import logging
import socket
from pathlib import Path

from typing import Callable, Coroutine, Any

from common.user.user import UserPermissions, User
from common.communication.communication_exceptions import BadlyFormattedMessage
from common.communication.message import Message, MessageType
from common.communication.network_manager import NetworkManager
from server.database.abstract_database_handler import AbstractDataBaseManager


#   - - - - - Constants - - - - -   #

#   - - - - - Classes - - - - -   #


class AccessDenied(Exception):
    ...


class NotLoggedIn(Exception):
    ...

class ClientHandler:
    def __init__(self, client_socket: socket.socket, database_manager: AbstractDataBaseManager):
        self._client_socket = client_socket
        self._database_manager = database_manager
        self._network_manager = NetworkManager(client_socket=client_socket)
        self._user = None

    async def handle_client(self):
        request = Message(message_type=MessageType.ERROR, content=b"")

        while True:
            try:
                request = await self._network_manager.receive_message()
                response: Message = await self._handle_message(request)
                await self._network_manager.send_message(response)
            except NotLoggedIn:
                await self._network_manager.send_message(Message(message_type=MessageType.ACCESS_DENIED,
                                                                 content="Please login first.".encode("utf-8")))
                logging.warning(f"{self._client_socket.getpeername()} requested a message without loggin in.")

            except AccessDenied:
                await self._network_manager.send_message(Message(message_type=MessageType.ACCESS_DENIED,
                                                                 content="Access is denied".encode("utf-8")))
                logging.warning(f"{self._client_socket.getpeername()} requested {request.message_type.value}"
                                f" with the user {self._user}")

            except BadlyFormattedMessage:
                await self._network_manager.send_message(Message(message_type=MessageType.ERROR,
                                                                 content="Message format is wrong!".encode("utf-8")))
                logging.warning(f"{self._client_socket.getpeername()} sent a message not in format!")
                break

            except ConnectionAbortedError:
                logging.error(f"An established connection was aborted by the software in your host machine")
                break

            except ConnectionResetError:
                logging.info(f"{self._client_socket.getsockname()} has disconnected")
                break

    # noinspection PyArgumentList
    async def _handle_message(self, request: Message) -> Message:
        functions: dict[MessageType: Callable[[bytes], Coroutine[Any, Any, Message]]] = {
            MessageType.DOWNLOAD_FILE: self._download_file,
            MessageType.UPLOAD_FILE: self._upload_file,
            MessageType.DELETE_FILE: self._delete_file,
        }

        if request.message_type not in functions.keys():
            logging.warning(f"{self._client_socket.getpeername()} has requested "
                            f"{MessageType(request.message_type).name} with the content {request.content},"
                            f" without permission!")
            return Message(message_type=MessageType.ACCESS_DENIED,
                           content="You are not allowed to request such an action!".encode("utf-8"))

        return await functions[request.message_type](request.content)

    async def _download_file(self, encoded_file_name: bytes) -> Message:
        try:
            file_name = encoded_file_name.decode("utf-8")
        except UnicodeDecodeError:
            raise BadlyFormattedMessage()

        logging.info(f"{self._client_socket.getpeername()} has requested to download {file_name}")

        if self._user is None:
            raise NotLoggedIn()

        if len(self._user.permissions.intersection({UserPermissions.DOWNLOAD_FILE, UserPermissions.ROOT})) == 0:
            raise AccessDenied()

        try:
            logging.info(f"Sending success message.")
            return Message(message_type=MessageType.OK, content=await self._database_manager.get_file(Path(file_name)))
        except FileNotFoundError as e:
            logging.warning(f"Could not find {file_name}, exception: {type(e), e}")
            return Message(message_type=MessageType.ERROR, content=f"Could not find {file_name}".encode("utf-8"))

    async def _upload_file(self, file_data: bytes) -> Message:
        """
        Saves a file at database.
        :param file_data: bytes of the file name and file data
            - format -> encoded_full_path_of_file + (null byte) + file_data
                * null byte is one of the following: [ \x00, '\0', 0x00 ]
        :return: Message with a response
        """

        try:
            encoded_file_name, file_data = file_data.split(b'\0', maxsplit=1)
            file_name = encoded_file_name.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            raise BadlyFormattedMessage()

        logging.info(f"{self._client_socket.getpeername()} has requested to upload {file_name}")

        if self._user is None:
            raise NotLoggedIn()

        if len(self._user.permissions.intersection({UserPermissions.UPLOAD_FILE, UserPermissions.ROOT})) == 0:
            raise AccessDenied()

        if UserPermissions.UPLOAD_FILE not in self._user.permissions:
            raise AccessDenied()

        try:
            await self._database_manager.save_file(file_path=Path(file_name), file_data=file_data)
            logging.info(f"Sending success message.")
            return Message(message_type=MessageType.OK, content=b"")
        except Exception as e:
            logging.warning(f"Could not save {file_name}, exception: {type(e), e}")
            return Message(message_type=MessageType.ERROR, content=f"Could not save {file_name}".encode("utf-8"))

    async def _delete_file(self, encoded_file_name: bytes) -> Message:
        try:
            file_name = encoded_file_name.decode("utf-8")
        except UnicodeDecodeError:
            raise BadlyFormattedMessage()

        logging.info(f"{self._client_socket.getpeername()} has requested to delete {file_name}")

        if self._user is None:
            raise NotLoggedIn()

        if len(self._user.permissions.intersection({UserPermissions.DELETE_FILE, UserPermissions.ROOT})) == 0:
            raise AccessDenied()

        try:
            await self._database_manager.delete_file(file_path=Path(file_name))
            logging.info(f"Sending success message.")
            return Message(message_type=MessageType.OK, content=b"")
        except FileNotFoundError:
            logging.warning(f"Could not find {file_name} for deletion.")
            return Message(message_type=MessageType.ERROR, content=f"Could not find {file_name}".encode("utf-8"))
        except Exception as e:
            logging.warning(f"Could not delete {file_name}, exception: {type(e), e}")
            return Message(message_type=MessageType.ERROR, content=f"Could not delete {file_name}".encode("utf-8"))

#   - - - - - Functions - - - - -   #
