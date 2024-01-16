from board_description import FieldType
from interfaces import ClientMessage
from state.buy_property import BuyPropertyState
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

    def _roll_dice(self) -> None:
        game_data = self.controller.game_data
        roll = self.controller.dice.roll()
        game_data.update(section="misc", item="last_roll", value=roll.get())
        if self.controller.dice.triple_double:
            new_field_id = game_data.fields.JAIL
        else:
            new_field_id = (game_data.get_value(
                section="players", item=game_data.on_turn_uuid, attribute="field"
            ) + roll.sum()) % 40
        game_data.update(
            section="players",
            item=game_data.on_turn_uuid,
            attribute="field",
            value=new_field_id
        )
        self._field_action(new_field_id)


    def _field_action(self, field_id):
        game_data = self.controller.game_data
        field = game_data.fields.get_field(field_id)
        match field.type:
            case FieldType.GO | FieldType.JUST_VISITING | FieldType.FREE_PARKING | FieldType.JAIL:
                self._end_turn()
            case FieldType.GO_TO_JAIL:
                game_data.update(
                    section="players",
                    item=game_data.on_turn_uuid,
                    attribute="field",
                    value=game_data.fields.JAIL
                )
                self._end_turn()
            case FieldType.RAILROAD | FieldType.UTILITY | FieldType.STREET:
                if field.owner:
                    self._pay_rent(field)
                else:
                    self._change_state(BuyPropertyState(self.controller))
            case FieldType.CC | FieldType.CHANCE:
                self._draw_card()

    def _end_turn(self):
        self._change_state(EndTurnState(self.controller))
        self._broadcast_changes()

    def _pay_rent(self, field):
        pass

    def _draw_card(self):
        pass