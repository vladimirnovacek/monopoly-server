
from typing import TypedDict, Any, overload

from interfaces import Observer


class Field(TypedDict, total=False):
    field_id: int
    owner: int
    houses: int
    mortgage: bool


class Player(TypedDict, total=False):
    player_id: int
    name: str
    token: str
    cash: int
    field_id: int
    ready: bool


class Misc(TypedDict, total=False):
    on_turn: int
    last_roll: tuple
    my_id: int
    my_uuid: str
    players_order: list[int]


class GameData:

    def __init__(self):
        self.observers: list[Observer] = []
        self.fields: dict[int, Field] = {}
        self.players: list[Player] = [
            {"player_id": 0, "name": "", "token": "", "cash": 0, "field_id": -1, "ready": False},
            {"player_id": 1, "name": "", "token": "", "cash": 0, "field_id": -1, "ready": False},
            {"player_id": 2, "name": "", "token": "", "cash": 0, "field_id": -1, "ready": False},
            {"player_id": 3, "name": "", "token": "", "cash": 0, "field_id": -1, "ready": False}
        ]
        self.misc: Misc = {
            "my_uuid": None
        }

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

    def register(self, observer: Observer):
        self.observers.append(observer)

    @overload
    def update(self, *, section: str, item: str | int, value: Any):
        ...

    @overload
    def update(self, *, section: str, item: str | int, attribute: str, value: Any):
        ...

    def update(self, *, section: str, item: str | int, attribute: str | Any = None, value: Any):
        for observer in self.observers:
            observer.update(section, item, attribute, value)
        if attribute is not None:
            self[section][item][attribute] = value
        else:
            self[section][item] = value
        print(self)


'''
{"jmeno":
    {
        "player_id": 0,
        "name": "jmeno",
        "token": "car",
        "
    }
}
'''