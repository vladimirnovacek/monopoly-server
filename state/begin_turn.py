
from board_description import FieldType
from interfaces import ClientMessage, IPlayer, IField, IController, IRoll
from state.state import State
from state.end_turn import EndTurnState


class BeginTurnState(State):
    def __init__(self, controller: IController):
        super().__init__(controller)
        self.on_turn_player: IPlayer = self.controller.gd.on_turn_player
        self.extra_roll: IRoll | None = None
        self.stage = "begin_turn"
        self.input_expected = True

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
        match message["action"]:
            case "roll":
                if self.stage == "rent_roll":
                    self.stage = "rent_rolling"
                elif self.on_turn_player.in_jail:
                    self.stage = "roll_in_jail"
                else:
                    self.stage = "rolling"
            case "payout":
                self.stage = "payout"
            case "use_card":
                self.stage = "use_card"
            case "buy":
                self.stage = "buying_property"
            case "auction":
                self.stage = "auctioning"
            case "rent_roll":
                self.stage = "rent_roll"
            case "buy":
                self.stage = "buying_property"
            case "auction":
                self.stage = "auctioning"
        if not self.controller.gd.is_player_on_turn(message["my_uuid"]):
            return  # The player is not on turn.
            # TODO add possibilities of buying houses, mortgaging and trading.
        self.input_expected = False
        self._run_action_loop(message)

    def _run_action_loop(self, message: ClientMessage):
        while self.stage != "end_turn" or not self.input_expected:
            match self.stage:
                case "auctioning":
                    self.stage = "end_roll"  # TODO
                case "buying_property":
                    self.stage = self._buy_property()
                case "end_roll":
                    self.stage = self._end_roll()
                case "go_to_jail":
                    self.stage = self._go_to_jail()
                case "leaving_jail":
                    self.stage = self._leave_jail()
                case "moved":
                    self.stage = self._moved()
                case "moving":
                    self.stage = self._move()
                case "on_card":
                    self.stage = self._take_card()
                case "on_property":
                    self.stage = self._on_property()
                case "pay_rent":
                    self.stage = self._pay_rent()
                case "pay_tax":
                    self.stage = self._pay_tax()
                case "rent_rolling":
                    self.stage = self._rent_roll()
                case "roll_in_jail":
                    self.stage = self._roll_in_jail()
                case "rolling":
                    self.stage = self._roll_dice()
                case "unowned_property":
                    self.stage = self._unowned_property()
                case "triple_double":
                    self.stage = self._go_to_jail()
        if self.stage == "end_turn":
            self._end_turn()

    def _buy_property(self) -> str:
        self.controller.pay(self.on_turn_player_field.price, self.on_turn_player.uuid)
        self.on_turn_player_field.owner = self.on_turn_player.uuid
        return "end_roll"

    def _end_roll(self) -> str:
        if self.controller.dice.last_roll.is_double():
            self.input_expected = True
            return "begin_turn"
        else:
            return "end_turn"

    def _go_to_jail(self) -> str:
        self.controller.move_to(self.controller.gd.fields.JAIL)
        return "end_turn"

    def _leave_jail(self):
        self.on_turn_player.in_jail = False
        self.on_turn_player.jail_turns = 0
        self.controller.move_to(self.controller.gd.fields.JUST_VISITING)
        self.input_expected = True
        return "begin_turn"

    def _move(self) -> str:
        self.controller.move_by(self.controller.dice.last_roll.sum())
        return "moved"

    def _moved(self) -> str:
        match self.on_turn_player_field.type:
            case FieldType.GO | FieldType.JUST_VISITING | FieldType.FREE_PARKING:
                return "end_roll"
            case FieldType.STREET | FieldType.RAILROAD | FieldType.UTILITY:
                return "on_property"
            case FieldType.TAX:
                return "pay_tax"
            case FieldType.CC | FieldType.CHANCE:
                return "on_card"
            case FieldType.GO_TO_JAIL:
                return "go_to_jail"

    def _on_property(self) -> str:
        if not self.on_turn_player_field.owner:
            return "unowned_property"
        elif self.on_turn_player_field.owner == self.on_turn_player.uuid:
            return "end_roll"
        else:
            return "pay_rent"

    def _pay_rent(self) -> str:
        rent = self.on_turn_player_field.rent
        if self.on_turn_player_field.type == FieldType.UTILITY:
            rent *= self.controller.dice.last_roll.sum()
        if self.special_rent == "double":
            rent *= 2
        if self.special_rent == "10xroll":
            if self.extra_roll:
                rent = self.extra_roll.sum() * 10
            else:
                self.input_expected = True
                return "extra_roll"
        self.special_rent = ""
        self.controller.pay(rent, self.on_turn_player.uuid, self.on_turn_player_field.owner)
        return "end_roll"

    def _pay_tax(self):
        self.controller.pay(self.on_turn_player_field.tax, self.on_turn_player.uuid)
        return "end_roll"

    def _rent_roll(self) -> str:
        self.controller.roll(False)
        return "pay_rent"

    def _roll_dice(self) -> str:
        self.controller.roll()
        if self.controller.dice.triple_double:
            return "triple_double"
        else:
            return "moving"

    def _roll_in_jail(self) -> str:
        roll = self.controller.dice.roll(False)
        if roll.is_double():
            return "leaving_jail"
        else:
            self.controller.gd.on_turn_player.jail_turns += 1
            return "end_turn"

    def _take_card(self) -> str:
        deck = self.controller.cc if self.on_turn_player_field.type == FieldType.CC else self.controller.chance
        card = deck.draw()
        card.apply(self.controller)
        if card.special_rent:
            self.special_rent = card.special_rent
        if card.type == "move":
            return "moved"
        elif card.type == "go_to_jail":
            return "go_to_jail"
        elif card.ends_turn:
            return "end_turn"
        else:
            return "end_roll"

    def _unowned_property(self) -> str:
        self.input_expected = True
        return "buying_decision"

    def _get_possible_actions_in_jail(self):
        actions = {"payoff"}
        if self.controller.gd.on_turn_player.get_out_of_jail_cards > 0:
            actions.add("use_card")
        if self.controller.gd.on_turn_player.jail_turns < 3:
            actions.add("roll")
        return actions

    def _end_turn(self):
        self._change_state(EndTurnState(self.controller))
        self._broadcast_changes()

# === STAGES LIST ===
'''
stages = {
    "auctioning",  # player decided not to buy a property
    "buying_property",  # player decided to buy a property
    "end_roll",  # player did all actions after roll. If player rolled doubles,
                 # rolls again
    "end_turn",  # player's turn is over
    "go_to_jail",  # player is moving to jail
    "leaving_jail",  # player is leaving jail
    "moved",  # player moved to a new field. It is separated from "moving"
              # because cards can move the player
    "moving",  # player is moving to a new field
    "on_card",  # player landed on a card field
    "on_property",  # player landed on a property field
    "pay_rent",  # player is going to pay a rent
    "pay_tax",  # player is going to pay a tax
    "payout",  # player decided to pay the fine to get out of jail
    "rent_roll",  # special roll required. Induced by chance card for paying 10x roll
                  # rent on utility field
    "rent_rolling",  # player is rolling for the "rent_roll"(see above)
    "roll_in_jail",  # player in jail decided to roll
    "rolling",  # player is rolling for regular movement
    "unowned_property",  # player landed on an unowned property
    "use_card",  # player in jail decided to use a free of jail card
    "triple_double",  # player rolled 3 doubles in a row
} '''