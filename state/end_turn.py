from interfaces import ClientMessage
from state.state import State


class EndTurnState(State):
    def get_possible_actions(self, on_turn: bool = True) -> set[str]:
        if on_turn:
            return {"end_turn"}
        return set()

    def parse(self, message: ClientMessage):
        # TODO: If player in jail, new state is supposed to be InJailState or something like that
        # TODO: If player in bankrupt, new state is supposed to be BankruptState or something like that
        game_data = self.controller.game_data
        if message["action"] == "end_turn" and game_data.is_player_on_turn(message["my_uuid"]):
            from state.begin_turn import BeginTurnState
            game_data.update(section="misc", item="on_turn", value=next(game_data.player_order_cycler))
            self.controller.dice.reset()
            self._change_state(BeginTurnState(self.controller))
            self._broadcast_changes()
