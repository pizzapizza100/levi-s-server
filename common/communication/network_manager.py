"""
Description: 
"""

#   - - - - - Imports - - - - -   #
import json
from json import JSONDecodeError
from types import SimpleNamespace

import PySimpleGUI
import asyncio
import socket
import logging

from common.communication.communication_exceptions import BadlyFormattedMessage
from common.communication.message import Message, MessageType


#   - - - - - Constants - - - - -   #


MAX_MESSAGE_METADATA_LENGTH = 256
METADATA_MINIMAL_LENGTH = 32
CHUNK_SIZE = (2 ** 20) * 10  # 10 MB
LARGE_FILE_CHUNK_THRESHOLD = 1_000
CHUNK_TO_PROGRESS_BAR_UPDATE = 100


#   - - - - - Classes - - - - -   #


class NetworkManager:
    METADATA_FORMAT = '"message_type": {message_type}, "length": {length}'

    def __init__(self, client_socket: socket.socket, callback_functions=None):
        self._socket = client_socket
        self._loop = asyncio.get_event_loop()
        self._progress_bar_window = None
        self._call_back_functions = callback_functions if callback_functions is not None else []

    def __del__(self):
        self._socket.close()
        if self._progress_bar_window is not None:
            self._progress_bar_window.close()

    async def close_connection(self):
        self._socket.close()

    async def send_message(self, message: Message):
        metadata = self.METADATA_FORMAT.format(message_type=message.message_type.value, length=message.length)
        data_frame = ("{" + f"{metadata}" + "}").encode("utf-8") + message.content
        chunked_data_frame = [data_frame[i:i + CHUNK_SIZE] for i in range(0, len(data_frame), CHUNK_SIZE)]

        logging.info(f"Sending... {len(data_frame)} bytes to {self._socket.getpeername()}")

        # using_progress_bar = message.length > LARGE_FILE_CHUNK_THRESHOLD * CHUNK_SIZE and self._using_gui
        for index, data_chunk in enumerate(chunked_data_frame):
            await self._loop.sock_sendall(self._socket, data_chunk)

            # if using_progress_bar and index % CHUNK_TO_PROGRESS_BAR_UPDATE == 0:
            #     await self._update_progress_bar_window(total=message.length, index=index * CHUNK_SIZE, is_reading=False)

        logging.info(f"Done sending {len(data_frame)} to {self._socket.getpeername()}")

    async def receive_message(self) -> Message:
        raw_metadata = (await self._loop.sock_recv(self._socket, METADATA_MINIMAL_LENGTH)).decode("utf-8")
        while not len(raw_metadata) > MAX_MESSAGE_METADATA_LENGTH:
            try:
                metadata = json.loads(raw_metadata, object_hook=lambda d: SimpleNamespace(**d))
                break
            except JSONDecodeError:
                raw_metadata += (await self._loop.sock_recv(self._socket, 1)).decode("utf-8")
                if len(raw_metadata) > MAX_MESSAGE_METADATA_LENGTH:
                    raise BadlyFormattedMessage()

        logging.info(f"Got new message from {self._socket.getpeername()} "
                     f"reading message data ( size : {metadata.length} bytes )")

        data = bytearray()

        # using_progress_bar = metadata.length > LARGE_FILE_CHUNK_THRESHOLD * CHUNK_SIZE and self._using_gui
        # chunk_counter = 0

        while len(data) != metadata.length:
            total_data_left = metadata.length - len(data)
            next_chunk = CHUNK_SIZE if total_data_left > CHUNK_SIZE else total_data_left
            data.extend((await self._loop.sock_recv(self._socket, next_chunk)))
            # chunk_counter += 1
            # if using_progress_bar and chunk_counter % CHUNK_TO_PROGRESS_BAR_UPDATE == 0:
            #     await self._update_progress_bar_window(total=metadata.length, index=len(data), is_reading=True)

        # if using_progress_bar:
        #     await self._update_progress_bar_window(total=metadata.length, index=metadata.length, is_reading=True)

        if len(data) == metadata.length:
            logging.info(f"Done reading {self._socket.getpeername()}'s message's data, {len(data)} bytes.")
        else:
            logging.warning(f"Did not read all data! {len(data)} / {metadata.length} bytes,"
                            f" {len(data) != metadata.length}%.")
            raise ConnectionResetError()

        return Message(message_type=MessageType(metadata.message_type), content=data)

    async def _create_progress_bar_window(self):
        self._progress_bar_window = PySimpleGUI.Window('Progress Bar', layout=[
            [PySimpleGUI.ProgressBar(100, orientation='h', expand_x=True, size=(20, 20), key='-PBAR-')], [
                PySimpleGUI.Text('', key='-OUT-', enable_events=True, font=('Arial Bold', 16), justification='center',
                                 expand_x=True)]], size=(715, 150), finalize=True, keep_on_top=True)

        screen_width, screen_height = self._progress_bar_window.get_screen_dimensions()
        win_width, win_height = self._progress_bar_window.size
        self._progress_bar_window.move(screen_width - win_width, win_height)

    async def _update_progress_bar_window(self, total: int, index: int, is_reading: bool):
        present = round(100 * index / total, 3)

        print(present)
        if self._progress_bar_window is None:
            await self._create_progress_bar_window()

        if self._progress_bar_window.read(timeout=0)[0] in [PySimpleGUI.WIN_CLOSED, 'Exit']:
            self._progress_bar_window.close()
            self._progress_bar_window = None

        self._progress_bar_window['-PBAR-'].update(current_count=present + 1)
        self._progress_bar_window['-OUT-'].update(f"{'Read' if is_reading else 'Sent'}"
                                                  f" {present}% ({index // CHUNK_SIZE}/{total // CHUNK_SIZE} MB) of the file to {self._socket.getpeername()}")

        if total == index:
            self._progress_bar_window.close()
            self._progress_bar_window = None
        else:
            await asyncio.sleep(0.1)

#   - - - - - Functions - - - - -   #
