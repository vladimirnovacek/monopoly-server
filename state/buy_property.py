from interfaces import ClientMessage
from state.state import State


class BuyPropertyState(State):
    def get_possible_actions(self, on_turn: bool = True) -> set[str]:
        if on_turn:
            return {"buy"}
        return set()

    def parse(self, message: ClientMessage):
        pass