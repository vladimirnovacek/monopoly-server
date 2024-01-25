from abc import ABC, abstractmethod
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


class Data(ABC):
    pass


class Controller(ABC):
    def __init__(self, game_data: Data):
        self.game_data: Data = game_data

    @abstractmethod
    def parse(self, message: ClientMessage):
        pass



class IServer(ABC):
    def __init__(self):
        self.server_uuid: UUID = UUID()
