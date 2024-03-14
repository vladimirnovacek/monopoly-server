from abc import ABC, abstractmethod
from collections.abc import Sized, Iterable, Iterator
from typing import Self, TypedDict, Any, ClassVar, Optional
from uuid import UUID

from board_description import FieldType


class ClientMessage(TypedDict):
    my_uuid: UUID
    action: str
    parameters: dict


class IServer(ABC):
    server_uuid: UUID


class IMessenger(ABC):
    server: IServer
    controller: "IController"

    @abstractmethod
    def add(self, to: str | UUID = "all", **kwargs: Any) -> Self:
        ...

    @abstractmethod
    def send(self, player_uuid: UUID, message: Any | None = None) -> None:
        ...

    @abstractmethod
    def broadcast(self) -> None:
        ...

    @abstractmethod
    def receive(self, message: ClientMessage) -> None:
        ...

    @abstractmethod
    def set_server(self, server: IServer) -> None:
        ...

    @abstractmethod
    def is_messages_pending(self) -> bool:
        ...


class IDataUnit(ABC):
    ...


class IPlayer(ABC):
    uuid: UUID
    player_id: int
    name: str
    token: str
    ready: bool
    field: int
    in_jail: bool
    jail_turns: int
    get_out_of_jail_cards: int

    def __getitem__(self, item):
        ...

    @abstractmethod
    def __iter__(self):
        ...


class IPlayers(IDataUnit, Sized, Iterable):
    @abstractmethod
    def __getitem__(self, item):
        ...

    @abstractmethod
    def uuid_from_id(self, player_id: int) -> UUID:
        ...

    @abstractmethod
    def add(self, player_uuid: UUID, player_id: int) -> IPlayer:
        ...

    @abstractmethod
    def is_all_ready(self) -> bool:
        ...


class IField(ABC):
    name: str
    id: int
    type: FieldType
    owner: Optional[UUID]
    price: int
    rent: int
    tax: int
    mortgage: bool
    mortgage_value: int
    houses: int

    @abstractmethod
    def is_property(self):
        ...


class IFields(IDataUnit):
    GO: ClassVar[int]
    JAIL: ClassVar[int]
    JUST_VISITING: ClassVar[int]

    @abstractmethod
    def __getitem__(self, item) -> IField:
        ...

    @abstractmethod
    def get_field(self, field_id: int) -> IField:
        ...

    @abstractmethod
    def get_full_set(self, attr) -> set[IField]:
        ...

    @abstractmethod
    def count_houses(self, player_uuid: UUID) -> int:
        ...

    @abstractmethod
    def advance_field_id(self, original_field: int, steps: int) -> int:
        ...

    @abstractmethod
    def has_full_set(self, attr, owner):
        ...


class IData(ABC):
    players: IPlayers
    fields: IFields
    player_order_cycler: Iterator

    @property
    @abstractmethod
    def on_turn_uuid(self) -> UUID | None:
        ...

    @property
    @abstractmethod
    def on_turn_player(self) -> IPlayer | None:
        ...

    @abstractmethod
    def __getitem__(self, item):
        ...

    @abstractmethod
    def add_player(self, player_uuid: UUID, player_id: int) -> IPlayer:
        ...

    @abstractmethod
    def get_all_for_player(self, player_uuid: UUID) -> list[dict]:
        ...

    @abstractmethod
    def get_value(self, section: str, item: str | UUID, attribute: str | None = None) -> Any:
        ...

    @abstractmethod
    def set_initial_values(self) -> None:
        ...

    @abstractmethod
    def update(self, *, section: str, item: int |str | UUID, attribute: str | None = None, value: Any) -> bool:
        ...

    @abstractmethod
    def is_player_on_turn(self, player_uuid: UUID) -> bool:
        ...


class IRoll(ABC):
    """
    Class represents a roll of dice. You can access particular dice values using the index,
    e.g. Roll[0] returns the first dice.
    """

    @abstractmethod
    def __getitem__(self, item) -> int:
        ...

    @abstractmethod
    def get(self) -> tuple[int, ...]:
        """
        Returns the roll as a tuple of individual dice values.
        :return: The roll as a tuple of individual dice values.
        :rtype: tuple[int, ...]
        """
        ...

    @abstractmethod
    def sum(self) -> int:
        """
        Returns the sum of all the dice values.
        :return: The sum of all the dice values.
        :rtype: int
        """
        ...

    @abstractmethod
    def is_double(self) -> bool:
        """
        Returns True if all the dice are equal.
        :return: True if all the dice are equal.
        :rtype: bool
        """
        ...

