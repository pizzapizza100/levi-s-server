"""
Description:
"""

#   - - - - - Imports - - - - -   #

import socket
import os
from pathlib import Path

import aiofiles
import asyncio

#   - - - - - Constants - - - - -   #
import logging

from colorlog import ColoredFormatter

from common.communication.message import Message, MessageType
from common.communication.network_manager import NetworkManager

SERVER_IP = "127.0.0.1"
SERVER_PORT = 16239


#   - - - - - Functions - - - - -   #
async def download_file(network_manager: NetworkManager, file_name: str):
    logging.info(f"Requesting {file_name}.")
    message = Message(message_type=MessageType.DOWNLOAD_FILE, content=file_name.encode("utf-8"))
    await network_manager.send_message(message)
    response = await network_manager.receive_message()

    logging.info(f"Writing file...")
    async with aiofiles.open(Path(os.getcwd()) / Path(file_name).name, "wb") as downloaded_file:
        await downloaded_file.write(response.content)
    logging.info(f"Done writing file.")


async def main():
    set_logger()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.connect((SERVER_IP, SERVER_PORT))
    except ConnectionRefusedError:
        logging.error("Server is down.")

    network_manager = NetworkManager(server)
    try:
        await download_file(network_manager, "public/text.txt")
        await asyncio.sleep(0.5)
        await download_file(network_manager, "public/music.mp3")
        await asyncio.sleep(0.5)
        await download_file(network_manager, "public/pic.png")
        await asyncio.sleep(0.5)
        await download_file(network_manager, "public/movie.mp4")

    except KeyboardInterrupt:
        pass
    server.close()

def set_logger():
    log_level = logging.DEBUG
    log_format = "%(log_color)s%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s%(reset)s"
    logging.root.setLevel(log_level)
    stream = logging.StreamHandler()
    stream.setLevel(log_level)
    stream.setFormatter(ColoredFormatter(log_format))
    logging.basicConfig(handlers=[stream], format=log_format)

if __name__ == '__main__':

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.debug("The server has stopped due to a keyboard interrupt")

