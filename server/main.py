"""
Description: The main file_handling
"""

#   - - - - - Imports - - - - -   #
import logging
import os
import socket
from pathlib import Path

import asyncio

from common.set_loggin import set_logger
from server.client_handler import ClientHandler
from server.database.json_database_handler import JSONDataBaseManager

#   - - - - - Constants - - - - -   #

SERVER_PORT = 16239
MAX_CONNECTION_QUEUE = 3
CLIENT_TIMEOUT = 10
DATA_BASE_PATH = Path(os.getcwd() + r"/database/database_files/json_DB.json")


#   - - - - - Functions - - - - -   #
async def create_main_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((socket.gethostbyname(socket.gethostname()), SERVER_PORT))
    server_socket.listen(MAX_CONNECTION_QUEUE)
    return server_socket


async def run_server():
    set_logger()

    database_manager = JSONDataBaseManager(DATA_BASE_PATH)
    await database_manager.create(create_if_missing=True)
    await database_manager.load()

    server_socket = await create_main_socket()
    logging.info("Server is up and listening.")

    loop = asyncio.get_event_loop()

    condition = True
    while condition:
        client_socket, address = await loop.sock_accept(server_socket)
        logging.info(f"{address} has connected.")
        client_handler = ClientHandler(client_socket, database_manager)
        loop.create_task(client_handler.handle_client())

    await database_manager.save()


if __name__ == '__main__':

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logging.debug("The server has stopped due to a keyboard interrupt")
