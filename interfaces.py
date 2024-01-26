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
    ...

class IPlayers(IDataUnit, Sized, Iterable):
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


class IFields(IDataUnit):
    JAIL: ClassVar[int]

    @abstractmethod
    def get_field(self, field_id: int) -> IField:
        ...


class IData(ABC):
    players: IPlayers
    fields: IFields
    player_order_cycler: Iterator

    @abstractmethod
    @property
    def on_turn_uuid(self) -> UUID:
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


class IDice(ABC):

    @abstractmethod
    @property
    def triple_double(self) -> bool:
        ...

    @abstractmethod
    def roll(self) -> IRoll:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...


class IController(ABC):
    dice: IDice
    game_data: IData
    message: IMessenger
    server_uuid: UUID

    @abstractmethod
    def __init__(self, game_data: IData) -> None:
        self.game_data: IData = game_data

    @abstractmethod
    def parse(self, message: ClientMessage) -> None:
        ...
