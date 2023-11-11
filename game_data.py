import uuid
from typing import TypedDict, Any, overload, Iterable


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


class GameData:

    def __init__(self):
        self.fields: dict[int, Field] = {}
        self.players: dict[uuid.UUID, Player] = {}
        self.misc: Misc = {}

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"

    def add_player(self, player_uuid, player_id):
        self.players[player_uuid] = Player(
            player_id=player_id,
            name=f"Player {player_id}",
            token="",
            cash=0,
            field_id=-1,
            ready=False
        )
        print(self)

    @overload
    def update(self, *, section: str, item: str | int, value: Any):
        ...

    @overload
    def update(self, *, section: str, item: str | int, attribute: str, value: Any):
        ...

    def update(self, *, section: str, item: str | int, attribute: str | None = None, value: Any):
        if attribute is not None:
            self[section][item][attribute] = value
        else:
            self[section][item] = value
        print(self)

    def select(self, keys: Iterable):
        value = self
        for key in keys:
            value = value[key]
        return value

    def get_value(self, section: str, item: str | uuid.UUID, attribute: str | None = None) -> Any:
        return self[section][item][attribute] if attribute else self[section][item]

    def get(self, section: str, item: str | uuid.UUID, attribute: str | None = None) -> dict:
        keys = (section, item, attribute) if attribute else (section, item)
        record = {"section": section, "item": item, "value": self.select(keys)}
        if attribute:
            record["attribute"] = attribute
        return record

    def get_all_for_player(self, player_uuid: uuid.UUID) -> list[dict]:
        """
        Retrieves all data for a specific player in a format that can be used by the message factory.
        Args:
            player_uuid (uuid.UUID): The UUID of the player.
        Returns:
            list[dict]: A list of dictionaries containing the retrieved data for the player.
        """
        data = list()
        # Following data is stored in a different location on the player's side.
        data.append({"section": "misc", "item": "my_uuid", "value": str(player_uuid)})
        player_id = self.get_value("players", player_uuid, "player_id")
        data.append({"section": "misc", "item": "my_id", "value": player_id})
        # Retrieve data from sections "fields" and "misc".
        for section in ("fields", "misc"):
            for item in self[section]:
                # In "misc", item doesn't contain a dictionary of attributes, but values.
                if isinstance(Iterable, self[section][item]):
                    for attribute in self[section][item]:
                        value = self.get_value(section, item, attribute)
                        data.append({"section": section, "item": item, "attribute": attribute, "value": value})
                else:
                    value = self.get(section, item)
                    data.append({"section": section, "item": item, "value": value})
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