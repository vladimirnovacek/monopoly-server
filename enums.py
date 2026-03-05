
from enum import StrEnum, auto

class Action(StrEnum):
    ADD_PLAYER = auto()
    UPDATE_PLAYER = auto()
    START_GAME = auto()
    ROLL = auto()
    PAYOUT = auto()
    USE_CARD = auto()
    BUY = auto()
    BUY_HOUSES = auto()
    SELL_HOUSES = auto()
    MORTGAGE = auto()
    UNMORTGAGE = auto()
    AUCTION = auto()
    BID = auto()
    END_TURN = auto()


class Stage(StrEnum):
    ADD_PLAYER = auto()
    AUCTIONING = auto()
    BEGIN_TURN = auto()
    BUYING_DECISION = auto()
    BUYING_PROPERTY = auto()
    END_ROLL = auto()
    END_TURN = auto()
    END_TURN_CONFIRMED = auto()
    GO_TO_JAIL = auto()
    IN_JAIL = auto()
    LEAVING_JAIL = auto()
    MOVED = auto()
    MOVING = auto()
    ON_CARD = auto()
    ON_PROPERTY = auto()
    PAY_RENT = auto()
    PAY_TAX = auto()
    PAYOUT = auto()
    PRE_GAME = auto()
    RENT_ROLL = auto()
    RENT_ROLLING = auto()
    ROLL_IN_JAIL = auto()
    ROLLING = auto()
    START_GAME = auto()
    UNOWNED_PROPERTY = auto()
    UPDATE_PLAYER = auto()
    USE_CARD = auto()
    TRIPLE_DOUBLE = auto()


class Event(StrEnum):
    PLAYER_CONNECTED = auto()
    PROPERTY_BOUGHT = auto()
