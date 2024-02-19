import logging
import pickle
import struct
from abc import ABC, abstractmethod
from typing import Any


class Encoder(ABC):
    @staticmethod
    @abstractmethod
    def encode(message: Any) -> bytes:
        ...

    @staticmethod
    @abstractmethod
    def decode(data: bytes) -> list:
        ...

class PickleEncoder(Encoder):
    @staticmethod
    def encode(message: Any) -> bytes:
        pickled_data = pickle.dumps(message)
        return struct.pack("!I", len(pickled_data)) + pickled_data

    @staticmethod
    def decode(data: bytes) -> list:
        try:
            size = struct.unpack("!I", data[:4])[0]
            pickled_data = data[4:4 + size]
            messages = [pickle.loads(pickled_data)]
            remaining_data = b"" if len(data) <= 4 + size else data[4 + size:]
            if remaining_data:
                message = PickleEncoder.decode(remaining_data)
                if len(message) == 1:
                    messages.append(message[0])
                elif len(message) == 0:
                    pass
                else:
                    messages.extend(message)
            return messages
        except (struct.error, pickle.UnpicklingError, EOFError) as e:
            logging.error(f"Error extracting pickled object: {e}")
            return []