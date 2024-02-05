
from uuid import UUID

import config
from chance_cc_cards import CardDeck
from dice import Dice
from interfaces import ClientMessage, IController, IMessenger, IData, IDice, IRoll
from state.pre_game import PreGameState
from state.state import State


class GameController(IController):
    def __init__(self, data: IData):
        super().__init__(data)
        self.gd: IData = data
        self.message: IMessenger | None = None
        self.server_uuid: UUID | None = None
        self.state: State = PreGameState(self)
        self.dice: IDice = Dice(2, 6)
        self.cc: CardDeck = CardDeck("cc")
        self.chance: CardDeck = CardDeck("chance")

    def __getattr__(self, item):
        return getattr(self.state, item)

    def parse(self, message: ClientMessage) -> None:
        self.state.parse(message)

    def roll(self, register: bool = True) -> IRoll:
        roll = self.dice.roll(register)
        self.gd.update(section="events", item="roll", value=roll.get())
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
        self.gd.update(section="players", item=payer_uuid, attribute="cash", value=payer_cash - payment)
        if payee_uuid is not None:
            payee_cash = self.gd.players[payee_uuid].cash
            self.gd.update(section="players", item=payee_uuid, attribute="cash", value=payee_cash + payment)

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
        self.gd.update(section="players", item=player_uuid, attribute="cash", value=player_cash + payment)

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
