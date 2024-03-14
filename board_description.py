
import typing
from enum import Enum, auto, Flag


class FieldType(Flag):
    """
    FieldType represents the type of a field. Some of the field types represent a combination of other field types.
    """
    STREET = auto()
    CC = auto()
    CHANCE = auto()
    RAILROAD = auto()
    UTILITY = auto()
    JAIL = auto()
    GO_TO_JAIL = auto()
    GO = auto()
    FREE_PARKING = auto()
    JUST_VISITING = auto()
    TAX = auto()
    PROPERTY = STREET | RAILROAD | UTILITY
    """ Property field types can be one of these: STREET, RAILROAD, UTILITY. """
    CARD = CC | CHANCE
    """ Card field types can be one of these: CC, CHANCE. """
    NONACTIVE = GO | JUST_VISITING | FREE_PARKING
    """ Nonactive field types can be one of these: GO, JUST_VISITING, FREE_PARKING. """

    def __str__(self):
        return self.name.lower()

class StreetColor(Enum):
    """ StreetColor represents the color of a street. """
    BROWN = "brown"
    LBLUE = "lblue"
    PURPLE = "purple"
    ORANGE = "orange"
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    DBLUE = "dblue"

    def __str__(self):
        return self.value


class FieldRecord(typing.TypedDict):
    """
    FieldRecords are used in a list of fields.
    """
    index: str
    type: FieldType


