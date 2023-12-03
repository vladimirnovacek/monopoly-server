from typing import Protocol, Self, TypedDict
from uuid import UUID


class ClientMessage(TypedDict):
    my_uuid: UUID
    action: str
    parameters: dict


class Observer(Protocol):
    def update(self, section, item, attribute_or_value, value):
        ...


class MessageFactory(Protocol):
    def add(self, **kwargs) -> Self:
        ...

    def get(self) -> bytes:
        ...


class Parser(Protocol):
    def get_initial_message(self, player_uuid):
        ...

    def parse(self, data):
        ...
