
from board_description import FieldType
from interfaces import ClientMessage, IPlayer, IField, IController
from state.state import State
from state.end_turn import EndTurnState


class BeginTurnState(State):
    def __init__(self, controller: IController):
        super().__init__(controller)
        self.on_turn_player: IPlayer = self.controller.gd.on_turn_player

    @property
    def on_turn_player_field(self) -> IField:
        return self.controller.gd.fields.get_field(self.on_turn_player.field)

    def get_possible_actions(self, on_turn: bool = True) -> set[str]:
        if self.on_turn_player.in_jail:
            return self._get_possible_actions_in_jail()
        if on_turn:
            return {"roll"}
        return set()

    def parse(self, message: ClientMessage):
        if not self.controller.gd.is_player_on_turn(message["my_uuid"]):
            return  # The player is not on turn. TODO add possibilities of buying houses, mortgaging and trading.
        self._run_action_loop(message)

    def _run_action_loop(self, message: ClientMessage):
        if self.on_turn_player.in_jail:
            match message["action"]:
                case "roll":
                    self.stage = "roll_in_jail"
                case "payoff":
                    self.stage = "payout"
                case "use_card":
                    self.stage = "use_card"
        elif self.stage == "buying_decision":
            match message["action"]:
                case "buy":
                    self.stage = "buying_property"  # TODO
                case "auction":
                    self.stage = "auctioning"  # TODO
        else:
            self.stage = "rolling"
        self.input_expected = False
        while self.stage != "end_turn" or not self.input_expected:
            match self.stage:
                case "rolling":
                    self.stage = self._roll_dice()
                case "triple_double":
                    self.stage = self._go_to_jail()
                case "moving":
                    self.stage = self._move()
                case "on_property":
                    self.stage = self._on_property()
                case "pay_tax":
                    self.stage = self._pay_tax()
                case "pay_rent":
                    self.stage = self._pay_rent()
                case "unowned_property":
                    self.stage = self._unowned_property()
                case "go_to_jail":
                    self.stage = self._go_to_jail()
                case "roll_in_jail":
                    self.stage = self._roll_in_jail()
                case "leaving_jail":
                    self.stage = self._leave_jail()
                case "end_roll":
                    self.stage = self._end_roll()
        if self.stage == "end_turn":
            self._end_turn()

    def _roll_dice(self) -> str:
        self.controller.roll()
        if self.controller.dice.triple_double:
            return "triple_double"
        else:
            return "moving"

    def _go_to_jail(self) -> str:
        self.controller.move_to(self.controller.gd.fields.JAIL)
        return "end_turn"

    def _move(self) -> str:
        self.controller.move_by(self.controller.dice.last_roll.sum())
        match self.on_turn_player_field.type:
            case FieldType.GO | FieldType.JUST_VISITING | FieldType.FREE_PARKING:
                return "end_roll"
            case FieldType.STREET | FieldType.RAILROAD | FieldType.UTILITY:
                return "on_property"
            case FieldType.TAX:
                return "pay_tax"
            case FieldType.CC | FieldType.CHANCE:
                return "on_card"  # TODO
            case FieldType.GO_TO_JAIL:
                return "go_to_jail"

    def _pay_tax(self):
        self.controller.pay(self.on_turn_player_field.tax, self.on_turn_player.player_uuid)
        return "end_roll"

    def _on_property(self) -> str:
        if not self.on_turn_player_field.owner:
            return "unowned_property"
        elif self.on_turn_player_field.owner == self.on_turn_player.player_uuid:
            return "end_roll"
        else:
            return "pay_rent"

    def _unowned_property(self) -> str:
        self.input_expected = True
        return "buying_decision"

    def _pay_rent(self) -> str:
        rent = self.on_turn_player_field.rent
        if self.on_turn_player_field.type == FieldType.UTILITY:
            rent *= self.controller.dice.last_roll.sum()
        self.controller.pay(rent, self.on_turn_player.player_uuid, self.on_turn_player_field.owner)
        return "end_roll"

    def _roll_in_jail(self) -> str:
        roll = self.controller.dice.roll(False)
        if roll.is_double():
            return "leaving_jail"
        else:
            self.controller.gd.on_turn_player.jail_turns += 1
            return "end_turn"

    def _end_roll(self) -> str:
        if self.controller.dice.last_roll.is_double():
            return "rolling"
        else:
            return "end_turn"


    # def _field_action(self, field_id):
    #     game_data = self.controller.gd
    #     field = game_data.fields.get_field(field_id)
    #     match field.type:
    #         case FieldType.JAIL:
    #             logging.warning("This should never happen. Player is not supposed to get to jail by moving.")
    #         case FieldType.GO | FieldType.JUST_VISITING | FieldType.FREE_PARKING:
    #             self._actions_over()
    #         case FieldType.GO_TO_JAIL:
    #             self._move_to_jail()
    #         case FieldType.RAILROAD | FieldType.STREET:
    #             if field.owner:
    #                 self._pay_rent(field)
    #             else:
    #                 self._change_state(BuyPropertyState(self.controller))
    #         case FieldType.UTILITY:
    #             if field.owner:
    #                 self._pay_rent(field, multiplier=self.controller.dice.last_roll.sum())
    #             else:
    #                 self._change_state(BuyPropertyState(self.controller))
    #         case FieldType.CC | FieldType.CHANCE:
    #             self._draw_card()
    #         case FieldType.TAX:
    #             self._pay_tax(field)

    # def _pay_rent(self, field: IField, multiplier: int = 1):
    #     self.controller.pay(field.rent, self.on_turn_player.player_uuid, field.owner)
    #     self._actions_over()
    #
    # def _actions_over(self):
    #     if self.controller.dice.last_roll.is_double():
    #         self._change_state(BeginTurnState(self.controller))
    #     else:
    #         self._end_turn()

    def _leave_jail(self):
        self.on_turn_player.in_jail = False
        self.on_turn_player.jail_turns = 0
        self.controller.move_to(self.controller.gd.fields.JUST_VISITING)
        return "rolling"

    def _get_possible_actions_in_jail(self):
        actions = {"payoff"}
        if self.controller.gd.on_turn_player.get_out_of_jail_cards > 0:
            actions.add("use_card")
        if self.controller.gd.on_turn_player.jail_turns < 3:
            actions.add("roll")
        return actions
    #
    # def _draw_card(self):
    #     pass

    def _end_turn(self):
        self._change_state(EndTurnState(self.controller))
        self._broadcast_changes()