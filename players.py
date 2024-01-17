from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from game_data import GameData

class Player:
    def __init__(
            self, game_data: "GameData",player_uuid: UUID,  player_id: int, name: str = None,
            token: str = "", cash: int = 0, field: int = -1, ready: bool = False):
        self.gd = game_data
        self.player_id: int = player_id
        self.player_uuid: UUID = player_uuid
        self.name: str = f"Player {self.player_id + 1}" if name is None else name
        self.token = token
        self.cash = cash
        self.field = field
        self.ready = ready

    def __getitem__(self, item):
        return getattr(self, item)

    @property
    def attributes(self):
        return "player_id", "name", "token", "cash", "field", "ready"


class Players:
    def __init__(self, game_data: "GameData"):
        self.gd: GameData = game_data
        self._players: dict[UUID, Player] = {}

    def __iter__(self):
        return iter(self._players)

    def update(self, item: UUID, attribute: str, value: Any) -> None:
        player = self._players[item]
        setattr(player, attribute, value)

    def add_player(self, player_uuid: UUID, player_id: int):
        new_player = Player(self.gd, player_uuid, player_id)
        self._players[new_player.player_uuid] = new_player
        for attr in new_player.attributes:
            self.gd.add_change("players", new_player.player_uuid, attr, getattr(new_player, attr))

    def is_all_ready(self):
        return all(player.ready and player.token for player in self._players.values())

    def uuid_from_id(self, player_id: int) -> UUID:
        for player in self._players.values():
            if player.player_id == player_id:
                return player.player_uuid
        raise KeyError(f"Player with id {player_id} was not found.")

    def id_from_uuid(self, uuid: UUID) -> int:
        return self._players[uuid].player_id