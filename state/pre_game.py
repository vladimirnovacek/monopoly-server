import logging
import random
from itertools import cycle
from uuid import UUID

from interfaces import ClientMessage
from state.state import State
from state.begin_turn import BeginTurnState


class PreGameState(State):
    def get_possible_actions(self, on_turn: bool = True) -> set[str]:
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
        The message is then sent.
        :param player_uuid: The UUID of the player.
        :type player_uuid: uuid.UUID
        :return: The initial message as bytes.
        :rtype: bytes
        """
        for record in self.controller.gd.get_all_for_player(player_uuid):
            self.controller.message.add(to=player_uuid, **record)
        (self.controller.message
            .add(to=player_uuid, section="events", item="possible_actions", value=self.get_possible_actions())
            .send(player_uuid))

    def _add_player(self, message: ClientMessage) -> None:
        if message["my_uuid"] != self.controller.server_uuid:
            ''' The server should only be able to add other players. '''
            logging.warning(f"Player {message['my_uuid']} is trying to add other player.")
            return
        parameters = message["parameters"]
        self.controller.gd.players.add(parameters["player_uuid"], parameters["player_id"])
        self._send_initial_message(parameters["player_uuid"])
        self._broadcast_changes()
        logging.info(f"Player {parameters['player_uuid']} added.")

    def _update_user(self, message: ClientMessage):
        player = self.controller.gd["players"][message["my_uuid"]]
        if player["player_id"] != message["parameters"]["item"]:
            logging.warning(f"Player {message['my_uuid']} is trying to change other player's credentials.")
            return
        message["parameters"]["item"] = message["my_uuid"]
        self.controller.gd.update(**message["parameters"])
        self._broadcast_changes()

    def _start_game(self):
        game_data = self.controller.gd
        if not game_data.players.is_all_ready():
            logging.warning("Not all players are ready.")
            return
        if len(game_data.players) < 2:
            logging.warning("Not enough players.")
            return
        game_data.update(section="misc", item="state", value="begin_turn")
        game_data.set_initial_values()
        player_order = list(range(len(game_data.players)))
        random.shuffle(player_order)
        game_data.update(section="misc", item="player_order", value=player_order)
        game_data.player_order_cycler = cycle(player_order)
        game_data.update(section="misc", item="on_turn", value=next(game_data.player_order_cycler))
        game_data.update(section="events", item="game_started", value=True)
        self.controller.message.server.locked = True
        self._change_state(BeginTurnState(self.controller))
        self._broadcast_changes()
        logging.info("Game started.")
