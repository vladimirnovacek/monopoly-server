
import uuid

from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.python import failure

import interfaces


class Server(Protocol):

    def connectionMade(self):
        self.uuid = uuid.uuid4()
        self.factory.connected_clients[self.uuid] = self
        self.factory.message.add(
            type="status", section="misc", item="my_uuid", value=self.uuid
        )
        self.transport.write(self.factory.message.get())

    def connectionLost(self, reason: failure.Failure = connectionDone):
        del self.factory.connected_clients[self.uuid]

    def dataReceived(self, data: bytes):
        self.broadcast(data)

    def broadcast(self, data: bytes):
        message = f"{self.uuid}: {data.decode()}".encode()
        for client in self.factory.connected_clients.values():
            client.transport.write(message)


class ServerFactory(Factory):

    protocol = Server

    def __init__(self, message_factory: interfaces.MessageFactory):
        self.message = message_factory
        self.connected_clients = dict()
