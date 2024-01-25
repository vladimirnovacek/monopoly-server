
import pickle
from typing import Self, TYPE_CHECKING, Any
from uuid import UUID

from interfaces import ClientMessage, Controller, IServer

if TYPE_CHECKING:
    from server import ServerFactory


class Messenger:
    """
    The messenger is responsible for sending and receiving data to and from the server. After creating the messenger, it
    is necessary to set the server using the set_server() method.
    """
    def __init__(self, controller: Controller):
        self.controller: Controller = controller
        """ The controller. """
        self.controller.message = self  # Due to cross-referencing cannot be set in controller's __init__.
        self.server: ServerFactory | None = None
        """ The server. Due to cross-referencing is initially None. Has to be set by the set_server() method. """
        self._messages = []
        self._private_messages = {}

    def set_server(self, server: IServer) -> None:
        """
        Sets the server.
        :param server: The server.
        :type server: ServerFactory
        """
        self.server = server
        self.controller.server_uuid = self.server.server_uuid

    def receive(self, message: ClientMessage | bytes) -> None:
        """
        Passes the message to the controller. If the message is a bytes object, it is deserialized first.
        :param message: The message to be parsed.
        :type message: dict | bytes
        :return: None
        :rtype: None
        """
        if type(message) == bytes:
            message = pickle.loads(message)
        self.controller.parse(message)

    def add(self, to: str | UUID = "all", **kwargs: Any) -> Self:
        """
        Adds the given message to the message queue.
        :param to: The UUID of the player or "all" for all players.
        :type to: UUID | str
        :param kwargs: Allowed keys are: section, item, attribute, value
        :type kwargs: Any
        :return: The current instance so that methods can be chained.
        :rtype: Self
        """
        if to == "all":
            self._messages.append(kwargs)
        else:
            if to not in self._private_messages:
                self._private_messages[to] = []
            self._private_messages[to].append(kwargs)
        return self

    def get(self, player_uuid: UUID) -> bytes:
        """
        Returns the current message queue ready to send. The private queue is emptied.
        :param player_uuid: The UUID of the player.
        :type player_uuid: UUID
        :return: The current message queue pickled.
        :rtype: bytes
        """
        messages = []
        if self._messages:
            messages.extend(self._messages)
        if player_uuid in self._private_messages:
            messages.extend(self._private_messages[player_uuid])
            self._private_messages[player_uuid].clear()
        return pickle.dumps(messages) if messages else b""

    def send(self, player_uuid: UUID, data: bytes | None = None) -> None:
        """
        Sends the given data to the given player. If no data is given, the current message queue is sent. The queue is
        emptied.
        :param player_uuid: The UUID of the player.
        :type player_uuid: UUID
        :param data: The data to be sent.
        :type data: bytes | None
        """
        if data is None:
            data = self.get(player_uuid)
        if data:
            self.server.send(player_uuid, data)

    def broadcast(self, data: bytes | None = None) -> None:
        """
        Sends the given data to all players. If no data is given, the current message queue is sent. The queue is
        emptied.
        :param data: The data to be sent.
        :type data: bytes | None
        """
        if data is None:
            for player_uuid in self.server.connected_clients:
                data = self.get(player_uuid)
                if data:
                    self.server.send(player_uuid, data)
            self._messages.clear()
        else:
            self.server.broadcast(data)
