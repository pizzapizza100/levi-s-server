"""
Description: The main file_handling
"""

#   - - - - - Imports - - - - -   #
import logging
import os
import socket
from pathlib import Path

import asyncio
from colorlog import ColoredFormatter

from server.client_handler import ClientHandler
from server.database.json_database_handler import JSONDataBaseManager

#   - - - - - Constants - - - - -   #

SERVER_IP = "127.0.0.1"
SERVER_PORT = 16239
MAX_CONNECTION_QUEUE = 3
CLIENT_TIMEOUT = 10
DATA_BASE_PATH = Path(os.getcwd() + r"/database/database_files/json_DB.json")


#   - - - - - Functions - - - - -   #

def set_logger():
    log_level = logging.DEBUG
    log_format = "%(log_color)s%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s%(reset)s"
    logging.root.setLevel(log_level)
    stream = logging.StreamHandler()
    stream.setLevel(log_level)
    stream.setFormatter(ColoredFormatter(log_format))
    logging.basicConfig(handlers=[stream], format=log_format)


async def run_server():
    set_logger()

    database_manager = await JSONDataBaseManager(DATA_BASE_PATH).create(create_if_missing=True)
    await database_manager.load()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_IP, SERVER_PORT))
    server.listen(MAX_CONNECTION_QUEUE)
    logging.info("Server is up and listening.")

    loop = asyncio.get_event_loop()

    condition = True
    while condition:
        client_socket, address = await loop.sock_accept(server)
        client_socket.settimeout(CLIENT_TIMEOUT)
        logging.info(f"{address} has connected.")
        client_handler = ClientHandler(client_socket, database_manager)
        loop.create_task(client_handler.handle_client())

    await database_manager.save()


if __name__ == '__main__':

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logging.debug("The server has stopped due to a keyboard interrupt")
