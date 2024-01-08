from typing import ClassVar, Optional

from uuid import UUID

from board_description import FIELDS, FieldType


class Field:

    def __init__(self, board: "Board", field_id: int):
        self.board = board
        self.info: dict = FIELDS[field_id]
        if self.is_property():
            self.owner: Optional[UUID] = None
            if self.info["field_type"] is FieldType.STREET:
                self.houses: int = 0

    def __getattr__(self, item):
        if item in self.info:
            return self.info[item]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute {item}")

    @property
    def rent(self) -> int | None:
        if not self.is_property():
            return None
        if self.is_street():
            if 1 <= self.houses <= 4:
                rent = f"house_{self.houses}"
            elif self.houses == 5:
                rent = "hotel"
            else:
                if self.board.has_full_set(self):
                    rent ="double_rent"
                else:
                    rent = "rent"
        else:
            owned_count = self.board.get_properties_in_set_owned(self)
            rent = "rent" if owned_count == 1 else f"rent_{owned_count}"
        return getattr(self, rent)

    def set_owner(self, player: UUID) -> None:
        self.owner = player

    def get_info(self) -> dict:
        info = dict()
        info.update(dict(self.info))
        info["index"] = self.index
        info["type"] = self.field_type.name.lower()
        if bool(self.field_type & FieldType.PROPERTY):
            info["owner"] = self.owner
            info["current_rent"] = self.rent
            if self.field_type is FieldType.STREET:
                info["color"] = self.info["color"].name.lower()
                info["houses"] = self.houses
        return info

    def is_tax(self):
        return self.field_type is FieldType.TAX

    def is_chance_cc_card(self) -> bool:
        return bool(self.field_type & FieldType.CARD)

    def is_property(self) -> bool:
        return bool(self.field_type & FieldType.PROPERTY)

    def is_street(self) -> bool:
        return bool(self.field_type & FieldType.STREET)

    def is_go_to_jail(self) -> bool:
        return bool(self.field_type & FieldType.GO_TO_JAIL)

    def is_nonactive(self) -> bool:
        return bool(self.field_type & FieldType.NONACTIVE)


class Board:
    # počet polí na hracím plánu
    LENGHT: ClassVar[int] = 40
    """ Lenght of the board. """
    JAIL: ClassVar[int] = 40
    """ Index of the jail field. It has to be out of the range of 0 - LENGHT """
    JUST_VISITING: ClassVar[int] = 10
    """ Index of the just visiting field. """
    GO_CASH: ClassVar[int] = 200
    """ Cash that the player recieves when they land on GO. """

    def __init__(self, game = None):
        self.game = game
        self.fields: list[Field] = list()
        self._generate_fields()
        self.lenght: int = self.LENGHT
        self.jail: int = self.JAIL
        self.just_visiting: int = self.JUST_VISITING
        self.go_cash: int = self.GO_CASH

    @property
    def streets(self) -> list[Field]:
        return list(filter(
            lambda field: field.field_type == FieldType.STREET, self.fields
        ))

    def player_landed(self, field: int):
        self.game.set_changes(section="field", value=self.get_field_info(field))
        if self.is_card(field):
            self.game.take_card()

    def _generate_fields(self) -> None:
        for i in range(len(FIELDS)):
            self.fields.append(Field(self, i))

    def get_properties_in_set_owned(self, field: Field) -> int:
        owner = field.owner
        owned_properties = filter(lambda prop: prop.index in field.full_set and prop.owner == owner, self.fields)
        return len(list(owned_properties))

    def has_full_set(self, field: Field) -> bool:
        owner = field.owner
        streets_in_set = filter(
            lambda street: street.index in field.full_set, self.fields)
        if all(street.owner == owner for street in streets_in_set):
            return True
        else:
            return False

    def get_field(self, field: int) -> Field:
        return self.fields[field]

    def get_field_info(self, field: int):
        return self.get_field(field).get_info()

    def get_field_type(self, field: int) -> FieldType:
        return self.fields[field].field_type

    def is_chance(self, field: int) -> bool:
        return self.get_field_type(field) is FieldType.CHANCE

    def is_cc(self, field: int) -> bool:
        return self.get_field_type(field) is FieldType.CC

    def is_card(self, field: int) -> bool:
        return bool(self.get_field_type(field) & FieldType.CARD)

    def is_street(self, field: int) -> bool:
        return self.get_field_type(field) is FieldType.STREET

    def is_railroad(self, field: int) -> bool:
        return self.get_field_type(field) is FieldType.RAILROAD

    def is_utility(self, field: int) -> bool:
        return self.get_field_type(field) is FieldType.UTILITY

    def is_tax(self, field: int) -> bool:
        return self.get_field_type(field) is FieldType.TAX

    def is_property(self, field: int) -> bool:
        return bool(self.get_field_type(field) & FieldType.PROPERTY)

    def is_go_to_jail(self, field: int) -> bool:
        return self.get_field(field).is_go_to_jail()

    def is_nonactive(self, field: int) -> bool:
        return self.get_field(field).is_nonactive()
