from interfaces import ClientMessage
from state.state import State


class EndTurnState(State):
    def get_possible_actions(self) -> set[str]:
        return {"end_turn"}

    def parse(self, message: ClientMessage):
        game_data = self.controller.game_data
        if message["action"] == "end_turn" and game_data.is_player_on_turn(message["my_uuid"]):
            from state.begin_turn import BeginTurnState
            game_data.update(section="misc", item="on_turn", value=next(game_data.player_order_cycler))
            self._change_state(BeginTurnState(self.controller))
