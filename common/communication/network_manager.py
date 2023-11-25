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

MAX_MESSAGE_METADATA_LENGTH = 4096
METADATA_MINIMAL_LENGTH = 32
CHUNK_SIZE = 1_048_576 * 10  # 10MB
LARGE_FILE_CHUNK_THRESHOLD = 20


#   - - - - - Classes - - - - -   #


class NetworkManager:
    IS_USING_CHUNKING = True
    IS_USING_PROGRESS_BAR = False
    METADATA_FORMAT = '"message_type": {message_type}, "length": {length}'

    def __init__(self, client_socket: socket.socket):
        self._socket = client_socket
        self._loop = asyncio.get_event_loop()
        self._progress_bar_window = None

    def __del__(self):
        if self._progress_bar_window is not None:
            self._progress_bar_window.close()

    async def send_message(self, message: Message):
        metadata = self.METADATA_FORMAT.format(message_type=message.message_type.value, length=message.length)
        data_frame = ("{" + f"{metadata}" + "}").encode("utf-8") + message.content
        logging.info(f"Sending... {len(data_frame)} bytes to {self._socket.getpeername()}")

        if not self.IS_USING_CHUNKING:
            await self._loop.sock_sendall(self._socket, data_frame)
        else:
            chunked_data_frame = [data_frame[i:i + CHUNK_SIZE] for i in range(0, len(data_frame), CHUNK_SIZE)]

            using_progress_bar = False
            if len(chunked_data_frame) > LARGE_FILE_CHUNK_THRESHOLD and self.IS_USING_PROGRESS_BAR:
                using_progress_bar = True
                await self._create_progress_bar_window()

            for index, data_chunk in enumerate(chunked_data_frame):
                await self._loop.sock_sendall(self._socket, data_chunk)

                if using_progress_bar:
                    # logging.debug(f"Sending data... {present}%")
                    present = round(100 * index / len(chunked_data_frame), 3)
                    await self._update_progress_bar_window(present, is_reading=False)

            if using_progress_bar:
                self._progress_bar_window.close()
                self._progress_bar_window = None

        logging.info(f"Done sending {len(data_frame)} to {self._socket.getpeername()}")

    async def receive_message(self) -> Message:
        raw_metadata = (await self._loop.sock_recv(self._socket, METADATA_MINIMAL_LENGTH))
        print(raw_metadata)
        raw_metadata = raw_metadata.decode("utf-8")
        while True:
            try:
                metadata = json.loads(raw_metadata, object_hook=lambda d: SimpleNamespace(**d))
                break
            except JSONDecodeError:
                raw_metadata += (await self._loop.sock_recv(self._socket, 1)).decode("utf-8")

        try:
            logging.info(f"Got new message from {self._socket.getpeername()},"
                         f" reading message data ( size : {metadata.length} bytes )")

            data = bytearray()

            if self.IS_USING_CHUNKING:
                using_progress_bar = False
                if metadata.length > LARGE_FILE_CHUNK_THRESHOLD * CHUNK_SIZE and self.IS_USING_PROGRESS_BAR:
                    using_progress_bar = True
                    await self._create_progress_bar_window()

                while len(data) != metadata.length:
                    # logging.debug(f"Reading data... {100 * len(data) / metadata.length}%")
                    data.extend((await self._loop.sock_recv(self._socket, CHUNK_SIZE)))

                    if using_progress_bar:
                        await self._update_progress_bar_window(100 * len(data) / metadata.length, is_reading=True)

                if using_progress_bar:
                    self._progress_bar_window.close()
            else:
                data = (await self._loop.sock_recv(self._socket, metadata.length))

            if len(data) == metadata.length:
                logging.info(f"Done reading {self._socket.getpeername()}'s message's data, {len(data)} bytes.")
            else:
                logging.warning(f"Did not read all data! {len(data)} / {metadata.length} bytes,"
                                f" {len(data) != metadata.length}%.")
                raise ConnectionResetError()

            return Message(message_type=MessageType(metadata.message_type), content=data)
        except AttributeError:
            logging.warning(f"Got a message with a wrong format from {self._socket.getpeername()}")
            raise BadlyFormattedMessage()

    async def _create_progress_bar_window(self):
        self._progress_bar_window = PySimpleGUI.Window('Progress Bar', layout=[
            [PySimpleGUI.ProgressBar(100, orientation='h', expand_x=True, size=(20, 20), key='-PBAR-')], [
                PySimpleGUI.Text('', key='-OUT-', enable_events=True, font=('Arial Bold', 16), justification='center',
                                 expand_x=True)]], size=(715, 150), finalize=True,keep_on_top=True)

        screen_width, screen_height = self._progress_bar_window.get_screen_dimensions()
        win_width, win_height = self._progress_bar_window.size
        self._progress_bar_window.move(screen_width - win_width, win_height)

    async def _update_progress_bar_window(self, present: float, is_reading: bool):
        if self._progress_bar_window.read(timeout=0)[0] in [PySimpleGUI.WIN_CLOSED, 'Exit']:
            raise Exception()

        self._progress_bar_window['-PBAR-'].update(current_count=present + 1)
        self._progress_bar_window['-OUT-'].update(f"{'Read' if is_reading else 'Sent'}"
                                                  f" {present}% of the file to {self._socket.getpeername()}")
        await asyncio.sleep(0)

#   - - - - - Functions - - - - -   #
