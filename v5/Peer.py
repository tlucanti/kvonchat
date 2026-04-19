
from __future__ import annotations

import time
from typing import final, Callable, Any

from Server import Address, Server, Recv
from Prompt import Prompt, KeyRange

RETRY_COUNT = 3
RECEIVE_TIMEOUT = 3.0


@final
class Dispatcher:
    @final
    class Handler:
        def __init__(self,
                     address: Address | None,
                     prompt: str,
                     timeout: bool,
                     recv_cb: Callable[[Address, Prompt], None],
                     timeout_cb: Callable[[Address | None, int, Any], None] | None,
                     retry: int,
                     opaque: Any):
            self.address = address
            self.prompt = prompt
            if timeout:
                self.timeout = time.time() + RECEIVE_TIMEOUT
            else:
                self.timeout = None
            self.recv_cb = recv_cb
            self.timeout_cb = timeout_cb
            self.retry = retry
            self.opaque = opaque

        def match(self, address: Address, prompt: Prompt):
            address_ok = True
            if self.address is not None:
                address_ok = (address == self.address)
            return address_ok and prompt.TYPE == self.prompt


    #@final
    #class Timer:
    #    def __init__(self, delta: int, callback: function):
    #        self.timeout = time.time() + delta
    #        self.callback = callback

    #    def __lt__(self, other: object):
    #        assert isinstance(other, Peer.Timer)
    #        return self.timeout < other.timeout


    def __init__(self):
        self.handlers: list[Dispatcher.Handler] = list()
        #self.timers: list[Dispatcher.Timer] = list()

    def add_handler(self, handler: Dispatcher.Handler):
        self.handlers.append(handler)

    @staticmethod
    def _match(handler: Dispatcher.Handler, prompt: Prompt, recv: Recv):
        if handler.address is None:
            return True
        if recv.address != handler.address:
            return False
        if prompt.TYPE != handler.prompt:
            return False
        return True

    def _step_recv(self, recv: Recv):
        prompt = Prompt.deserialize(recv.data)
        if prompt is None:
            return

        iter = self.handlers.copy()
        self.handlers = []
        copy: list[Dispatcher.Handler] = list()

        for handler in iter:
            if self._match(handler, prompt, recv):
                handler.recv_cb(recv.address, prompt)
            else:
                copy.append(handler)
        self.handlers = copy + self.handlers

    def _step_timeout(self):
        t = time.time()

        iter = self.handlers.copy()
        self.handlers = []
        copy: list[Dispatcher.Handler] = list()

        for handler in iter:
            if handler.timeout is not None and t > handler.timeout:
                if handler.timeout_cb is not None:
                    handler.timeout_cb(handler.address, handler.retry, handler.opaque)
            else:
                copy.append(handler)
        self.handlers = copy + self.handlers

    def step(self, recv: Recv | None):
        if recv is not None:
            self._step_recv(recv)
        self._step_timeout()


@final
class Peer:
    def __init__(self, name: str, port: int):
        self.name = name
        self.keyRange: KeyRange = KeyRange.max()
        self.localPeers: set[Address] = set()
        self.nextPeers: set[Address] = set()
        self.dataStorage: dict[str, str] = dict()

        self.server = Server(port)
        self.dispatcher = Dispatcher()


    def _add_register_handler(self):
        handler = Dispatcher.Handler(
            None,
            "REGISTER",
            False,
            self._recv_register,
            None,
            0,
            None
        )
        self.dispatcher.add_handler(handler)

    def _recv_register(self, address: Address, msg: Prompt):
        assert msg.TYPE == "REGISTER"

        welcome = (Prompt()
            .SET_TYPE("WELCOME")
            .SET_KEYRANGE(self.keyRange)
            .SET_LOCAL_COUNT(len(self.localPeers))
            .SET_LOCAL_PEERS(self.localPeers)
            .SET_NEXT_COUNT(len(self.nextPeers))
            .SET_NEXT_PEERS(self.nextPeers)
        )
        self.server.send_udp(address, welcome.serialize())

        self._add_register_handler()


    def _recv_welcome(self, address: Address, msg: Prompt):
        assert msg.TYPE == "WELCOME"

        self.localPeers.add(address)
        for peer in msg.LOCAL_PEERS:
            self.localPeers.add(peer)
        for peer in msg.NEXT_PEERS:
            self.nextPeers.add(peer)


    def _timeout_welcome(self,
                         address: Address | None,
                         retry: int,
                         bootstrap: list[Address]):

        if retry >= RETRY_COUNT:
            if address is not None:
                print(f'FAILED to get WELCOME response from {address}')
            if len(bootstrap):
                address = bootstrap.pop()
                retry = 0
            else:
                raise RuntimeError("FAILED to connect to any of bootstrap peers")

        reg = (Prompt()
            .SET_TYPE("REGISTER")
            .SET_NAME(self.name)
        )

        assert address is not None
        handler = Dispatcher.Handler(
            address,
            "WELCOME",
            True,
            self._recv_welcome,
            self._timeout_welcome,
            retry + 1,
            bootstrap
        )

        self.dispatcher.add_handler(handler)
        self.server.send_udp(address, reg.serialize())


    def run(self, bootstrap: list[Address]):
        if len(bootstrap):
            self._timeout_welcome(None, RETRY_COUNT, bootstrap)
        else:
            self._add_register_handler()

        while True:
            recv = self.server.recv_udp()
            self.dispatcher.step(recv)
            time.sleep(0.1)
