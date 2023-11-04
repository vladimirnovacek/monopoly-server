import pickle
from typing import Self


class MessageFactory:
    def __init__(self):
        self.messages = []

    def add(self, **kwargs) -> Self:
        self.messages.append(kwargs)
        return self

    def get(self) -> bytes:
        data = pickle.dumps(self.messages)
        self.messages.clear()
        return data
