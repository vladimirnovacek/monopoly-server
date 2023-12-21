import logging
import random
import typing
from abc import ABC, abstractmethod
from itertools import cycle

from uuid import UUID

from interfaces import ClientMessage

if typing.TYPE_CHECKING:
    from game_controller import GameController


class State(ABC):
    def __init__(self, controller: "GameController"):
        self.controller = controller

    @abstractmethod
    def parse(self, message: ClientMessage):
        ...

    @abstractmethod
    def get_possible_actions(self) -> set[str]:
        ...

    def _broadcast_changes(self):
        for record in self.controller.game_data.get_changes():
            self.controller.message.add(**record)
        self.controller.message.broadcast()


class PreGameState(State):
    def get_possible_actions(self) -> set[str]:
        return {"add_player", "user_info", "start_game"}

    def parse(self, message: ClientMessage):
        if message["action"] == "add_player":
            self._add_player(message)
        elif message["action"] == "user_info":
            self._update_user(message)
        elif message["action"] == "start_game":
            self._start_game()

    def _send_initial_message(self, player_uuid: UUID) -> None:
        """
        Generates the initial message for the given player containing all necessary data from the game data.
        The message is already pickled and ready to be sent.
        :param player_uuid: The UUID of the player.
        :type player_uuid: uuid.UUID
        :return: The initial message as bytes.
        :rtype: bytes
        """
        for record in self.controller.game_data.get_all_for_player(player_uuid):
            self.controller.message.add(**record)
        self.controller.message.send(player_uuid)

    def _add_player(self, message: ClientMessage) -> None:
        if message["my_uuid"] != self.controller.server_uuid:
            return
        parameters = message["parameters"]
        self.controller.game_data.add_player(parameters["player_uuid"], parameters["player_id"])
        self._send_initial_message(parameters["player_uuid"])
        self._broadcast_changes()

    def _update_user(self, message: ClientMessage):
        player = self.controller.game_data["players"][message["my_uuid"]]
        if player["player_id"] != message["parameters"]["item"]:
            logging.warning(f"Player {message['my_uuid']} is trying to change other player's credentials.")
            return
        message["parameters"]["item"] = message["my_uuid"]
        self.controller.game_data.update(**message["parameters"])
        self._broadcast_changes()

    def _start_game(self):
        game_data = self.controller.game_data
        if not game_data.is_all_players_ready():
            return
        if len(game_data.players) < 2:
            return
        game_data.update(section="misc", item="state", value="begin_turn")
        game_data.set_initial_values()
        player_order = list(range(len(game_data.players)))
        random.shuffle(player_order)
        game_data.update(section="misc", item="player_order", value=player_order)
        game_data.player_order_cycler = cycle(player_order)
        game_data.update(section="misc", item="on_turn", value=next(game_data.player_order_cycler))
        self._broadcast_changes()
        self.controller.state = BeginTurnState(self.controller)


class BeginTurnState(State):
    def get_possible_actions(self) -> set[str]:
        return {"roll_dice"}

    def parse(self, message: ClientMessage):
        if message["action"] == "roll_dice":
            self._roll_dice()

    def _roll_dice(self):
        game_data = self.controller.game_data
        on_turn_uuid = game_data.uuid_from_id(game_data["misc"]["on_turn"])
        roll = self.controller.dice.roll()
        game_data.update(section="misc", item="last_roll", value=roll.get())
        game_data.update(
            section="players",
            item=on_turn_uuid,
            attribute="field",
            value=game_data.get_value(section="players", item=on_turn_uuid, attribute="field") + roll.sum()
        )
        self._broadcast_changes()
