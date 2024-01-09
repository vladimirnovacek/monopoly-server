
import typing
import uuid

import game_data
from board import Board
from dice import Dice
from interfaces import ClientMessage
from states import PreGameState, State

if typing.TYPE_CHECKING:
    from messenger import Messenger


class GameController:
    def __init__(self, data: game_data.GameData):
        self.game_data: game_data.GameData = data
        self.message: Messenger | None = None
        self.server_uuid: uuid.UUID | None = None
        self.state: State = PreGameState(self)
        self.dice: Dice = Dice(2, 6)
        self.board: Board = Board(self)

    def __getattr__(self, item):
        return getattr(self.state, item)

    def parse(self, message: ClientMessage) -> None:
        self.state.parse(message)
