import logging
from abc import ABC, abstractmethod

from interfaces import ClientMessage, IController


class State(ABC):
    def __init__(self, controller: IController):
        self.controller = controller

    @abstractmethod
    def parse(self, message: ClientMessage):
        ...

    @abstractmethod
    def get_possible_actions(self, on_turn: bool = True) -> set[str]:
        ...

    def _broadcast_changes(self):
        for record in self.controller.game_data.get_changes():
            self.controller.message.add(**record)
        self.controller.message.broadcast()

    def _change_state(self, state: "State"):
        game_data = self.controller.game_data
        on_turn = game_data.players.uuid_from_id(game_data.get_value(section="misc", item="on_turn"))
        for player in game_data.players:
            self.controller.game_data.update(
                section="players", item=player, attribute="possible_actions",
                value=state.get_possible_actions(player is on_turn)
            )
        self.controller.state = state
        logging.debug(f"Changed state to {state}.")
