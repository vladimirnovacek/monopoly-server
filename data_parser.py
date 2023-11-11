
import pickle
from typing import Callable

import uuid

from message_factory import MessageFactory
import server
from game_data import GameData


class MessageParser:
    def __init__(self, game_data: GameData, message_factory: MessageFactory):
        self.game_data: GameData = game_data
        self.message: MessageFactory = message_factory
        self.network: server.Server | None = None

    def get_initial_message(self, player_uuid: uuid.UUID) -> bytes:
        """
        Generates the initial message for the given player containing all necessary data from the game data.
        The message is already pickled and ready to be sent.

        Args:
            player_uuid (uuid.UUID): The UUID of the player.

        Returns:
            bytes: The initial message as bytes.
        """
        for record in self.game_data.get_all_for_player(player_uuid):
            self.message.add(**record)
        return self.message.get()

    @staticmethod
    def retype(method: Callable) -> Callable:
        """
        A decorator that changes the input type of a method.

        Parameters:
            method (Callable): The method to be decorated.

        Returns:
            Callable: The decorated method.
        """
        def wrapper(self, data):
            if type(data) == bytes:
                message = pickle.loads(data)
            else:
                message = data
            return method(self, message)
        return wrapper

    @retype
    def parse(self, message):
        """
        Parses the given message and updates the game data.
        :param message:
        :return:
        """
        if message["action"] == "add_player":
            self._add_player(message["my_uuid"], message["parameters"]["my_id"])

    def _add_player(self, player_uuid: uuid.UUID, player_id: int):
        self.game_data.add_player(player_uuid, player_id)