class IDice(ABC):
    last_roll: IRoll | None
    """ The last roll. None if no roll has been made yet. """

    @property
    @abstractmethod
    def triple_double(self) -> bool:
        """ True if three doubles rolled in a row. """
        ...

    @abstractmethod
    def roll(self, register: bool = True) -> IRoll:
        """
        Rolls the dice.
        :param register: If True, the roll counts toward doubles.
        :type register: bool
        :return: Roll object
        :rtype: Roll
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Resets the double counter and last_roll attribute.
        """
        ...


class ICard(ABC):
    id: int
    text: str
    type: str
    ends_turn: bool
    special_rent: str

    @abstractmethod
    def apply(self, controller: "IController") -> None:
        """
        Apply the effects of the card through the given controller.
        :param controller: Controller that can apply the card effect.
        :type controller: IController
        """
        ...

class ICardDeck(ABC):

    @abstractmethod
    def draw(self) -> ICard:
        """
        Draw a next card from the deck and return it.
        :return: Drawn card
        :rtype: ICard
        """
        ...


class IController(ABC):
    dice: IDice
    gd: IData
    message: IMessenger
    server_uuid: UUID
    cc: ICardDeck
    chance: ICardDeck
    on_turn_player: IPlayer

    @abstractmethod
    def parse(self, message: ClientMessage) -> None:
        """
        Process the message given in the parameter.
        :param message:
        :type message: ClientMessage
        """
        ...

    @abstractmethod
    def roll(self, register: bool = True) -> IRoll:
        """
        Make a roll, add it to the message queue and send.
        :param register: Whether the roll counts towards double roll count.
        :type register: bool
        :return: The IRoll object
        :rtype: IRoll
        """
        ...

    @abstractmethod
    def pay(self, payment: int, payer_uuid: UUID, payee_uuid: UUID | None = None) -> None:
        """
        Pay the given amount of cash from the given payer to the given payee. If the payment is meant to the bank,
        the payee_uuid should be None.
        :param payment:
        :type payment: int
        :param payer_uuid:
        :type payer_uuid: UUID
        :param payee_uuid:
        :type payee_uuid: UUID
        """
        ...

    @abstractmethod
    def collect(self, payment: int, player_uuid: UUID) -> None:
        """
        Collect the given amount of cash for the given player from bank. For money transfer use pay() method
        :param payment:
        :type payment:
        :param player_uuid:
        :type player_uuid:
        :return:
        :rtype:
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def buy_property(self, field: IField, player: IPlayer, price: int = -1) -> None:
        """
        Change owner of the given field to the given player. Player also pays the given price
        to the owner. If price is not given, the original field price is used.
        :param field:
        :type field: IField
        :param player:
        :type player: IPlayer
        :param price: default: -1
        :type price: int
        """
        ...

    def send_event(self, event: str, value: Any = True, to: str | UUID = "all") -> None:
        """
        Adds a given event to the message queue and sends messages.
        :param event:
        :type event: str
        :param value: Obsolete.
        :type value: Any
        :param to: Send only to given client. When "all", event is send to all connected clients
        :type to: str | UUID
        """
        ...

    def update(self, *, section: str, item: Any, attribute: str | None = None, value: Any) -> bool:
        """
        Update game data with given parameters. If game data was changed, add to the message queue,
        :param section:
        :type section: str
        :param item:
        :type item: Any
        :param attribute:
        :type attribute: str
        :param value:
        :type value: Any
        :return: True if changes were made in game data, False otherwise
        :rtype: bool
        """
        ...

    def add_message(self, *, section: str, item: Any, attribute: str = None, value: Any, to: str | UUID = "all"):
        """
        Adds message to the message queue without updating game data.
        :param section:
        :type section: str
        :param item:
        :type item: Any
        :param attribute:
        :type attribute: str
        :param value:
        :type value: Any
        :param to: Send only to given client. When "all", event is send to all connected clients
        :type to: str | UUID
        """
        ...


