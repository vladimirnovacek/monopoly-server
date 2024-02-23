import itertools
import logging
import random

from uuid import UUID

import config
from board_description import FieldType
from interfaces import ClientMessage, IPlayer, IField, IController, IRoll


class Turn:
    def __init__(self, controller: IController):
        self.controller: IController = controller
        self.on_turn_player: IPlayer | None = None
        self.extra_roll: IRoll | None = None
        self.stage = "pre_game"

    @property
    def on_turn_player_field(self) -> IField:
        return self.controller.gd.fields.get_field(self.on_turn_player.field)

    def get_possible_actions(self, player_uuid: UUID) -> set[str]:
        if player_uuid == self.controller.server_uuid:
            return {"add_player"}
        if self.stage in ("pre_game", "add_player"):
            return {"update_player", "start_game"}
        if player_uuid != self.on_turn_player.uuid:
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
        if message["action"] not in self.get_possible_actions(message["my_uuid"]):
            return
        match message["action"]:
            case "add_player":
                self._add_player(message)
            case "update_player":
                self._update_player(message)
            case "start_game":
                self._start_game()
            case "roll":
                if self.stage == "rent_roll":
                    self._rent_roll()
                elif self.stage == "in_jail":
                    self._roll_in_jail()
                else:
                    self._roll_dice()
            case "payout":
                self._payout()
            case "use_card":
                self._use_card()
            case "buy":
                self._buy_property()
            case "auction":
                self._end_roll()
            case "end_turn":
                self._end_turn_confirmed()
            # TODO add possibilities of buying houses, mortgaging and trading.

    def _add_player(self, message: ClientMessage) -> None:
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
            self.controller.add_message(
                section="misc", item="possible_actions", value=self.get_possible_actions(to.uuid), to=to.uuid
            )
            self.controller.send_event("initialize", to=to.uuid)

        if message["my_uuid"] != self.controller.server_uuid:
            ''' Only the server should be able to add other players. '''
            logging.warning(f"Player {message['my_uuid']} is trying to add other player.")
        else:
            parameters = message["parameters"]
            for player in self.controller.gd.players:
                self.controller.update(section="players", item=player, attribute="ready", value=False)
            player = self.controller.gd.add_player(parameters["player_uuid"], parameters["player_id"])
            send_initial_message(player)
            for attribute in player:
                self.controller.add_message(
                    section="players", item=player.uuid, attribute=attribute, value=player[attribute]
                )
            self.controller.send_event("player_connected", value=player.player_id)
            logging.info(f"Player {player.name} connected to the game.")
        self.stage = "pre_game"

    def _buy_property(self) -> None:
        self.controller.buy_property(self.on_turn_player_field, self.on_turn_player)
        self.controller.send_event("property_bought")
        logging.info(f"Player {self.on_turn_player.uuid} bought {self.on_turn_player_field.name} for "
                     f"{self.on_turn_player_field.price}.")
        self._end_roll()

    def _end_roll(self) -> None:
        if self.controller.dice.last_roll.is_double():
            self.controller.send_event("end_roll")
            logging.info(f"Player {self.on_turn_player.name} rolled a double and rolls again.")
            self.stage = "begin_turn"
        else:
            self._end_turn()

    def _end_turn(self) -> None:
        logging.info(f"Player {self.on_turn_player.name} ended their turn.")
        self.controller.send_event("end_turn", value=self.on_turn_player.player_id)
        self.stage = "end_turn"

    def _end_turn_confirmed(self) -> None:
        on_turn = next(self.controller.gd.player_order_cycler)
        self.controller.update(section="misc", item="on_turn", value=on_turn)
        self.on_turn_player = self.controller.gd.on_turn_player
        self.special_rent = ""
        self.extra_roll = None
        self.controller.dice.reset()
        logging.info(f"Player {self.on_turn_player.name} is on turn.")
        self.controller.send_event("begin_turn", value=self.on_turn_player.player_id)
        if self.on_turn_player.in_jail:
            self.stage = "in_jail"
        else:
            self.stage = "begin_turn"

    def _go_to_jail(self) -> None:
        logging.info(f"Player {self.on_turn_player.name} was sent to jail.")
        self.controller.move_to(self.controller.gd.fields.JAIL)
        self.controller.send_event("go_to_jail")
        self._end_turn()

    def _leave_jail(self) -> None:
        self.on_turn_player.in_jail = False
        self.on_turn_player.jail_turns = 0
        self.controller.move_to(self.controller.gd.fields.JUST_VISITING)
        logging.info(f"Player {self.on_turn_player.name} left jail.")
        self.controller.send_event("leaving_jail")
        self.stage = "begin_turn"

    def _move(self) -> None:
        self.controller.move_by(self.controller.dice.last_roll.sum())
        logging.info(f"Player {self.on_turn_player.name} moved to {self.on_turn_player_field.name}.")
        self._moved()

    def _moved(self) -> None:
        self.controller.send_event("moved")
        match self.on_turn_player_field.type:
            case FieldType.GO | FieldType.JUST_VISITING | FieldType.FREE_PARKING:
                self._end_roll()
            case FieldType.STREET | FieldType.RAILROAD | FieldType.UTILITY:
                self._on_property()
            case FieldType.TAX:
                self._pay_tax()
            case FieldType.CC | FieldType.CHANCE:
                self._take_card()
            case FieldType.GO_TO_JAIL:
                self._go_to_jail()

    def _on_property(self) -> None:
        if not self.on_turn_player_field.owner:
            self._unowned_property()
        elif self.on_turn_player_field.owner == self.on_turn_player.uuid:
            self._end_roll()
        else:
            self._pay_rent()

    def _payout(self) -> None:
        logging.info(f"Player {self.on_turn_player.name} pays the fine.")
        self.controller.pay(config.payout_price, self.on_turn_player.uuid)
        self.controller.send_event("payout")
        self._leave_jail()

    def _pay_rent(self) -> None:
        if self.special_rent == "10xroll":
            if self.extra_roll:
                rent = self.extra_roll.sum() * 10
                self.special_rent = ""
                self.extra_roll = None
            else:
                self.controller.send_event("rent_roll")
                self.stage = "rent_roll"
                return
        else:
            rent = self.on_turn_player_field.rent
            if self.on_turn_player_field.type == FieldType.UTILITY:
                rent *= self.controller.dice.last_roll.sum()
            if self.special_rent == "double":
                rent *= 2
        logging.info(
            f"Player {self.on_turn_player.name} pays the rent of £{rent} to {self.on_turn_player_field.owner}."
        )
        self.controller.pay(rent, self.on_turn_player.uuid, self.on_turn_player_field.owner)
        self.controller.send_event("rent_paid")
        self._end_roll()

    def _pay_tax(self) -> None:
        logging.info(f"Player {self.on_turn_player.name} pays the tax of £{self.on_turn_player_field.tax}.")
        self.controller.pay(self.on_turn_player_field.tax, self.on_turn_player.uuid)
        self.controller.send_event("tax_paid")
        self._end_roll()

    def _rent_roll(self) -> None:
        self.extra_roll = self.controller.roll(False)
        self.controller.send_event("rent_roll")
        logging.info(f"Player {self.on_turn_player.name} rolled a {self.extra_roll.sum()}.")
        self._pay_rent()

    def _roll_dice(self) -> None:
        roll = self.controller.roll()
        logging.info(f"Player {self.on_turn_player.name} rolled a {roll.sum()}.")
        if self.controller.dice.triple_double:
            self.controller.send_event("triple_double")
            self._go_to_jail()
        else:
            self._move()

    def _roll_in_jail(self) -> None:
        roll = self.controller.dice.roll(False)
        self.controller.send_event("roll_in_jail")
        logging.info(f"Player {self.on_turn_player.name} rolled {roll.get()[0]} and {roll.get()[1]}.")
        if roll.is_double():
            self._leave_jail()
        else:
            self.controller.gd.on_turn_player.jail_turns += 1
            self._end_turn()

    def _start_game(self) -> None:
        gd = self.controller.gd
        if not gd.players.is_all_ready():
            logging.warning("Not all players are ready.")
            return
        if len(gd.players) < 2:
            logging.warning("Not enough players.")
            return
        for player in gd.players:
            self.controller.update(section="players", item=player, attribute="cash", value=config.initial_cash)
            self.controller.update(section="players", item=player, attribute="field", value=config.initial_field)
        player_order = list(range(len(gd.players)))
        random.shuffle(player_order)
        self.controller.update(section="misc", item="player_order", value=player_order)
        self.player_order_cycler = itertools.cycle(player_order)
        self.controller.update(section="misc", item="on_turn", value=next(self.player_order_cycler))
        self.controller.message.server.locked = True
        self.on_turn_player = gd.on_turn_player
        self.controller.send_event("game_started")
        logging.info("Game started.")
        self.stage = "begin_turn"

    def _take_card(self) -> None:
        deck = self.controller.cc if self.on_turn_player_field.type == FieldType.CC else self.controller.chance
        card = deck.draw()
        logging.info(f"Player {self.on_turn_player.name} takes card saying: {card.text}.")
        self.controller.add_message(section="misc", item="card", value=(card.id, card.text))
        self.controller.send_event("card")
        card.apply(self.controller)
        if card.special_rent:
            self.special_rent = card.special_rent
        if card.type == "move":
            self._moved()
        elif card.type == "go_to_jail":
            self._go_to_jail()
        elif card.ends_turn:
            self._end_turn()
        else:
            self._end_roll()

    def _unowned_property(self) -> None:
        self.controller.send_event("buying_decision")
        self.stage = "buying_decision"

    def _update_player(self, message: ClientMessage) -> None:
        player = self.controller.gd.players[message["my_uuid"]]
        if message["parameters"]["attribute"] not in ("name", "token", "ready"):
            logging.warning(f"Attempt to update invalid player attribute: {message['parameters']['attribute']} by "
                            f"player {player.name}: {player.uuid}.")
            return
        if self.controller.update(
                section="players",
                item=player.uuid,
                attribute=message["parameters"]["attribute"],
                value=message["parameters"]["value"]
        ):
            self.controller.send_event("player_updated")
            if message["parameters"]["attribute"] == "ready":
                if self.controller.gd.players.is_all_ready() and len(self.controller.gd.players) >= 2:
                    self._start_game()

    def _use_card(self) -> None:
        self.controller.gd.update(section="events", item="use_card", value=True)
        cards_left = self.on_turn_player.get_out_of_jail_cards - 1
        self.on_turn_player.get_out_of_jail_cards = cards_left
        self.controller.update(
            section="players", item=self.on_turn_player.uuid, attribute="get_out_of_jail_cards", value=cards_left
        )
        self.controller.send_event("use_card")
        logging.info(f"Player {self.on_turn_player.name} uses a get out of jail card.")
        self._leave_jail()

    def _get_possible_actions_in_jail(self):
        actions = {"payout"}
        if self.on_turn_player.get_out_of_jail_cards > 0:
            actions.add("use_card")
        if self.on_turn_player.jail_turns < 3:
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
    pregame, begin_turn, end_turn, in_jail, rent_roll, buying_decision
} '''