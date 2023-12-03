from twisted.internet import reactor

import config
import messenger
from game_data import GameData
from game_controller import GameController
from server import ServerFactory


def start_server():
    gcontroller = GameController(GameData())
    parser = messenger.Messenger(gcontroller)
    factory = ServerFactory(parser)
    reactor.listenTCP(config.listen_port, factory)
    reactor.run()


if __name__ == '__main__':
    start_server()
