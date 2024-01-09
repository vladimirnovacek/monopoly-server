from abc import ABC, abstractmethod

from game_controller import GameController
from interfaces import ClientMessage


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

    def _change_state(self, state: "State"):
        self.controller.game_data.update(
            section="events", item="possible_actions", value=state.get_possible_actions()
        )
        self.controller.state = state
