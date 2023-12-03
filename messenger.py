
import pickle
from typing import  Self, TYPE_CHECKING

from uuid import UUID

from game_controller import GameController
from interfaces import ClientMessage
if TYPE_CHECKING:
    from server import ServerFactory


class Messenger:
    def __init__(self, controller: GameController):
        self.controller: GameController = controller
        self.controller.message = self
        self.server: ServerFactory | None = None
        self.messages = []

    def set_server(self, server: "ServerFactory") -> None:
        self.server = server
        self.controller.server_uuid = self.server.server_uuid

    def receive(self, message: ClientMessage | bytes) -> None:
        """ TODO update docstring
        Parses the given message and updates the game data.
        :param message: The message to be parsed.
        :type message: dict | bytes
        :return: None
        :rtype: None
        """
        if type(message) == bytes:
            message = pickle.loads(message)
        self.controller.parse(message)

    def add(self, **kwargs) -> Self:
        self.messages.append(kwargs)
        return self

    def get(self) -> bytes:
        data = pickle.dumps(self.messages)
        self.messages.clear()
        return data

    def send(self, uuid: UUID, data: bytes | None = None) -> None:
        if data is None:
            data = self.get()
        self.server.send(uuid, data)

    def broadcast(self, data: bytes | None = None) -> None:
        if data is None:
            data = self.get()
        self.server.broadcast(data)