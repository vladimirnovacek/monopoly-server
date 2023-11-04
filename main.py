from twisted.internet import reactor

import config
import message_factory
from server import ServerFactory


def start_server():
    factory = ServerFactory(message_factory.MessageFactory())
    reactor.listenTCP(config.listen_port, factory)
    reactor.run()


if __name__ == '__main__':
    start_server()
