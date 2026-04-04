
from __future__ import annotations

from typing import final
from collections import OrderedDict

from Server import Address, Server
from Prompt import Prompt, KeyRange

RETRY_COUNT = 3


@final
class Peer:

    def __init__(self, name: str, port: int):
        self.server = Server(port)
        self.name = name
        self.keyRange: KeyRange = KeyRange(0, 0)
        self.localPeers: set[Address] = set()
        self.nextPeers: set[Address] = set()
        self.dataStorage: dict[str, str] = dict()


    def register(self, bootstrap: list[Address]):
        msg = None

        assert len(bootstrap)
        for address in bootstrap:
            reg = Prompt(OrderedDict({
                "TYPE": "REGISTER",
                "NAME": self.name
            }))
            address.send_udp(reg.serialize())

            for retry in range(RETRY_COUNT):
                recv  = self.server.recv_udp()
                if recv is None or recv.address != address:
                    continue

                msg = Prompt.deserialize(recv.data)

            if msg is not None:
                break
            else:
                print(f'FAILED to get WELCOME response from {address}')
                return 1
        return 0


    def run(self):
        recv = None
        while recv is None:
            recv = self.server.recv_udp()
            if recv is None:
                continue

            msg = Prompt.deserialize(recv.data)
            print(msg)
