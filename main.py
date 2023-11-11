from twisted.internet import reactor

import config
import data_parser
import game_data
import message_factory
from server import ServerFactory


def start_server():
    gdata = game_data.GameData()
    mess_factory = message_factory.MessageFactory()
    parser = data_parser.MessageParser(gdata, mess_factory)
    factory = ServerFactory(mess_factory, parser)
    reactor.listenTCP(config.listen_port, factory)
    reactor.run()


if __name__ == '__main__':
    start_server()