FIELDS: list[FieldRecord] = [
    {
        "index": "go",
        "type": FieldType.GO,
        "name": "Go"
    },  # 0
    {
        "index": "brown_1",
        "type": FieldType.STREET,
        "name": "Old Kent Road",
        "color": StreetColor.BROWN,
        "full_set": ("brown_1", "brown_2"),
        "price": 60,
        "rent": 2,
        "double_rent": 4,
        "house_1": 10,
        "house_2": 30,
        "house_3": 90,
        "house_4": 160,
        "hotel": 250,
        "house_price": 50,
        "hotel_price": 50,
        "mortgage_value": 30,
        "unmortgage_price": 33
    },  # 1
    {
        "index": "cc_1",
        "type": FieldType.CC,
        "name": "Community Chest",
    },  # 2
    {
        "index": "brown_2",
        "type": FieldType.STREET,
        "name": "Whitechapel Road",
        "color": StreetColor.BROWN,
        "full_set": ("brown_1", "brown_2"),
        "price": 60,
        "rent": 4,
        "double_rent": 8,
        "house_1": 20,
        "house_2": 60,
        "house_3": 180,
        "house_4": 320,
        "hotel": 450,
        "house_price": 50,
        "hotel_price": 50,
        "mortgage_value": 30,
        "unmortgage_price": 33
    },  # 3
    {
        "index": "tax_1",
        "type": FieldType.TAX,
        "name": "Income Tax",
        "tax": 200
    },  # 4
    {
        "index": "railroad_1",
        "type": FieldType.RAILROAD,
        "name": "Kings Cross Station",
        "full_set": ("railroad_1", "railroad_2", "railroad_3", "railroad_4"),
        "price": 200,
        "rent": 25,
        "rent_2": 50,
        "rent_3": 100,
        "rent_4": 200,
        "mortgage_value": 100,
        "unmortgage_price": 110
    },  # 5
    {
        "index": "light_blue_1",
        "type": FieldType.STREET,
        "name": "The Angel, Islington",
        "color": StreetColor.LBLUE,
        "full_set": ("light_blue_1", "light_blue_2", "light_blue_3"),
        "price": 100,
        "rent": 6,
        "double_rent": 12,
        "house_1": 30,
        "house_2": 90,
        "house_3": 270,
        "house_4": 400,
        "hotel": 550,
        "house_price": 50,
        "hotel_price": 50,
        "mortgage_value": 50,
        "unmortgage_price": 55
    },  # 6
    {
        "index": "chance_1",
        "type": FieldType.CHANCE,
        "name": "Chance",
    },  # 7
    {
        "index": "light_blue_2",
        "type": FieldType.STREET,
        "name": "Euston Road",
        "color": StreetColor.LBLUE,
        "full_set": ("light_blue_1", "light_blue_2", "light_blue_3"),
        "price": 100,
        "rent": 6,
        "double_rent": 12,
        "house_1": 30,
        "house_2": 90,
        "house_3": 270,
        "house_4": 400,
        "hotel": 550,
        "house_price": 50,
        "hotel_price": 50,
        "mortgage_value": 50,
        "unmortgage_price": 55
    },  # 8
    {
        "index": "light_blue_3",
        "type": FieldType.STREET,
        "name": "Pentonville Road",
        "color": StreetColor.LBLUE,
        "full_set": ("light_blue_1", "light_blue_2", "light_blue_3"),
        "price": 120,
        "rent": 8,
        "double_rent": 16,
        "house_1": 40,
        "house_2": 100,
        "house_3": 300,
        "house_4": 450,
        "hotel": 600,
        "house_price": 50,
        "hotel_price": 50,
        "mortgage_value": 60,
        "unmortgage_price": 66
    },  # 9
    {
        "index": "just_visiting",
        "type": FieldType.JUST_VISITING,
        "name": "Just Visiting",
    },  # 10
    {
        "index": "purple_1",
        "type": FieldType.STREET,
        "name": "Pall Mall",
        "color": StreetColor.PURPLE,
        "full_set": ("purple_1", "purple_2", "purple_3"),
        "price": 140,
        "rent": 10,
        "double_rent": 20,
        "house_1": 50,
        "house_2": 150,
        "house_3": 450,
        "house_4": 625,
        "hotel": 750,
        "house_price": 100,
        "hotel_price": 100,
        "mortgage_value": 70,
        "unmortgage_price": 77
    },  # 11
    {
        "index": "utility_1",
        "type": FieldType.UTILITY,
        "name": "Electric Company",
        "full_set": ("utility_1", "utility_2"),
        "price": 150,
        "rent": 4,
        "rent_2": 10,
        "mortgage_value": 75,
        "unmortgage_price": 83
    },  # 12
    {
        "index": "purple_2",
        "type": FieldType.STREET,
        "name": "Whitehall",
        "color": StreetColor.PURPLE,
        "full_set": ("purple_1", "purple_2", "purple_3"),
        "price": 140,
        "rent": 10,
        "double_rent": 20,
        "house_1": 50,
        "house_2": 150,
        "house_3": 450,
        "house_4": 625,
        "hotel": 750,
        "house_price": 100,
        "hotel_price": 100,
        "mortgage_value": 70,
        "unmortgage_price": 77
    },  # 13
    {
        "index": "purple_3",
        "type": FieldType.STREET,
        "name": "Northumbld Avenue",
        "color": StreetColor.PURPLE,
        "full_set": ("purple_1", "purple_2", "purple_3"),
        "price": 160,
        "rent": 12,
        "double_rent": 24,
        "house_1": 60,
        "house_2": 180,
        "house_3": 500,
        "house_4": 700,
        "hotel": 900,
        "house_price": 100,
        "hotel_price": 100,
        "mortgage_value": 80,
        "unmortgage_price": 88
    },  # 14
    {
        "index": "railroad_2",
        "type": FieldType.RAILROAD,
        "name": "Marylebone Station",
        "full_set": ("railroad_1", "railroad_2", "railroad_3", "railroad_4"),
        "price": 200,
        "rent": 25,
        "rent_2": 50,
        "rent_3": 100,
        "rent_4": 200,
        "mortgage_value": 100,
        "unmortgage_price": 110
    },  # 15
    {
        "index": "orange_1",
        "type": FieldType.STREET,
        "name": "Bow Street",
        "color": StreetColor.ORANGE,
        "full_set": ("orange_1", "orange_2", "orange_3"),
        "price": 180,
        "rent": 14,
        "double_rent": 28,
        "house_1": 70,
        "house_2": 200,
        "house_3": 550,
        "house_4": 750,
        "hotel": 950,
        "house_price": 100,
        "hotel_price": 100,
        "mortgage_value": 90,
        "unmortgage_price": 99
    },  # 16
    {
        "index": "cc_2",
        "type": FieldType.CC,
        "name": "Community Chest"
    },  # 17
    {
        "index": "orange_2",
        "type": FieldType.STREET,
        "name": "Marlborough Street",
        "color": StreetColor.ORANGE,
        "full_set": ("orange_1", "orange_2", "orange_3"),
        "price": 180,
        "rent": 14,
        "double_rent": 28,
        "house_1": 70,
        "house_2": 200,
        "house_3": 550,
        "house_4": 750,
        "hotel": 950,
        "house_price": 100,
        "hotel_price": 100,
        "mortgage_value": 90,
        "unmortgage_price": 99
    },  # 18
    {
        "index": "orange_3",
        "type": FieldType.STREET,
        "name": "Vine Street",
        "color": StreetColor.ORANGE,
        "full_set": ("orange_1", "orange_2", "orange_3"),
        "price": 200,
        "rent": 16,
        "double_rent": 32,
        "house_1": 80,
        "house_2": 220,
        "house_3": 600,
        "house_4": 800,
        "hotel": 1000,
        "house_price": 100,
        "hotel_price": 100,
        "mortgage_value": 100,
        "unmortgage_price": 110
    },  # 19
    {
        "index": "free_parking",
        "type": FieldType.FREE_PARKING,
        "name": "Free Parking"
    },  # 20
    {
        "index": "red_1",
        "type": FieldType.STREET,
        "name": "Strand",
        "color": StreetColor.RED,
        "full_set": ("red_1", "red_2", "red_3"),
        "price": 220,
        "rent": 18,
        "double_rent": 36,
        "house_1": 90,
        "house_2": 250,
        "house_3": 700,
        "house_4": 875,
        "hotel": 1050,
        "house_price": 150,
        "hotel_price": 150,
        "mortgage_value": 110,
        "unmortgage_price": 121
    },  # 21
    {
        "index": "chance_2",
        "type": FieldType.CHANCE,
        "name": "Chance"
    },  # 22
    {
        "index": "red_2",
        "type": FieldType.STREET,
        "name": "Fleet Street",
        "color": StreetColor.RED,
        "full_set": ("red_1", "red_2", "red_3"),
        "price": 220,
        "rent": 18,
        "double_rent": 36,
        "house_1": 90,
        "house_2": 250,
        "house_3": 700,
        "house_4": 875,
        "hotel": 1050,
        "house_price": 150,
        "hotel_price": 150,
        "mortgage_value": 110,
        "unmortgage_price": 121
    },  # 23
    {
        "index": "red_3",
        "type": FieldType.STREET,
        "name": "Trafalgar Square",
        "color": StreetColor.RED,
        "full_set": ("red_1", "red_2", "red_3"),
        "price": 240,
        "rent": 20,
        "double_rent": 40,
        "house_1": 100,
        "house_2": 300,
        "house_3": 750,
        "house_4": 925,
        "hotel": 1100,
        "house_price": 150,
        "hotel_price": 150,
        "mortgage_value": 120,
        "unmortgage_price": 132
    },  # 24
    {
        "index": "railroad_3",
        "type": FieldType.RAILROAD,
        "name": "Fenchurch St. Station",
        "full_set": ("railroad_1", "railroad_2", "railroad_3", "railroad_4"),
        "price": 200,
        "rent": 25,
        "rent_2": 50,
        "rent_3": 100,
        "rent_4": 200,
        "mortgage_value": 100,
        "unmortgage_price": 110
    },  # 25
    {
        "index": "yellow_1",
        "type": FieldType.STREET,
        "name": "Leicester Square",
        "color": StreetColor.YELLOW,
        "full_set": ("yellow_1", "yellow_2", "yellow_3"),
        "price": 260,
        "rent": 22,
        "double_rent": 44,
        "house_1": 110,
        "house_2": 330,
        "house_3": 800,
        "house_4": 975,
        "hotel": 1150,
        "house_price": 150,
        "hotel_price": 150,
        "mortgage_value": 130,
        "unmortgage_price": 143
    },  # 26
    {
        "index": "yellow_2",
        "type": FieldType.STREET,
        "name": "Coventry Street",
        "color": StreetColor.YELLOW,
        "full_set": ("yellow_1", "yellow_2", "yellow_3"),
        "price": 260,
        "rent": 22,
        "double_rent": 44,
        "house_1": 110,
        "house_2": 330,
        "house_3": 800,
        "house_4": 975,
        "hotel": 1150,
        "house_price": 150,
        "hotel_price": 150,
        "mortgage_value": 130,
        "unmortgage_price": 143
    },  # 27
    {
        "index": "utility_2",
        "type": FieldType.UTILITY,
        "name": "Water Works",
        "full_set": ("utility_1", "utility_2"),
        "price": 150,
        "rent": 4,
        "rent_2": 10,
        "mortgage_value": 75,
        "unmortgage_price": 83
    },  # 28
    {
        "index": "yellow_3",
        "type": FieldType.STREET,
        "name": "Piccadilly",
        "color": StreetColor.YELLOW,
        "full_set": ("yellow_1", "yellow_2", "yellow_3"),
        "price": 280,
        "rent": 24,
        "double_rent": 48,
        "house_1": 120,
        "house_2": 360,
        "house_3": 850,
        "house_4": 1025,
        "hotel": 1200,
        "house_price": 150,
        "hotel_price": 150,
        "mortgage_value": 140,
        "unmortgage_price": 154
    },  # 29
    {
        "index": "go_to_jail",
        "type": FieldType.GO_TO_JAIL,
        "name": "Go To Jail"
    },  # 30
    {
        "index": "green_1",
        "type": FieldType.STREET,
        "name": "Regent Street",
        "color": StreetColor.GREEN,
        "full_set": ("green_1", "green_2", "green_3"),
        "price": 300,
        "rent": 26,
        "double_rent": 52,
        "house_1": 130,
        "house_2": 390,
        "house_3": 900,
        "house_4": 1100,
        "hotel": 1275,
        "house_price": 200,
        "hotel_price": 200,
        "mortgage_value": 150,
        "unmortgage_price": 165
    },  # 31
    {
        "index": "green_2",
        "type": FieldType.STREET,
        "name": "Oxford Street",
        "color": StreetColor.GREEN,
        "full_set": ("green_1", "green_2", "green_3"),
        "price": 300,
        "rent": 26,
        "double_rent": 52,
        "house_1": 130,
        "house_2": 390,
        "house_3": 900,
        "house_4": 1100,
        "hotel": 1275,
        "house_price": 200,
        "hotel_price": 200,
        "mortgage_value": 150,
        "unmortgage_price": 165
    },  # 32
    {
        "index": "cc_3",
        "type": FieldType.CC,
        "name": "Community Chest"

    },  # 33
    {
        "index": "green_3",
        "type": FieldType.STREET,
        "name": "Bond Street",
        "color": StreetColor.GREEN,
        "full_set": ("green_1", "green_2", "green_3"),
        "price": 320,
        "rent": 28,
        "double_rent": 56,
        "house_1": 150,
        "house_2": 450,
        "house_3": 1000,
        "house_4": 1200,
        "hotel": 1400,
        "house_price": 200,
        "hotel_price": 200,
        "mortgage_value": 160,
        "unmortgage_price": 176
    },  # 34
    {
        "index": "railroad_4",
        "type": FieldType.RAILROAD,
        "name": "Liverpool St. Station",
        "full_set": ("railroad_1", "railroad_2", "railroad_3", "railroad_4"),
        "price": 200,
        "rent": 25,
        "rent_2": 50,
        "rent_3": 100,
        "rent_4": 200,
        "mortgage_value": 100,
        "unmortgage_price": 110
    },  # 35
    {
        "index": "chance_3",
        "type": FieldType.CHANCE,
        "name": "Chance"
    },  # 36
    {
        "index": "dark_blue_1",
        "type": FieldType.STREET,
        "name": "Park Lane",
        "color": StreetColor.DBLUE,
        "full_set": ("dark_blue_1", "dark_blue_2"),
        "price": 350,
        "rent": 35,
        "double_rent": 70,
        "house_1": 175,
        "house_2": 500,
        "house_3": 1100,
        "house_4": 1300,
        "hotel": 1500,
        "house_price": 200,
        "hotel_price": 200,
        "mortgage_value": 175,
        "unmortgage_price": 193
    },  # 37
    {
        "index": "tax_2",
        "type": FieldType.TAX,
        "name": "Super Tax",
        "tax": 100
    },  # 38
    {
        "index": "dark_blue_2",
        "type": FieldType.STREET,
        "name": "Mayfair",
        "color": StreetColor.DBLUE,
        "full_set": ("dark_blue_1", "dark_blue_2"),
        "price": 400,
        "rent": 50,
        "double_rent": 100,
        "house_1": 200,
        "house_2": 600,
        "house_3": 1400,
        "house_4": 1700,
        "hotel": 2000,
        "house_price": 200,
        "hotel_price": 200,
        "mortgage_value": 200,
        "unmortgage_price": 220
    },  # 39
    {
        "index": "jail",
        "type": FieldType.JAIL,
        "name": "Jail"
    }   # 40
]
""" The list of all fields with their properties. """
