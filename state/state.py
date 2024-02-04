import logging
from abc import ABC, abstractmethod

from interfaces import ClientMessage, IController, IPlayer


class State(ABC):
    def __init__(self, controller: IController):
        self.controller = controller
        self.stage: str = "pre_game"
        self.input_expected: bool = False

    @abstractmethod
    def parse(self, message: ClientMessage):
        ...

    @abstractmethod
    def get_possible_actions(self, player: IPlayer) -> set[str]:
        ...

    def _broadcast_changes(self):
        for record in self.controller.gd.get_changes():
            self.controller.message.add(**record)
        self.controller.message.broadcast()

    def _change_state(self, state: "State"):
        game_data = self.controller.gd
        on_turn = game_data.players.uuid_from_id(game_data.get_value(section="misc", item="on_turn"))
        for player in game_data.players:
            self.controller.gd.update(
                section="players", item=player, attribute="possible_actions",
                value=state.get_possible_actions(game_data.players[player])
            )
        self.controller.state = state
        logging.debug(f"Changed state to {state}.")
