
from __future__ import annotations

from typing import final

from Server import Address, Server
from Prompt import Prompt, REGISTER, WELCOME
from PromptField import KeyRange

PromptClass = type[Prompt]

@final
class Peer:

    def __init__(self, server: Server, name: str):
        self.server = server
        self.name = name
        self.keyRange: KeyRange = KeyRange(0, 0)
        self.localPeers: set[Address] = set()
        self.nextPeers: set[Address] = set()
        self.dataStorage: dict[str, str] = dict()

    def register(self, bootstrap: list[Address]):
        retry = 0

        if len(bootstrap) == 0:
            while True:
                msg, addr = self.server.recv_udp()

        while True:
            address = bootstrap.pop()
            reg = REGISTER(name=self.name)
            address.send_udp(reg.serialize())

            msg, addr = self.server.recv_udp()
            print(msg, addr)
            break

            raise RuntimeError("can not connect to any of bootstrap peers")









