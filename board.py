# -*- tests-case-name: tests.test_board -*-
from typing import ClassVar, Optional, Any

from uuid import UUID

from board_description import FIELDS, FieldType, FieldRecord
from interfaces import IFields, IField


class Field(IField):
    """
    Represents a field on the board. The data of the fields are defined in board_description.py
    """

    def __init__(self, board: "BoardData", field_id: int):
        self.id: int = field_id
        """ The id of the field """
        self.board = board
        """ The board this field belongs to """
        self.info: dict = FIELDS[field_id]
        """ The immutable data of the field """
        if self.is_property():
            self.owner: Optional[UUID] = None
            """ The owner of the field. None if the field is not owned """
            self.mortgage: bool = False
            """ True if the field is mortgaged """
            if self.type is FieldType.STREET:
                self.houses: int = 0
                """ The number of houses built on the field """

    def __getattr__(self, item):
        if item in self.info:
            return self.info[item]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute {item}")

    def __getitem__(self, item):
        return self.full_info[item]
    def __iter__(self):
        return iter(self.full_info)

    @property
    def full_info(self) -> dict:
        """
        Returns the full info of the field including mutable and immutable data.
        :return: The full info of the field
        :rtype: dict
        """
        info = self.info.copy()
        for attr in ["owner", "mortgage", "houses"]:
            if hasattr(self, attr):
                info[attr] = getattr(self, attr)
        return info

    @property
    def rent(self) -> int | None:
        """
        Returns the rent of the field. For utilities it returns just a multiplier that has to be multiplied with
        the dice roll to get the actual rent.
        :return: The actual rent. None if the field is not a property.
        :rtype: int | None
        """
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
        return self[rent]

    def get_info(self) -> dict:
        """
        Returns the info of the field with object values replaced with strings.
        :return:
        :rtype:
        """
        info = self.full_info
        info["type"] = self.field_type.name.lower()  # substitute FieldType with string
        if "color" in info:
            info["color"] = self.info["color"].name.lower()  # substitute Color with string
        return info

    def is_tax(self) -> bool:
        """
        Returns True if the field type is TAX.
        :return:
        :rtype:
        """
        return self.type is FieldType.TAX

    def is_chance_cc_card(self) -> bool:
        """
        Returns True if the field type is CHANCE or CC
        :return:
        :rtype:
        """
        return bool(self.type & FieldType.CARD)

    def is_property(self) -> bool:
        """
        Returns True if the field type is PROPERTY
        :return:
        :rtype:
        """
        return bool(self.type & FieldType.PROPERTY)

    def is_street(self) -> bool:
        """
        Returns True if the field type is STREET
        :return:
        :rtype:
        """
        return bool(self.type & FieldType.STREET)

    def is_go_to_jail(self) -> bool:
        """
        Returns True if the field type is GO_TO_JAIL
        :return:
        :rtype:
        """
        return bool(self.type & FieldType.GO_TO_JAIL)

    def is_nonactive(self) -> bool:
        """
        Returns True if the field type is NONACTIVE
        :return:
        :rtype:
        """
        return bool(self.type & FieldType.NONACTIVE)


class BoardData(IFields):
    """
    BoardData represents the immutable data of the board and contains the fields.
    """
    LENGHT: ClassVar[int] = 40
    """ Lenght of the board. The Jail and Just Visiting fields are counted as one field. """
    JAIL: ClassVar[int] = 40
    """ Index of the jail field. It has to be out of the range of 0 - LENGHT """
    JUST_VISITING: ClassVar[int] = 10
    """ Index of the just visiting field. """
    GO_CASH: ClassVar[int] = 200
    """ Cash that the player recieves when they pass GO. """

    def __init__(self):
        self.fields: list[Field] = list()
        """ List of all fields on the board. """
        self._generate_fields()
        self.lenght: int = self.LENGHT
        """ Lenght of the board. The Jail and Just Visiting fields are counted as one field. """
        self.jail: int = self.JAIL
        """ Index of the jail field. It has to be out of the range of 0 - LENGHT """
        self.just_visiting: int = self.JUST_VISITING
        """ Index of the just visiting field. """
        self.go_cash: int = self.GO_CASH
        """ Cash that the player recieves when they pass GO. """

    def __len__(self):
        return len(self.fields)

    def __iter__(self):
        return iter(self.fields)

    def __getitem__(self, item):
        return self.fields[item]

    @property
    def streets(self) -> set[Field]:
        """
        Returns a list of all streets on the board.
        :return: A list of all streets on the board.
        :rtype: list[Field]
        """
        return set(filter(
            lambda field: field.type == FieldType.STREET, self.fields
        ))

    def count_houses(self, player_uuid: UUID) -> tuple[int, int]:
        """
        Returns the number of houses and hotels on the board.
        :return: The number of houses and hotels on the board.
        :rtype: tuple[int, int]
        """
        houses = 0
        hotels = 0
        for field in self.streets:
            if field.owner != player_uuid:
                continue
            if field.houses == 5:
                hotels += 1
            else:
                houses += field.houses
        return houses, hotels

    def update(self, *, item: str, attribute: str, value: Any) -> None:
        """
        Updates a field on the board.
        :param item: The numeric index of the field to update. Do not confuse it with the string index.
        :type item: str
        :param attribute: The name of the attribute to update
        :type attribute: str
        :param value: The new value
        :type value: Any
        """
        field = self.fields[int(item)]
        if attribute not in ("owner", "houses", "mortgage") or not hasattr(field, attribute):
            raise AttributeError(f"Attribute invalid or immutable: {attribute}")
        setattr(field, attribute, value)

    def get_properties_in_set_owned(self, field: Field) -> int:
        """
        Returns the number of properties in a set that are owned by the same player.
        :param field:
        :type field:
        :return:
        :rtype:
        """
        owner = field.owner
        owned_properties = filter(lambda prop: prop.index in field.full_set and prop.owner == owner, self.fields)
        return len(list(owned_properties))

    def has_full_set(self, field: Field) -> bool:
        """
        Returns True if all streets in the set of the field given as parameter are owned by the same player.
        :param field:
        :type field:Field
        :return:
        :rtype: bool
        """
        owner = field.owner
        streets_in_set = filter(
            lambda street: street.index in field.full_set, self.fields)
        if all(street.owner == owner for street in streets_in_set):
            return True
        else:
            return False

    def get_field(self, field_id: int) -> Field:
        """
        Returns a field by its index.
        :param field_id:
        :type field_id: int
        :return:
        :rtype: Field
        """
        return self.fields[field_id]

    def advance_field_id(self, original_field: int, steps: int) -> int:
        """
        Counts a field_id where a token lands when it starts on the `original_field` and moves `steps` steps.
        :param original_field: Field_id of the field where the token starts.
        :type original_field: int
        :param steps: Number of steps the token moves.
        :type steps: int
        :return: Field_id of the field where the token lands.
        :rtype: int
        """
        return (original_field + steps) % self.lenght

    def _generate_fields(self, fields: list[FieldRecord] = None) -> None:
        """
        Generates a list of all fields on the board. If no fields are given, they are taken
        from the board_description.FIELDS constant.
        """
        if fields is None:
            fields = FIELDS
        for i in range(len(fields)):
            self.fields.append(Field(self, i))
