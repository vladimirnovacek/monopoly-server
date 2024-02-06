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
    def add(self, **kwargs) -> Self:
        ...

    @abstractmethod
    def get(self, player_uuid: UUID) -> bytes:
        ...

    @abstractmethod
    def send(self, player_uuid: UUID) -> None:
        ...

    @abstractmethod
    def broadcast(self) -> None:
        ...

    @abstractmethod
    def receive(self, message: ClientMessage | bytes) -> None:
        ...

    @abstractmethod
    def set_server(self, server: IServer) -> None:
        ...


class IDataUnit(ABC):
    ...


class IPlayer(ABC):
    uuid: UUID
    field: int
    in_jail: bool
    jail_turns: int
    get_out_of_jail_cards: int

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
    type: FieldType
    owner: Optional[UUID]
    price: int
    rent: int
    tax: int


class IFields(IDataUnit):
    GO: ClassVar[int]
    JAIL: ClassVar[int]
    JUST_VISITING: ClassVar[int]

    @abstractmethod
    def get_field(self, field_id: int) -> IField:
        ...

    @abstractmethod
    def count_houses(self, player_uuid: UUID) -> int:
        ...

    @abstractmethod
    def advance_field_id(self, original_field: int, steps: int) -> int:
        ...

class IData(ABC):
    players: IPlayers
    fields: IFields
    player_order_cycler: Iterator


    @property
    @abstractmethod
    def on_turn_uuid(self) -> UUID:
        ...

    @property
    @abstractmethod
    def on_turn_player(self) -> IPlayer:
        ...

    @abstractmethod
    def __getitem__(self, item):
        ...

    @abstractmethod
    def get_all_for_player(self, player_uuid: UUID) -> list[dict]:
        ...

    @abstractmethod
    def get_changes(self) -> Iterator[dict]:
        ...

    @abstractmethod
    def get_value(self, section: str, item: str | UUID, attribute: str | None = None) -> Any:
        ...

    @abstractmethod
    def set_initial_values(self) -> None:
        ...

    @abstractmethod
    def update(self, *, section: str, item: str | UUID, attribute: str | None = None, value: Any) -> None:
        ...

    @abstractmethod
    def is_player_on_turn(self, player_uuid: UUID) -> bool:
        ...


class IRoll(ABC):
    @abstractmethod
    def get(self) -> tuple[int, ...]:
        ...

    @abstractmethod
    def sum(self) -> int:
        ...

    @abstractmethod
    def is_double(self) -> bool:
        ...

class IDice(ABC):
    last_roll: IRoll | None

    @property
    @abstractmethod
    def triple_double(self) -> bool:
        ...

    @abstractmethod
    def roll(self, register: bool = True) -> IRoll:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...


class ICard(ABC):
    type: str
    ends_turn: bool
    special_rent: str

    @abstractmethod
    def apply(self, controller) -> None:
        ...

class ICardDeck(ABC):

    @abstractmethod
    def draw(self) -> ICard:
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
    def __init__(self, game_data: IData) -> None:
        self.gd: IData = game_data

    @abstractmethod
    def parse(self, message: ClientMessage) -> None:
        ...

    @abstractmethod
    def roll(self, register: bool = True) -> IRoll:
        ...

    @abstractmethod
    def pay(self, rent: int, payer_uuid: UUID, payee_uuid: UUID | None = None) -> None:
        ...

    @abstractmethod
    def collect(self, payment: int, player_uuid: UUID) -> None:
        ...

    @abstractmethod
    def move_to(self, field_id: int, player_uuid: UUID | None = None, check_pass_go: bool = False) -> None:
        ...

    @abstractmethod
    def move_by(self, fields: int, player_uuid: UUID | None = None, check_pass_go: bool = True) -> None:
        ...
