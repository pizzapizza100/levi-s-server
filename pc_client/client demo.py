"""
Description:
"""

#   - - - - - Imports - - - - -   #

import logging
import socket
from pathlib import Path

import asyncio

from common.communication.message import Message, MessageType
from common.communication.network_manager import NetworkManager
from common.file_handling.file_handler import FileHandler
from common.set_loggin import set_logger

#   - - - - - Constants - - - - -   #

SERVER_IP = "10.100.102.18"
SERVER_PORT = 16239


#   - - - - - Classes - - - - -   #
class Client:
    def __init__(self, network_manager: NetworkManager):
        self._network_manager = network_manager

    async def close_connection(self):
        await self._network_manager.close_connection()

    async def download_file(self, local_file_path: Path, remote_file_path: Path):
        logging.info(f"Requesting to download {remote_file_path}.")
        message = Message(message_type=MessageType.DOWNLOAD_FILE, content=str(remote_file_path).encode("utf-8"))
        await self._network_manager.send_message(message)
        response = await self._network_manager.receive_message()

        if response.message_type is MessageType.OK:
            await FileHandler(file_path=Path(local_file_path)).write_file(response.content)
            logging.info(f"Successfully downloaded file to {local_file_path}.")
        else:
            logging.warning(f"Failed to delete, server response: {response.content.decode()}")

    async def upload_file(self, local_file_path: Path, remote_file_path: Path):
        logging.info(f"Requesting to upload {local_file_path} to {remote_file_path}.")

        file_data = await FileHandler(file_path=local_file_path).read_file()

        data = str(remote_file_path).encode("utf-8") + b"\0" + file_data
        message = Message(message_type=MessageType.UPLOAD_FILE, content=data)
        await self._network_manager.send_message(message)
        response = await self._network_manager.receive_message()

        if response.message_type is MessageType.OK:
            logging.info(f"Successfully upload file.")
        else:
            logging.warning(f"Failed to upload, server response: {response.content.decode()}")

    async def delete_file(self, remote_file_path: Path):
        logging.info(f"Requesting to delete {remote_file_path}.")

        message = Message(message_type=MessageType.DELETE_FILE, content=str(remote_file_path).encode("utf-8"))
        await self._network_manager.send_message(message)
        response = await self._network_manager.receive_message()

        if response.message_type is MessageType.OK:
            logging.info(f"Successfully deleted file.")
        else:
            logging.warning(f"Failed to delete, server response: {response.content.decode()}")


#   - - - - - Functions - - - - -   #


async def main():
    set_logger()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.connect((SERVER_IP, SERVER_PORT))
    except ConnectionRefusedError:
        logging.error("Server is down.")
        exit(1)

    client = Client(network_manager=NetworkManager(server))

    try:
        # await client.download_file(local_file_path=Path("text.txt"), remote_file_path=Path("public/text.txt"))
        await client.download_file(local_file_path=Path("bens_music.mp3"), remote_file_path=Path("public/music.mp3"))
        # upload_tasks = [
        #     asyncio.create_task(client.upload_file(local_file_path=Path("text.txt"),
        #                                            remote_file_path=Path("public/text2.txt"))),
        #
        #     asyncio.create_task(client.upload_file(local_file_path=Path("text.txt"),
        #                                            remote_file_path=Path("public/text3.txt"))),
        # ]
        # await asyncio.gather(*upload_tasks)
        #
        # await client.delete_file(remote_file_path=Path("public/text3.txt"))

        await client.close_connection()
    except KeyboardInterrupt:
        pass
    server.close()


if __name__ == '__main__':

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.debug("The server has stopped due to a keyboard interrupt")
