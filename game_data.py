from collections.abc import Iterator
from itertools import cycle
from uuid import UUID
from typing import TypedDict, Any

import config
from board import BoardData
from interfaces import IData
from players import Players, Player


class Misc(TypedDict, total=False):
    on_turn: int
    last_roll: tuple
    players_order: list[int]
    state: str


class GameData(IData):

    def __init__(self):
        self.fields: BoardData = BoardData()
        self.players: Players = Players()
        self.misc: Misc = {"state": "pregame"}
        self._changes: list[tuple] = []
        self.player_order_cycler: cycle | None = None

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

    @property
    def on_turn(self) -> int:
        on_turn = self.get_value("misc", "on_turn")
        if on_turn is not None:
            return on_turn
        return -1

    @property
    def on_turn_uuid(self) -> UUID | None:
        try:
            return self.players.uuid_from_id(self.on_turn)
        except KeyError:
            return None

    @property
    def on_turn_player(self) -> Player | None:
        try:
            return self.players[self.on_turn]
        except KeyError:
            return None

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
            self.add_change(section, item, attribute, value)
        elif section == "players":
            self.players.update(item=item, attribute=attribute, value=value)
            self.add_change(section, item, attribute, value)
        elif section == "events":
            self.add_change(section, item, value)
        elif attribute is not None:
            self[section][item][attribute] = value
            self.add_change(section, item, attribute, value)
        else:
            self[section][item] = value
            self.add_change(section, item, value)

    def add_change(self, *args, **kwargs) -> None:
        if kwargs:
            largs = list(args)
            largs.extend(kwargs.values())
            args = tuple(largs)
        if args in self._changes or not args:
            return
        self._changes.append(args)

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
        except (KeyError, IndexError, AttributeError):
            return None

    def get(self, *args, **kwargs) -> dict | None:
        """
        Retrieves data for a specific item in a dict format that can be used by the messenger. Returns None if there
        is no such item.
        :param args:
        :param kwargs:
        :return:
        :rtype: dict | None
        """
        if kwargs:
            if "value" not in kwargs:
                kwargs["value"] = self.get_value(**kwargs)
            args = tuple(list(args) + list(kwargs.values()))
        if len(args) == 4:
            keys = ("section", "item", "attribute", "value")
        elif len(args) == 3:
            keys = ("section", "item", "value")
        else:
            return
        record = {key: value for key, value in zip(keys, args)}
        if type(record["value"]) not in (int, str, tuple):
            record["value"] = str(record["value"])
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
            if change["section"] == "players" and change["attribute"] == "possible_actions":
                change["to"] = change["item"]
            if for_client:
                if change["section"] == "players":
                    change["item"] = self.players.id_from_uuid(change["item"])
            yield change

    def get_all_for_player(self, player_uuid: UUID) -> list[dict]:
        """
        Retrieves all data for a specific player in a format that can be used by the message factory. This method is
        meant to be used when a player is connected to the server to retrieve all data at once.
        :param player_uuid: The UUID of the player.
        :type player_uuid: UUID
        :return: A list of dictionaries containing the retrieved data for the player.
        :rtype: list[dict]
        """
        data = list()
        # Following data is stored in a different location on the player's side, so it has to be reformatted.
        data.append({"section": "misc", "item": "my_uuid", "value": player_uuid})
        player_id = self.get_value("players", player_uuid, "player_id")
        data.append({"section": "misc", "item": "my_id", "value": player_id})
        # Retrieve data from "fields" section
        # General board data are sent as "fields" with item == -1
        data.append({"section": "fields", "item": -1, "attribute": "lenght", "value": len(self.fields)})
        for i, field in enumerate(self.fields):
            for attribute in field:
                data.append(self.get("fields", i, attribute, getattr(field, attribute)))
        # Retrieve data from "misc" section
        for item in self.misc:
            data.append(self.get("misc", item, self.get_value("misc", item)))
        # Retrieve data from section "players". It is done separately because
        # we don't want to send uuids of other players so we have to replace them with their ids.
        for item in self["players"]:
            player_id = self.get_value("players", item, "player_id")
            for attribute, value in self.players[item].attr_dict.items():
                date = self.get("players", item, attribute, value)
                date["item"] = player_id
                data.append(date)
        return data

    def set_initial_values(self):
        for player in self.players:
            self.update(section="players", item=player, attribute="cash", value=config.initial_cash)
            self.update(section="players", item=player, attribute="field", value=config.initial_field)

    def is_player_on_turn(self, player_uuid: UUID) -> bool:
        return player_uuid == self.players.uuid_from_id(self.get_value("misc", "on_turn"))
