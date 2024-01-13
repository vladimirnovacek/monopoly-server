from collections.abc import Iterator
from itertools import cycle
from uuid import UUID
from typing import TypedDict, Any, Iterable

import config
from board import BoardData


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
    players_order: list[int]
    state: str


class GameData:

    def __init__(self):
        self.fields: BoardData = BoardData()
        self.players: dict[UUID, Player] = {}
        self.misc: Misc = {"state": "pregame"}
        self.events = {}
        self._changes: set[tuple] = set()
        self.player_order_cycler: cycle | None = None

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

    def add_player(self, player_uuid: UUID, player_id):
        new_player = Player(
            player_id=player_id,
            name=f"Player {player_id + 1}",
            token="",
            cash=0,
            field_id=-1,
            ready=False
        )
        self.players[player_uuid] = Player()
        for key, value in new_player.items():
            self.update(section="players", item=player_uuid, attribute=key, value=value)
        return {player_uuid: self.players[player_uuid]}

    def update(self, *, section: str, item: str | UUID, attribute: str | None = None, value: Any) -> None:
        """
        Updates the value of a specific item.
        :param section:
        :type section: str
        :param item:
        :type item: str | UUID
        :param attribute:
        :type attribute: str | None
        :param value:
        :type value: Any
        :return:
        :rtype: None
        """
        if self.get_value(section,item, attribute) == value:  # No changes, necessary due to recursion
            return
        if section == "fields":
            self.fields.update(item=item, attribute=attribute, value=value)
            self._changes.add((section, item, attribute, value))
        elif attribute is not None:
            self[section][item][attribute] = value
            self._changes.add((section, item, attribute))
        else:
            self[section][item] = value
            self._changes.add((section, item))

    def get_value(self, section: str, item: str | int | UUID, attribute: str | None = None) -> Any:
        """
        Retrieves only the value for a specific item. Returns None if there is no such item.
        :param section:
        :type section: str
        :param item:
        :type item: str | UUID
        :param attribute:
        :type attribute: str | None
        :return:
        :rtype: Any
        """
        try:
            return self[section][item][attribute] if attribute else self[section][item]
        except (KeyError, IndexError):
            return None

    def get(self, section: str, item: str | int | UUID, attribute: str | None = None, value: Any = None) -> dict:
        """
        Retrieves data for a specific item in a format that can be used by the messenger.
        :param section:
        :type section: str
        :param item:
        :type item: str | UUID
        :param attribute:
        :type attribute: str | None
        :param value:
        :type value: Any
        :return:
        :rtype: dict
        """
        keys = (section, item, attribute) if attribute else (section, item)
        if not value:
            value = self.get_value(*keys)
        if type(value) not in (int, str, tuple):
            value = str(value)
        record = {"section": section, "item": item, "value": value}
        if attribute:
            record["attribute"] = attribute
        return record

    def get_changes(self, for_client: bool = True) -> Iterator[dict]:
        """
        Retrieves data for all recently altered items in a format that can be used by the messenger. Method
        returns an iterator that can be used in a for loop.
        :param for_client: When changes are meant to be sent to a client, uuid has to be replaced with id.
        Default: True.
        :type for_client: bool
        :return:
        :rtype: Iterator[tuple[str, str | UUID, str | None]]
        """
        while self._changes:
            change = self.get(*self._changes.pop())
            if change["section"] == "events":
                del self.events[change["item"]]
            if for_client:
                if change["section"] == "players":
                    change["item"] = self.id_from_uuid(change["item"])
            yield change

    def get_all_for_player(self, player_uuid: UUID) -> list[dict]:
        """ TODO change docstring format
        Retrieves all data for a specific player in a format that can be used by the message factory.
        Args:
            player_uuid (uuid.UUID): The UUID of the player.
        Returns:
            list[dict]: A list of dictionaries containing the retrieved data for the player.
        """
        data = list()
        # Following data is stored in a different location on the player's side.
        data.append({"section": "misc", "item": "my_uuid", "value": player_uuid})
        player_id = self.get_value("players", player_uuid, "player_id")
        data.append({"section": "misc", "item": "my_id", "value": player_id})
        # Retrieve data from sections "fields" and "misc".
        data.append({"section": "fields", "item": -1, "attribute": "lenght", "value": len(self.fields)})
        for i, field in enumerate(self.fields):
            for attribute in field:
                data.append(self.get("fields", i, attribute, getattr(field, attribute)))
        for item in self.misc:
            data.append(self.get("misc", item))
        # Retrieve data from section "players". It is done separately because
        # we don't want to send uuids of other players.
        for item in self["players"]:
            player_id = self["players"][item]["player_id"]
            for attribute in self["players"][item]:
                value = self.get_value("players", item, attribute)
                data.append({"section": "players", "item": player_id, "attribute": attribute, "value": value})
        return data

    def get_all(self) -> set[dict]:
        data = set()
        for section in ("fields", "players", "misc"):
            for item in self[section]:
                if isinstance(Iterable, self[section][item]):
                    for attribute in self[section][item]:
                        value = self.get(section, item, attribute)
                        data.add({"section": section, "item": item, "attribute": attribute, "value": value})
                else:
                    value = self.get(section, item)
                    data.add({"section": section, "item": item, "value": value})
        return data

    def is_all_players_ready(self):
        return all([player["ready"] and player["token"] for player in self.players.values()])

    def set_initial_values(self):
        for player in self.players:
            self.update(section="players", item=player, attribute="cash", value=config.initial_cash)
            self.update(section="players", item=player, attribute="field", value=config.initial_field)

    def id_from_uuid(self, player_uuid: UUID) -> int:
        return self.players[player_uuid]["player_id"]

    def uuid_from_id(self, player_id: int) -> UUID:
        for player_uuid, player in self.players.items():
            if player["player_id"] == player_id:
                return player_uuid

    def is_player_on_turn(self, player_uuid: UUID) -> bool:
        return player_uuid == self.uuid_from_id(self.get_value("misc", "on_turn"))