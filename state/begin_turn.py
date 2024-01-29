import logging

from board_description import FieldType
from interfaces import ClientMessage, IPlayer, IField, IController
from state.buy_property import BuyPropertyState
from state.state import State
from state.end_turn import EndTurnState


class BeginTurnState(State):
    def __init__(self, controller: IController):
        super().__init__(controller)
        self.on_turn_player: IPlayer = self.controller.gd.on_turn_player

    def get_possible_actions(self, on_turn: bool = True) -> set[str]:
        if self.on_turn_player.in_jail:
            return self._get_possible_actions_in_jail()
        if on_turn:
            return {"roll"}
        return set()

    def parse(self, message: ClientMessage):
        if not self.controller.gd.is_player_on_turn(message["my_uuid"]):
            return  # The player is not on turn. TODO add possibilities of buying houses, mortgaging and trading.
        if message["action"] == "roll":
            self._roll_dice()
        if message["action"] == "payoff":
            pass
        if message["action"] == "use_card":
            pass

    def _roll_dice(self) -> None:
        if self.on_turn_player.in_jail:
            self._roll_in_jail()
            return
        game_data = self.controller.gd
        roll = self.controller.dice.roll()
        game_data.update(section="misc", item="last_roll", value=roll.get())
        if self.controller.dice.triple_double:
            self._move_to_jail()
        else:
            self._move()

    def _roll_in_jail(self):
        roll = self.controller.dice.roll(False)
        if roll.is_double():
            self.on_turn_player.in_jail = False
            self.on_turn_player.jail_turns = 0
            self.controller.move_to(self.controller.gd.fields.JUST_VISITING)
            self._change_state(BeginTurnState(self.controller))
        else:
            self.controller.gd.on_turn_player.jail_turns += 1
            self._end_turn()

    def _move_to_jail(self):
        self.controller.move_to(self.controller.gd.fields.JAIL)
        self._end_turn()

    def _move(self):
        self.controller.move_by(self.controller.dice.last_roll.sum())
        self._field_action(self.on_turn_player.field)

    def _field_action(self, field_id):
        game_data = self.controller.gd
        field = game_data.fields.get_field(field_id)
        match field.type:
            case FieldType.JAIL:
                logging.warning("This should never happen. Player is not supposed to get to jail by moving.")
            case FieldType.GO | FieldType.JUST_VISITING | FieldType.FREE_PARKING:
                self._actions_over()
            case FieldType.GO_TO_JAIL:
                self._move_to_jail()
            case FieldType.RAILROAD | FieldType.UTILITY | FieldType.STREET:
                if field.owner:
                    self._pay_rent(field)
                else:
                    self._change_state(BuyPropertyState(self.controller))
            case FieldType.CC | FieldType.CHANCE:
                self._draw_card()
            case FieldType.TAX:
                self._pay_tax(field)

    def _pay_rent(self, field: IField):
        self.controller.pay(field.rent, self.on_turn_player.player_uuid, field.owner)
        self._actions_over()

    def _actions_over(self):
        if self.controller.dice.last_roll.is_double():
            self._change_state(BeginTurnState(self.controller))
        else:
            self._end_turn()

    def _end_turn(self):
        self._change_state(EndTurnState(self.controller))
        self._broadcast_changes()

    def _pay_tax(self, field: IField):
        self.controller.pay(field.tax, self.on_turn_player.player_uuid)
        self._end_turn()

    def _draw_card(self):
        pass

    def _get_possible_actions_in_jail(self):
        actions = {"payoff"}
        if self.controller.gd.on_turn_player.get_out_of_jail_cards > 0:
            actions.add("use_card")
        if self.controller.gd.on_turn_player.jail_turns < 3:
            actions.add("roll")
        return actions