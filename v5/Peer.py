
from __future__ import annotations

from typing import final

from Address import Address
from Prompt import Prompt, Register, Welcome


@final
class Peer:

    def __init__(self, name: str, address: Address):
        self.name = name
        self.address = address
        self.keyRange: Peer.KeyRange = Peer.KeyRange(0, 0)
        self.localPeers: set[Address] = set()
        self.nextPeers: set[Address] = set()
        self.dataStorage: dict[str, str] = dict()

    def _send_prompt_return(self, address: Address, prompt: Prompt) -> Prompt:
        pass

    def register(self, bootstrap: list[Address]):
        reg = Register(
            Prompt.Name(self.name),
        )

        for bs in bootstrap:
            try:
                welcome = self._send_prompt_return(bs, reg)
                if isinstance(welcome, Welcome):
                    break
            except TimeoutError:
                continue
        else:
            raise RuntimeError("can not connect to any of bootstrap peers")









