import itertools
import logging
import random

from board_description import FieldType
from interfaces import ClientMessage, IPlayer, IField, IController, IRoll
from state.state import State
from state.end_turn import EndTurnState


class BeginTurnState(State):
    def __init__(self, controller: IController):
        super().__init__(controller)
        self.on_turn_player: IPlayer = self.controller.gd.on_turn_player
        self.extra_roll: IRoll | None = None
        self.stage = "in_jail" if self.on_turn_player.in_jail else "begin_turn"
        self.input_expected = True

    @property
    def on_turn_player_field(self) -> IField:
        return self.controller.gd.fields.get_field(self.on_turn_player.field)

    def get_possible_actions(self, player: IPlayer) -> set[str]:
        if self.stage == "pre_game":
            return {"add_player", "update_player", "start_game"}
        if not player == self.on_turn_player:
            return set()
        match self.stage:
            case "begin_turn":
                return {"roll"}
            case "in_jail":
                return self._get_possible_actions_in_jail()
            case "rent_roll":
                return {"roll"}
            case "buying_decision":
                return {"buy", "auction"}
            case "end_turn":
                return {"end_turn"}

    def parse(self, message: ClientMessage):
        if message["action"] not in self.get_possible_actions(self.controller.gd.players[message["my_uuid"]]):
            return
        match message["action"]:
            case "add_player":
                self.stage = "add_player"
            case "update_player":
                self.stage = "update_player"
            case "start_game":
                self.stage = "start_game"
            case "roll":
                if self.stage == "rent_roll":
                    self.stage = "rent_rolling"
                elif self.stage == "in_jail":
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
            case "buy":
                self.stage = "buying_property"
            case "auction":
                self.stage = "auctioning"
            case "end_turn":
                self.stage = "end_turn_confirmed"
        if not self.controller.gd.is_player_on_turn(message["my_uuid"]):
            return  # The player is not on turn.
            # TODO add possibilities of buying houses, mortgaging and trading.
        self.input_expected = False
        self._run_action_loop(message)

    def _run_action_loop(self, message: ClientMessage):
        while not self.input_expected:
            match self.stage:
                case "add_player":
                    self.stage = self._add_player(message)
                case "auctioning":
                    self.stage = "end_roll"  # TODO
                case "buying_property":
                    self.stage = self._buy_property()
                case "end_roll":
                    self.stage = self._end_roll()
                case "end_turn":
                    self.stage = self._end_turn()
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
                case "start_game":
                    self.stage = self._start_game()
                case "unowned_property":
                    self.stage = self._unowned_property()
                case "update_player":
                    self.stage = self._update_player(message)
                case "triple_double":
                    self.stage = self._go_to_jail()

    def _add_player(self, message: ClientMessage) -> str:
        def send_initial_message(to: IPlayer) -> None:
            """
            Generates the initial message for the given player containing all necessary data from the game data.
            The message is then sent.
            :param to: The player.
            :type to: IPlayer
            :return: The initial message as bytes.
            :rtype: bytes
            """
            for record in self.controller.gd.get_all_for_player(to.uuid):
                self.controller.message.add(to=to.uuid, **record)
            (self.controller.message
             .add(to=to.uuid, section="events", item="possible_actions", value=self.get_possible_actions(to))
             .send(to.uuid))

        if message["my_uuid"] != self.controller.server_uuid:
            ''' Only the server should be able to add other players. '''
            logging.warning(f"Player {message['my_uuid']} is trying to add other player.")
        else:
            parameters = message["parameters"]
            player = self.controller.gd.players.add(parameters["player_uuid"], parameters["player_id"])
            send_initial_message(player)
            self._broadcast_changes()
            logging.info(f"Player {parameters['player_uuid']} added.")
        self.input_expected = True
        return "pre_game"

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

    def _end_turn(self) -> str:
        self.input_expected = True
        return "end_turn"

    def _end_turn_confirmed(self) -> str:
        game_data = self.controller.gd
        game_data.update(section="misc", item="on_turn", value=next(game_data.player_order_cycler))
        self.on_turn_player = game_data.on_turn_player
        self.special_rent = ""
        self.extra_roll = None
        self.controller.dice.reset()
        self._broadcast_changes()
        self.input_expected = True
        return "begin_turn"

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
        if self.special_rent == "10xroll":
            if self.extra_roll:
                rent = self.extra_roll.sum() * 10
                self.special_rent = ""
                self.extra_roll = None
            else:
                self.input_expected = True
                return "rent_roll"
        else:
            rent = self.on_turn_player_field.rent
            if self.on_turn_player_field.type == FieldType.UTILITY:
                rent *= self.controller.dice.last_roll.sum()
            elif self.special_rent == "double":
                rent *= 2
        self.controller.pay(rent, self.on_turn_player.uuid, self.on_turn_player_field.owner)
        return "end_roll"

    def _pay_tax(self):
        self.controller.pay(self.on_turn_player_field.tax, self.on_turn_player.uuid)
        return "end_roll"

    def _rent_roll(self) -> str:
        self.extra_roll = self.controller.roll(False)
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

    def _start_game(self) -> str:
        game_data = self.controller.gd
        if not game_data.players.is_all_ready():
            logging.warning("Not all players are ready.")
            return "pre_game"
        if len(game_data.players) < 2:
            logging.warning("Not enough players.")
            return "pre_game"
        game_data.update(section="misc", item="state", value="begin_turn")
        game_data.set_initial_values()
        player_order = list(range(len(game_data.players)))
        random.shuffle(player_order)
        game_data.update(section="misc", item="player_order", value=player_order)
        game_data.player_order_cycler = itertools.cycle(player_order)
        game_data.update(section="misc", item="on_turn", value=next(game_data.player_order_cycler))
        game_data.update(section="events", item="game_started", value=True)
        self.controller.message.server.locked = True
        self._broadcast_changes()
        self.on_turn_player = game_data.on_turn_player
        logging.info("Game started.")
        self.input_expected = True
        return "begin_turn"

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

    def _update_player(self, message: ClientMessage):
        player = self.controller.gd.players[message["my_uuid"]]
        self.controller.gd.update(
            section="players",
            item=player.uuid,
            attribute=message["parameters"]["attribute"],
            value=message["parameters"]["value"]
        )
        self._broadcast_changes()
        self.input_expected = True
        return "pre_game"

    def _get_possible_actions_in_jail(self):
        actions = {"payout"}
        if self.controller.gd.on_turn_player.get_out_of_jail_cards > 0:
            actions.add("use_card")
        if self.controller.gd.on_turn_player.jail_turns < 3:
            actions.add("roll")
        return actions

