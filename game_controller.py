import logging
import typing
import uuid

import game_data
from interfaces import ClientMessage
from states import PreGameState, State

if typing.TYPE_CHECKING:
    from messenger import Messenger


class GameController:
    def __init__(self, data: game_data.GameData):
        self.game_data: game_data.GameData = data
        self.message: Messenger | None = None
        self.server_uuid: uuid.UUID | None = None
        self.state: State = PreGameState(self)

    def parse(self, message: ClientMessage) -> None:
        self.state.parse(message)

    def send_initial_message(self, player_uuid: uuid.UUID) -> None:
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
        self.message.send(player_uuid)

    def _broadcast_changes(self):
        for record in self.game_data.get_changes():
            self.message.add(**record)
        self.message.broadcast()

    def _add_player(self, message: ClientMessage) -> None:
        if message["my_uuid"] != self.server_uuid:
            return
        parameters = message["parameters"]
        self.game_data.add_player(parameters["player_uuid"], parameters["player_id"])
        self.send_initial_message(parameters["player_uuid"])
        self._broadcast_changes()

    def _update_user(self, message: ClientMessage):
        player = self.game_data["players"][message["my_uuid"]]
        if player["player_id"] != message["parameters"]["item"]:
            logging.warning(f"Player {message['my_uuid']} is trying to change other player's credentials.")
            return
        message["parameters"]["item"] = message["my_uuid"]
        self.game_data.update(**message["parameters"])
        self._broadcast_changes()
