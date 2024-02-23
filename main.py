import logging

from twisted.internet import reactor

import config
import messenger
from game_data import GameData
from game_controller import GameController
from server import ServerFactory


def start_server():
    message = messenger.Messenger()
    gcontroller = GameController(GameData(), message)
    factory = ServerFactory(message)
    reactor.listenTCP(config.listen_port, factory)
    reactor.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    start_server()
