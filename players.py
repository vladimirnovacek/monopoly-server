from typing import Any
from uuid import UUID

from interfaces import IPlayers, IPlayer


class Player(IPlayer):
    def __init__(
            self, player_uuid: UUID,  player_id: int, name: str = None,
            token: str = "", cash: int = 0, field: int = -1, ready: bool = False):
        self.player_id: int = player_id
        self.uuid: UUID = player_uuid
        self.name: str = f"Player {self.player_id + 1}" if name is None else name
        self.token: str = token
        self.cash: int = cash
        self.field: int = field
        self.ready: bool = ready
        self.in_jail: bool = False
        self.jail_turns: int = 0
        self.get_out_of_jail_cards: int = 0

    def __getitem__(self, item):
        return getattr(self, item)

    def __iter__(self):
        for attr in self.attributes:
            yield attr

    @property
    def attributes(self):
        return "player_id", "name", "token", "cash", "field", "ready"

    @property
    def attr_dict(self) -> dict[str, Any]:
        return {attr: getattr(self, attr) for attr in self.attributes}


class Players(IPlayers):
    def __init__(self):
        self._players: dict[UUID, Player] = {}

    def __getitem__(self, item: UUID | int) -> Player:
        if type(item) is UUID:
            if item in self._players:
                return self._players[item]
            raise KeyError(f"Player with uuid {item} was not found.")
        if type(item) is int:
            matching = filter(lambda player: player.player_id == item, self._players.values())
            try:
                return next(matching)
            except StopIteration:
                raise KeyError(f"Player with id {item} was not found.")
        raise AttributeError(f"{item} has to be of type UUID or int.")

    def __len__(self):
        return len(self._players)

    def __iter__(self):
        return iter(self._players)

    def update(self, item: UUID, attribute: str, value: Any) -> None:
        if not hasattr(self._players[item], attribute):
            raise AttributeError(f"Player object has no attribute {attribute}.")
        player = self._players[item]
        setattr(player, attribute, value)

    def add(self, player_uuid: UUID, player_id: int) -> Player:
        new_player = Player(player_uuid, player_id)
        self._players[new_player.uuid] = new_player
        return new_player

    def is_all_ready(self):
        return all(player.ready and player.token for player in self._players.values())

    def uuid_from_id(self, player_id: int) -> UUID:
        for player in self._players.values():
            if player.player_id == player_id:
                return player.uuid
        raise KeyError(f"Player with id {player_id} was not found.")

    def id_from_uuid(self, uuid: UUID) -> int:
        return self._players[uuid].player_id