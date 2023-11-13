
import pickle
from typing import Any, Callable, Literal, Optional, TypedDict

import uuid

from message_factory import MessageFactory
import server
from game_data import GameData


class ClientMessage(TypedDict):
    my_uuid: uuid.UUID
    action: str
    parameters: dict


class ServerMessage(TypedDict):
    section: Literal["fields", "players", "misc"]
    item: str | uuid.UUID
    attribute: Optional[str]
    value: Any


class MessageParser:
    def __init__(self, game_data: GameData, message_factory: MessageFactory):
        self.game_data: GameData = game_data
        self.message: MessageFactory = message_factory
        self.network: server.ServerFactory | None = None

    def get_initial_message(self, player_uuid: uuid.UUID) -> bytes:
        """
        Generates the initial message for the given player containing all necessary data from the game data.
        The message is already pickled and ready to be sent.
        :param player_uuid: The UUID of the player.
        :type player_uuid: uuid.UUID
        :return: The initial message as bytes.
        :rtype: bytes
        """
        for record in self.game_data.get_all_for_player(player_uuid):
            self.message.add(**record)
        return self.message.get()

    @staticmethod
    def retype(method: Callable) -> Callable:
        """
        A decorator that changes the return type of a method.
        :param method: The method to be decorated.
        :type method: typing.Callable
        :return: The decorated method.
        :rtype: typing.Callable
        """
        def wrapper(self, data):
            if type(data) == bytes:
                message = pickle.loads(data)
            else:
                message = data
            return method(self, message)
        return wrapper

    @retype
    def parse(self, message: ClientMessage | bytes) -> None:
        """
        Parses the given message and updates the game data.
        :param message: The message to be parsed.
        :type message: dict | bytes
        :return: None
        :rtype: None
        """
        if self.network.server_uuid == message["my_uuid"]:
            self._add_player(message["parameters"]["player_uuid"], message["parameters"]["player_id"])

    def _add_player(self, player_uuid: uuid.UUID, player_id: int):
        self.game_data.add_player(player_uuid, player_id)