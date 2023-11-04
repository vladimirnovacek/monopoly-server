from typing import Protocol, Self


class MessageFactory(Protocol):
    def add(self, **kwargs) -> Self:
        ...

    def get(self) -> bytes:
        ...
