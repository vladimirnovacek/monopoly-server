import itertools
import logging
import random

from uuid import UUID

import config
from board_description import FieldType, StreetColor
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

    def get_possible_actions(self, player_uuid: UUID) -> list[str]:
        if player_uuid == self.controller.server_uuid:
            return ["add_player"]
        if self.stage == "pre_game":
            return ["update_player", "start_game"]
        if player_uuid != self.on_turn_player.uuid:
            return []
        match self.stage:
            case "begin_turn":
                return ["roll"]
            case "in_jail":
                return self._get_possible_actions_in_jail()
            case "rent_roll":
                return ["roll"]
            case "buying_decision":
                return ["buy", "auction"]
            case "end_turn":
                return ["end_turn"]

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
                self._auction()
            case "end_turn":
                self._end_turn_confirmed()
            # TODO add possibilities of buying houses, mortgaging and trading.

    def _add_player(self, message: ClientMessage) -> None:
        if message["my_uuid"] != self.controller.server_uuid:
            ''' Only the server should be able to add other players. '''
            logging.warning(f"Player {message['my_uuid']} is trying to add other player.")
        else:
            parameters = message["parameters"]
            for player in self.controller.gd.players:
                self.controller.update(section="players", item=player, attribute="ready", value=False)
            self.controller.send_event("update_player")
            player = self.controller.gd.add_player(parameters["player_uuid"], parameters["player_id"])
            for record in self.controller.gd.get_all_for_player(player.uuid):
                self.controller.message.add(to=player.uuid, **record)
            self.controller.send_event("initialize", to=player.uuid)
            for attribute in player:
                self.controller.add_message(
                    section="players", item=player.uuid, attribute=attribute, value=player[attribute]
                )
            self._change_stage("pre_game", "player_connected")
            logging.info(f"Player {player.name} connected to the game.")

    def _auction(self):
        self.controller.add_message(section="misc", item="bid", value=0)
        self.controller.send_event("auction")
        self._end_turn()

    def _buy_property(self) -> None:
        self.controller.buy_property(self.on_turn_player_field, self.on_turn_player)
        self.controller.add_message(section="misc", item="price", value=self.on_turn_player_field.price)
        self.controller.send_event("property_bought")
        logging.info(f"Player {self.on_turn_player.uuid} bought {self.on_turn_player_field.name} for "
                     f"{self.on_turn_player_field.price}.")
        self._end_roll()

    def _buy_houses(self, message: ClientMessage) -> None:
        params = message["parameters"]
        color = params["color"]
        new_houses = params["houses"]
        '''
        Checks:
        - if player has full set
        - if no street from the set has a mortgage
        - if building max five houses in one street (rounding to 5 in that case)
        - if the difference between houses in any two streets is less or equal to 1
        '''
        if not self.controller.gd.fields.has_full_set(StreetColor(color), self.on_turn_player):
            return
        full_set = list(self.controller.gd.fields.get_full_set(StreetColor(color)))
        if any(street.mortgage for street in full_set):
            return
        old_houses = [street.houses for street in full_set]
        houses = []
        for i, (o, n) in enumerate(zip(old_houses, new_houses)):
            total = o + n
            if total > 5:
                total = 5
                new_houses[i] = 5 - o
            houses.append(total)
        max_houses = max(houses)
        if any((max_houses - 1 > h or h > max_houses for h in houses)):
            return
        price = 0
        for h, street, n in zip(houses, full_set, new_houses):
            self.controller.update(section="fields", item=street.id, attribute="houses", value=h)
            if h == 5 and n > 0:
                price += street.hotel_price
                n -= 1
            price += street.house_price * n
        self.controller.pay(price, self.on_turn_player.uuid)
        self.controller.send_event("houses_bought")

    def _end_roll(self) -> None:
        if self.controller.dice.last_roll.is_double():
            self._change_stage("begin_turn")
            logging.info(f"Player {self.on_turn_player.name} rolled a double and rolls again.")
        else:
            self._end_turn()

    def _end_turn(self) -> None:
        logging.info(f"Player {self.on_turn_player.name} ended their turn.")
        self._change_stage("end_turn")

    def _end_turn_confirmed(self) -> None:
        on_turn = next(self.controller.gd.player_order_cycler)
        self.controller.update(section="misc", item="on_turn", value=on_turn)
        self.on_turn_player = self.controller.gd.on_turn_player
        self.special_rent = ""
        self.extra_roll = None
        self.controller.dice.reset()
        logging.info(f"Player {self.on_turn_player.name} is on turn.")
        if self.on_turn_player.in_jail:
            stage = "in_jail"
        else:
            stage = "begin_turn"
        self._change_stage(stage, "begin_turn")

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
        self._change_stage("begin_turn", "leaving_jail")

    def _mortgage(self, message: ClientMessage) -> None:
        field_id = message["parameters"]["field"]
        field = self.controller.gd.fields[field_id]
        if not field.is_property() or field.owner != message["my_uuid"] or field.mortgage:
            return
        for f in self.controller.gd.fields.get_full_set(field):
            if f.houses > 0:
                return
        self.controller.collect(field.mortgage_value, message["my_uuid"])
        self.controller.update(section="fields", item=field_id, attribute="mortgage", value=True)
        self.controller.send_event("mortgage")

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
            self._change_stage("buying_decision")
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
        if self.on_turn_player_field.mortgage:
            self._end_roll()
        if self.special_rent == "10xroll":
            if self.extra_roll:
                rent = self.extra_roll.sum() * 10
                self.special_rent = ""
                self.extra_roll = None
            else:
                self._change_stage("rent_roll")
                return
        else:
            rent = self.on_turn_player_field.rent
            if self.on_turn_player_field.type == FieldType.UTILITY:
                rent *= self.controller.dice.last_roll.sum()
            if self.special_rent == "double":
                rent *= 2
        logging.info(
            f"Player {self.on_turn_player.name} pays the rent of £{rent} to "
            f"{self.controller.gd.players[self.on_turn_player_field.owner].name}."
        )
        self.controller.pay(rent, self.on_turn_player.uuid, self.on_turn_player_field.owner)
        self.controller.add_message(section="misc", item="rent", value=rent)
        self.controller.send_event("rent_paid")
        self._end_roll()

    def _pay_tax(self) -> None:
        tax = self.on_turn_player_field.tax
        logging.info(f"Player {self.on_turn_player.name} pays the tax of £{tax}.")
        self.controller.pay(tax, self.on_turn_player.uuid)
        self.controller.add_message(section="misc", item="tax", value=tax)
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
        roll = self.controller.roll(False)
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
        self.controller.gd.player_order_cycler = itertools.cycle(player_order)
        self.controller.message.server.locked = True
        self.controller.send_event("game_started")
        self.controller.update(section="misc", item="on_turn", value=next(self.controller.gd.player_order_cycler))
        self.on_turn_player = gd.on_turn_player
        logging.info("Game started.")
        self._change_stage("begin_turn")

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
        self.controller.gd.update(section="event", item="use_card", value=True)
        cards_left = self.on_turn_player.get_out_of_jail_cards - 1
        self.on_turn_player.get_out_of_jail_cards = cards_left
        self.controller.update(
            section="players", item=self.on_turn_player.uuid, attribute="get_out_of_jail_cards", value=cards_left
        )
        self.controller.send_event("use_card")
        logging.info(f"Player {self.on_turn_player.name} uses a get out of jail card.")
        self._leave_jail()

    def _get_possible_actions_in_jail(self) -> list[str]:
        actions = ["payout"]
        if self.on_turn_player.get_out_of_jail_cards > 0:
            actions.append("use_card")
        if self.on_turn_player.jail_turns < 2:
            actions.append("roll")
        return actions

    def _change_stage(self, stage: str, event: str | None = None) -> None:
        if not event:
            event = stage
        self.stage = stage
        self._send_possible_actions()
        self.controller.send_event(event)

    def _send_possible_actions(self) -> None:
        for player_uuid in self.controller.gd.players:
            self.controller.add_message(
                section="misc", item="possible_actions", value=self.get_possible_actions(player_uuid), to=player_uuid
            )
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