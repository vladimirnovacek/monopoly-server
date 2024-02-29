import itertools
from itertools import cycle
import random
from types import NoneType
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
        self.misc: Misc = {}
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

    def update(self, *, section: str, item: int | str | UUID, attribute: str | None = None, value: Any) -> bool:
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
        :return: True if the value was changed
        :rtype: bool
        """
        if self.get_value(section,item, attribute) == value:  # No changes, necessary due to recursion
            return False
        if section == "fields":
            self.fields.update(item=item, attribute=attribute, value=value)
        elif section == "players":
            self.players.update(item=item, attribute=attribute, value=value)
        elif attribute is not None:
            self[section][item][attribute] = value
        else:
            self[section][item] = value
        return True

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
        if type(record["value"]) not in (bool, int, str, tuple, list, NoneType):  # objects (field type, color) convert to string
            record["value"] = str(record["value"])
        return record

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
        player_id = self.players.id_from_uuid(player_uuid)
        data.append({"section": "misc", "item": "my_id", "value": player_id})
        # Retrieve data from "fields" section
        # General board data are sent as "fields" with item == -1
        data.append({"section": "fields", "item": -1, "attribute": "lenght", "value": len(self.fields)})
        for i, field in enumerate(self.fields):
            for attribute in field:
                data.append(self.get("fields", i, attribute, getattr(field, attribute)))
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
        player_order = list(range(len(self.players)))
        random.shuffle(player_order)
        self.update(section="misc", item="player_order", value=player_order)
        self.player_order_cycler = itertools.cycle(player_order)
        self.update(section="misc", item="on_turn", value=next(self.player_order_cycler))

    def is_player_on_turn(self, player_uuid: UUID) -> bool:
        return player_uuid == self.players.uuid_from_id(self.get_value("misc", "on_turn"))

    def add_player(self, player_uuid: UUID, player_id: int):
        player = self.players.add(player_uuid, player_id)
        return player