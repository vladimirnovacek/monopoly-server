import pickle

import uuid

from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.python import failure

import interfaces


class Server(Protocol):
    factory: "ServerFactory"
    uuid: uuid.UUID
    player_id: int

    def connectionMade(self):
        if not self.factory.available_ids:
            self.transport.loseConnection()
            return
        else:
            self.player_id = self.factory.get_id()
        self.uuid = uuid.uuid4()
        self.factory.connected_clients[self.uuid] = self
        dic = {
            "my_uuid": self.factory.server_uuid, "action": "add_player",
            "parameters": {"player_uuid": self.uuid, "player_id": self.player_id}
        }
        self.factory.parser.parse(dic)
        message = self.factory.parser.get_initial_message(self.uuid)
        self.transport.write(message)

    def connectionLost(self, reason: failure.Failure = connectionDone):
        if self.uuid in self.factory.connected_clients:
            del self.factory.connected_clients[self.uuid]

    def dataReceived(self, data: bytes):
        print("Data received: ", pickle.loads(data))

    def broadcast(self, data: bytes):
        message = f"{self.uuid}: {pickle.loads(data)}"
        data = pickle.dumps(message)
        for client in self.factory.connected_clients.values():
            client.transport.write(data)


class ServerFactory(Factory):

    protocol = Server

    def __init__(self, message_factory: interfaces.MessageFactory, parser: interfaces.Parser):
        self.server_uuid = uuid.uuid4()
        self.message: interfaces.MessageFactory = message_factory
        self.parser: interfaces.Parser = parser
        self.parser.network = self
        self.connected_clients = dict()
        self.available_ids = set(range(1, 5))

    def get_id(self) -> int:
        """
        Gets an available player ID.
        :return: The player ID.
        :rtype: int
        """
        player_id = min(self.available_ids)
        self.available_ids.remove(player_id)
        return player_id