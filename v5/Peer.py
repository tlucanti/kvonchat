
from __future__ import annotations

from typing import final

from Server import Address, Server
from Prompt import Prompt, KeyRange

RETRY_COUNT = 3


@final
class Peer:

    def __init__(self, name: str, port: int):
        self.server = Server(port)
        self.name = name
        self.keyRange: KeyRange = KeyRange.max()
        self.localPeers: set[Address] = set()
        self.nextPeers: set[Address] = set()
        self.dataStorage: dict[str, str] = dict()


    def register(self, bootstrap: list[Address]):
        msg = None

        assert len(bootstrap)
        for address in bootstrap:
            reg = (Prompt()
                .SET_TYPE("REGISTER")
                .SET_NAME(self.name)
            )
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
                raise RuntimeError()


    def run(self):
        while True:
            recv = self.server.recv_udp()
            if recv is None:
                continue

            msg = Prompt.deserialize(recv.data)
            if msg is None:
                continue

            if msg.TYPE == "REGISTER":
                welcome = (Prompt()
                    .SET_TYPE("WELCOME")
                    .SET_KEYRANGE(self.keyRange)
                    .SET_COUNT(len(self.localPeers))
                    .SET_LOCAL_PEERS(self.localPeers)
                    .SET_COUNT(len(self.nextPeers))
                    .SET_NEXT_PEERS(self.nextPeers)
                )
                recv.address.send_udp(welcome.serialize())

