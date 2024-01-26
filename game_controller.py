
from uuid import UUID

from dice import Dice
from interfaces import ClientMessage, IController, IMessenger, IData, IDice
from state.pre_game import PreGameState
from state.state import State


class GameController(IController):
    def __init__(self, data: IData):
        super().__init__(data)
        self.game_data: IData = data
        self.message: IMessenger | None = None
        self.server_uuid: UUID | None = None
        self.state: State = PreGameState(self)
        self.dice: IDice = Dice(2, 6)

    def __getattr__(self, item):
        return getattr(self.state, item)

    def parse(self, message: ClientMessage) -> None:
        self.state.parse(message)
