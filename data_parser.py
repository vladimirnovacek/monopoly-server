import logging
import pickle

from game_data import GameData


class MessageParser:
    def __init__(self, game_data: GameData):
        self.game_data = game_data
        self.network = None

    def parse(self, data: bytes):
        message = pickle.loads(data)
        logging.debug(f"Message received: {message}")
        self.game_data.update(**message)

    def send(self, message: str):
        self.network.send(pickle.dumps(message))