# === STAGES LIST ===
'''
stages = {
    "add_player",  # player joined the game
    "auctioning",  # player decided not to buy a property
    "begin_turn",  # player is on turn and rolls dices, input is expected
    "buying_property",  # player decided to buy a property
    "end_roll",  # player did all actions after roll. If player rolled doubles,
                 # rolls again
    "end_turn",  # player's turn is over, waiting for confirmation, input is expected
    "end_turn_confirmed",  # player confirmed his turn, new turn begins, input is expected
    "go_to_jail",  # player is moving to jail
    "in_jail",  # player is in jail, input is expected
    "leaving_jail",  # player is leaving jail
    "moved",  # player moved to a new field. It is separated from "moving"
              # because cards can move the player
    "moving",  # player is moving to a new field
    "on_card",  # player landed on a card field
    "on_property",  # player landed on a property field
    "pay_rent",  # player is going to pay a rent. When player got to a utility field
                 # due to Chance card, he will pay 10x roll, so input is expected
    "pay_tax",  # player is going to pay a tax
    "payout",  # player decided to pay the fine to get out of jail
    "rent_roll",  # special roll required. Induced by chance card for paying 10x roll
                  # rent on utility field
    "rent_rolling",  # player is rolling for the "rent_roll"(see above)
    "roll_in_jail",  # player in jail decided to roll
    "rolling",  # player is rolling for regular movement
    "start_game",  # game is starting
    "unowned_property",  # player landed on an unowned property, input is expected
    "update_player",  # player changed his properties
    "use_card",  # player in jail decided to use a free of jail card
    "triple_double",  # player rolled 3 doubles in a row
} '''