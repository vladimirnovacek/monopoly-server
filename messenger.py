import logging
import pickle
from typing import Self, TYPE_CHECKING, Any
from uuid import UUID

from interfaces import ClientMessage, IController, IServer, IMessenger

if TYPE_CHECKING:
    from server import ServerFactory


class Messenger(IMessenger):
    """
    The messenger is responsible for sending and receiving data to and from the server. After creating the messenger, it
    is necessary to set the server using the set_server() method.
    """
    def __init__(self):
        self.controller: IController | None = None
        """ The controller. """
        self.server: ServerFactory | None = None
        """ The server. Due to cross-referencing is initially None. Has to be set by the set_server() method. """
        self._messages = []
        self._private_messages = {}

    def set_server(self, server: IServer) -> None:
        """
        Sets the server. Sets also the server_uuid in the controller.
        :param server: The server.
        :type server: ServerFactory
        """
        self.server = server
        self.controller.server_uuid = self.server.server_uuid

    def receive(self, message: ClientMessage) -> None:
        """
        Passes the message to the controller. If the message is a bytes object, it is deserialized first.
        :param message: The message to be parsed.
        :type message: dict | bytes
        :return: None
        :rtype: None
        """
        if message:
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
        kwargs = {k: v for k, v in kwargs.items() if k in {"section", "item", "attribute", "value"}}
        if "attribute" in kwargs and kwargs["attribute"] is None:
            del kwargs["attribute"]
        if to == "all":
            self._messages.append(kwargs)
        else:
            if to not in self._private_messages:
                self._private_messages[to] = []
            self._private_messages[to].append(kwargs)
        return self

    def get(self, player_uuid: UUID) -> list:
        """
        Returns the current message queue ready to send. The private queue is emptied.
        :param player_uuid: The UUID of the player.
        :type player_uuid: UUID
        :return: The current message queue.
        :rtype: bytes
        """
        messages = []
        if self._messages:
            messages.extend(self._messages)
        if player_uuid in self._private_messages:
            messages.extend(self._private_messages[player_uuid])
            del self._private_messages[player_uuid]
        return messages

    def send(self, player_uuid: UUID, message: Any | None = None) -> None:
        """
        Sends the given data to the given player. If no data is given, the current message queue is sent. The queue is
        emptied.
        :param player_uuid: The UUID of the player.
        :type player_uuid: UUID
        :param message: The data to be sent.
        :type message: bytes | None
        """
        if message is None:
            message = self.get(player_uuid)
        if message:
            logging.debug(f"Sending to {player_uuid}: {message}")
            self.server.send(player_uuid, message)

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
                    self.send(player_uuid, data)
            self._messages.clear()
        else:
            logging.debug(f"Broadcasting: {pickle.loads(data)}")
            self.server.broadcast(data)

    def is_messages_pending(self) -> bool:
        return bool(self._messages or self._private_messages)