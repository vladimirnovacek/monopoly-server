from interfaces import ClientMessage
from state.state import State
from state.end_turn import EndTurnState


class BeginTurnState(State):
    def get_possible_actions(self, on_turn: bool = True) -> set[str]:
        if on_turn:
            return {"roll"}
        return set()

    def parse(self, message: ClientMessage):
        if message["action"] == "roll" and self.controller.game_data.is_player_on_turn(message["my_uuid"]):
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
            value=(game_data.get_value(section="players", item=on_turn_uuid, attribute="field") + roll.sum()) % 40
        )
        self._change_state(EndTurnState(self.controller))
        self._broadcast_changes()
