import pickle

import uuid

from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.python import failure

import interfaces


class Server(Protocol):
    factory: "ServerFactory"
    uuid: uuid.UUID

    def connectionMade(self):
        if len(self.factory.connected_clients) >= 4:
            self.transport.loseConnection()
            return
        self.uuid = uuid.uuid4()
        self.factory.connected_clients[self.uuid] = self
        dic = {
            "my_uuid": self.uuid, "action": "add_player",
            "parameters": {"my_id": len(self.factory.connected_clients) - 1}
        }
        self.factory.parser.parse(dic)
        message = self.factory.parser.get_initial_message(self.uuid)
        self.transport.write(message)

    def connectionLost(self, reason: failure.Failure = connectionDone):
        if self.uuid in self.factory.connected_clients:
            del self.factory.connected_clients[self.uuid]

    def dataReceived(self, data: bytes):
        self.factory.message.add(
            section="players", item=0, attribute="name", value="Player 1"
        )
        self.transport.write(self.factory.message.get())

    def broadcast(self, data: bytes):
        message = f"{self.uuid}: {pickle.loads(data)}"
        data = pickle.dumps(message)
        for client in self.factory.connected_clients.values():
            client.transport.write(data)


class ServerFactory(Factory):

    protocol = Server

    def __init__(self, message_factory: interfaces.MessageFactory, parser: interfaces.Parser):
        self.message: interfaces.MessageFactory = message_factory
        self.parser: interfaces.Parser = parser
        self.connected_clients = dict()
