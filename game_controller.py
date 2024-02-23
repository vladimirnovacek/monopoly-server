from typing import Any
from uuid import UUID

import config
from chance_cc_cards import CardDeck
from dice import Dice
from interfaces import ClientMessage, IController, IMessenger, IData, IDice, IRoll, IField, IPlayer
from turn import Turn


class GameController(IController):
    def __init__(self, data: IData, messenger: IMessenger):
        super().__init__(data)
        self.gd: IData = data
        self.message: IMessenger | None = messenger
        self.message.controller = self
        self.server_uuid: UUID | None = None
        self.turn: Turn = Turn(self)
        self.dice: IDice = Dice(2, 6)
        self.cc: CardDeck = CardDeck("cc")
        self.chance: CardDeck = CardDeck("chance")

    def __getattr__(self, item):
        return getattr(self.turn, item)

    def parse(self, message: ClientMessage) -> None:
        self.turn.parse(message)

    def roll(self, register: bool = True) -> IRoll:
        roll = self.dice.roll(register)
        self.send_event(event="roll", value=roll.get())
        return roll

    def pay(self, payment: int, payer_uuid: UUID, payee_uuid: UUID | None = None) -> None:
        """
        Pay the given amount of cash from the given payer to the given payee. If the payment is meant to the bank,
        the payee_uuid should be None.
        :param payment:
        :type payment: int
        :param payer_uuid:
        :type payer_uuid:
        :param payee_uuid:
        :type payee_uuid:
        :return:
        :rtype:
        """
        payer_cash = self.gd.players[payer_uuid].cash
        self.update(section="players", item=payer_uuid, attribute="cash", value=payer_cash - payment)
        if payee_uuid is not None:
            payee_cash = self.gd.players[payee_uuid].cash
            self.update(section="players", item=payee_uuid, attribute="cash", value=payee_cash + payment)

    def collect(self, payment: int, player_uuid: UUID) -> None:
        """
        Collect the given amount of cash for the given player.
        :param payment:
        :type payment:
        :param player_uuid:
        :type player_uuid:
        :return:
        :rtype:
        """
        player_cash = self.gd.players[player_uuid].cash
        self.update(section="players", item=player_uuid, attribute="cash", value=player_cash + payment)

    def move_to(self, field_id: int, player_uuid: UUID | None = None, check_pass_go: bool = False) -> None:
        """
        Moves a player to a new field. If player_uuid is None, the player on turn is moved. If check_pass_go is True,
        the player will be checked if they pass Go and paid off.
        :param field_id:
        :type field_id:
        :param player_uuid: The UUID of the player.
        :type player_uuid: UUID | None
        :param check_pass_go: Whether to check if the player passes Go.
        :type check_pass_go: bool
        """
        if player_uuid is None:
            player_uuid = self.gd.on_turn_uuid
        original_field = self.gd.players[player_uuid].field
        self.update(section="players", item=player_uuid, attribute="field", value=field_id)
        if field_id == self.gd.fields.JAIL:
            self.update(section="players", item=player_uuid, attribute="in_jail", value=True)
        elif original_field == self.gd.fields.JAIL:
            self.update(section="players", item=player_uuid, attribute="in_jail", value=False)
        elif check_pass_go and original_field > field_id:
            self.add_message(section="events", item="pass_go", value=True)
            self.collect(config.go_cash, player_uuid)


    def move_by(self, fields: int, player_uuid: UUID | None = None, check_pass_go: bool = True) -> None:
        """
        Moves a player by the given number of fields. If player_uuid is None, the player on turn is moved. If
        check_pass_go is True, the player will be checked if they pass Go and paid off.
        :param fields: How many fields to move.
        :type fields: int
        :param player_uuid: Player UUID.
        :type player_uuid: UUID
        :param check_pass_go: Whether to check if the player passes Go.
        :type check_pass_go: bool
        """
        if player_uuid is None:
            player_uuid = self.gd.on_turn_uuid
        original_field = self.gd.players[player_uuid].field
        new_field = self.gd.fields.advance_field_id(original_field, fields)
        self.move_to(new_field, player_uuid, check_pass_go)

    def buy_property(self, field: IField, player: IPlayer, price: int = -1) -> None:
        if price == -1:
            price = field.price
        self.pay(price, player.uuid, field.owner)
        self.update(section="fields", item=field.id, attribute="owner", value=player.uuid)

    def update(self, *, section: str, item: Any, attribute: str | None = None, value: Any) -> bool:
        change = self.gd.update(section=section, item=item, attribute=attribute, value=value)
        if change:
            self.add_message(section=section, item=item, attribute=attribute, value=value)
        return change

    def send_event(self, event: str, value: Any = True, to: str = "all") -> None:
        self.add_message(section="events", item=event, value=value, to=to)
        self.message.broadcast()

    def add_message(self, *, section: str, item: Any, attribute: str = None, value: Any, to: str = "all") -> None:
        if type(item) == UUID:
            item = self.gd.players[item].player_id
        self.message.add(to=to, section=section, item=item, attribute=attribute, value=value)
