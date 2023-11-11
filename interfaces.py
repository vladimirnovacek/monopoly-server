from typing import Protocol, Self, overload


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
