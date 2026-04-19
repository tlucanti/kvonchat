
from typing import override

from KvonDNTP import Peer
from Server import Address
from Prompt import KeyRange

class ClientCore(Peer):
    def __init__(self, name: str, port: int):
        super().__init__(name, port)

    def hash(self, key: str):
        return hash(key) % KeyRange.MAX_KEY

    @override
    def new_client(self, name: str, address: Address):
        self.post(self.hash(name), address.serialize())


class Client(ClientCore):
    def __init__(self, name: str, port: int):
        super().__init__(name, port)

    @override
    def run(self, bootstrap: list[Address]):
        super().run(bootstrap)

    def send(self, name: str, message: str):
        addr = self.get(self.hash(name))
        address = Address.deserialize(addr)
