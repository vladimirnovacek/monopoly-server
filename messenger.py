
import pickle
from typing import Self, TYPE_CHECKING, Any
from uuid import UUID

from game_controller import GameController
from interfaces import ClientMessage

if TYPE_CHECKING:
    from server import ServerFactory


class Messenger:
    """
    The messenger is responsible for sending and receiving data to and from the server. After creating the messenger, it
    is necessary to set the server using the set_server() method.
    """
    def __init__(self, controller: GameController):
        self.controller: GameController = controller
        """ The controller. """
        self.controller.message = self  # Due to cross-referencing cannot be set in controller's __init__.
        self.server: ServerFactory | None = None
        """ The server. Due to cross-referencing is initially None. Has to be set by the set_server() method. """
        self._messages = []
        self._private_messages = {}

    def set_server(self, server: "ServerFactory") -> None:
        """
        Sets the server.
        :param server: The server.
        :type server: ServerFactory
        """
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

    def get(self, player: UUID | None = None) -> bytes:
        """
        Returns the current message queue ready to send. The queue is emptied.
        :return: The current message queue pickled.
        :rtype: bytes
        """
        messages = []
        if self._messages:
            messages.extend(self._messages)
        if player is not None and player in self._private_messages:
            messages.extend(self._private_messages[player])
            self._private_messages[player].clear()
        return pickle.dumps(messages) if messages else b""

    def send(self, uuid: UUID, data: bytes | None = None) -> None:
        """
        Sends the given data to the given player. If no data is given, the current message queue is sent. The queue is
        emptied.
        :param uuid: The UUID of the player.
        :type uuid: UUID
        :param data: The data to be sent.
        :type data: bytes | None
        """
        if data is None:  # Nothing was given by parameter
            data = self.get(uuid)
            if data is None:  # There is nothing to send at all
                return
        self.server.send(uuid, data)

    def broadcast(self, data: bytes | None = None) -> None:
        """
        Sends the given data to all players. If no data is given, the current message queue is sent. The queue is
        emptied.
        :param data: The data to be sent.
        :type data: bytes | None
        """
        if data is None:
            for player in self.server.connected_clients:
                data = self.get(player)
                if data is not None:
                    self.server.send(player, data)
            self._messages.clear()
        else:
            self.server.broadcast(data)
