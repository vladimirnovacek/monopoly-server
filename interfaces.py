from typing import Protocol, Self


class Observer(Protocol):
    def update(self, section, item, attribute_or_value, value):
        ...


class MessageFactory(Protocol):
    def add(self, **kwargs) -> Self:
        ...

    def get(self) -> bytes:
        ...
