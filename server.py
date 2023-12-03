import pickle

import uuid

from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.python import failure

from messenger import Messenger


class Server(Protocol):
    factory: "ServerFactory"

    def __init__(self):
        self.player_uuid: uuid.UUID | None = None
        self.player_id: int | None = None

    def connectionMade(self) -> None:
        if not self.factory.available_ids:
            self.transport.loseConnection()
            return
        else:
            self.player_id = self.factory.get_id()
        self.player_uuid = uuid.uuid4()
        self.factory.connected_clients[self.player_uuid] = self
        dic = {
            "my_uuid": self.factory.server_uuid, "action": "add_player",
            "parameters": {"player_uuid": self.player_uuid, "player_id": self.player_id}
        }
        self.factory.messenger.receive(dic)

    def connectionLost(self, reason: failure.Failure = connectionDone):
        if self.player_uuid in self.factory.connected_clients:
            del self.factory.connected_clients[self.player_uuid]
            self.factory.retrieve_id(self.player_id)


    def dataReceived(self, data: bytes):
        print("Data received: ", pickle.loads(data))

    def broadcast(self, data: bytes):
        message = f"{self.player_uuid}: {pickle.loads(data)}"
        data = pickle.dumps(message)
        for client in self.factory.connected_clients.values():
            client.transport.write(data)

    def send(self, data: bytes):
        self.transport.write(data)

class ServerFactory(Factory):

    protocol = Server

    def __init__(self, messenger: Messenger):
        self.server_uuid = uuid.uuid4()
        # self.message: interfaces.MessageFactory = message_factory  # possibly redundant
        self.messenger: Messenger = messenger
        self.messenger.set_server(self)
        # self.messenger.network = self  # possibly redundant
        self.connected_clients = dict()
        self.available_ids = set(range(4))

    def get_id(self) -> int:
        """
        Gets an available player ID.
        :return: The player ID.
        :rtype: int
        """
        player_id = min(self.available_ids)
        self.available_ids.remove(player_id)
        return player_id

    def retrieve_id(self, player_id: int) -> None:
        """
        Retrieves a disconnected player ID.
        :param player_id: The player ID.
        :type player_id: int
        :return: None
        :rtype: None
        """
        self.available_ids.add(player_id)

    def broadcast(self, data: bytes):
        for client in self.connected_clients.values():
            client.send(data)

    def send(self, player_uuid: uuid.UUID, data: bytes):
        self.connected_clients[player_uuid].send(data)
