import pickle

import uuid

from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.python import failure

import interfaces


class Server(Protocol):
    factory: "ServerFactory"
    uuid: uuid.UUID

    def connectionMade(self):
        self.uuid = uuid.uuid4()
        self.factory.connected_clients[self.uuid] = self
        self.factory.message.add(
            section="misc", item="my_uuid", value=str(self.uuid)
        )
        self.factory.message.add(
            section="misc", item="my_id", value=len(self.factory.connected_clients) - 1
        )
        self.transport.write(self.factory.message.get())

    def connectionLost(self, reason: failure.Failure = connectionDone):
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

    def __init__(self, message_factory: interfaces.MessageFactory):
        self.message = message_factory
        self.connected_clients = dict()
