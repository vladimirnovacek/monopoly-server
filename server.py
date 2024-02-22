import logging
import pickle
import struct

import uuid
from typing import Any

from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.python import failure

import config
from interfaces import IServer, IMessenger


def encode(message: Any) -> bytes:
    pickled_data = pickle.dumps(message)
    return struct.pack("!I", len(pickled_data)) + pickled_data


def decode(data: bytes) -> tuple[Any, bytes]:
        try:
            size = struct.unpack("!I", data[:4])[0]
            pickled_data = data[4:4 + size]
            data = b"" if len(data) <= 4 + size else data[4 + size:]
            return pickle.loads(pickled_data), data
        except (struct.error, pickle.UnpicklingError) as e:
            logging.error(f"Error extracting pickled object: {e}")
            return None, b""

class Server(Protocol):
    factory: "ServerFactory"

    def __init__(self):
        self.player_uuid: uuid.UUID | None = None
        self.player_id: int | None = None

    def connectionMade(self) -> None:
        if not self.factory.available_ids:
            self.transport.loseConnection()
            return
        elif self.factory.locked:
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
        # TODO exit when no player connected
        # TODO broadcast new info to other players when one of them leaves
        if self.player_uuid in self.factory.connected_clients:
            del self.factory.connected_clients[self.player_uuid]
            self.factory.retrieve_id(self.player_id)

    def dataReceived(self, data: bytes):
        messages = config.encoder.decode(data)
        for message in messages:
            print("Data received: ", message)
            self.factory.messenger.receive(message)

    def send(self, message: Any) -> None:
        """
        Sends the given data to the client.
        :param message: The data to be sent.
        :type message: Any
        """
        logging.debug(f"Sending data: {message}")
        self.transport.write(config.encoder.encode(message))


class ServerFactory(Factory, IServer):

    protocol = Server

    def __init__(self, messenger: IMessenger):
        self.server_uuid = uuid.uuid4()
        self.messenger: IMessenger = messenger
        self.messenger.set_server(self)
        self.connected_clients: dict[uuid.UUID, Server] = dict()
        self.available_ids: set[int] = set(range(4))
        self.locked = False

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

    def broadcast(self, message: Any) -> None:
        """
        Broadcasts the given data to all connected clients.
        :param message: The data to be sent.
        :type message: bytes
        """
        for client in self.connected_clients.values():
            client.send(message)

    def send(self, player_uuid: uuid.UUID, data: Any) -> None:
        """
        Sends the given data to the given player.
        :param player_uuid: The UUID of the player.
        :type player_uuid: UUID
        :param data: The data to be sent.
        :type data: bytes
        """
        self.connected_clients[player_uuid].send(data)
