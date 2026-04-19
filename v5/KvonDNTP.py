
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import final, Callable, Any, override

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
                     prompt: str | list[str],
                     timeout: bool,
                     recv_cb: Callable[[Address, Prompt, Any], None],
                     timeout_cb: Callable[[Address | None, int, Any], None] | None,
                     retry: int,
                     opaque: Any):
            self.address = address
            if isinstance(prompt, str):
                self.prompt = [prompt]
            else:
                self.prompt = prompt
            if timeout:
                self.timeout = time.time() + RECEIVE_TIMEOUT
            else:
                self.timeout = None
            self.recv_cb = recv_cb
            self.timeout_cb = timeout_cb
            self.retry = retry
            self.opaque = opaque

        @override
        def __repr__(self):
            return f"Handler({self.prompt}, {self.address})"


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
        if handler.address is not None:
            if recv.address != handler.address:
                return False
        if prompt.TYPE not in handler.prompt:
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
                handler.recv_cb(recv.address, prompt, handler.opaque)
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


class PeerCore(ABC):
    @final
    class PostArgs:
        def __init__(self, key: int, value: str, peers: set[Address]):
            self.key = key
            self.value = value
            self.peers = peers

    def __init__(self, name: str, port: int):
        self.name: str = name
        self.keyRange: KeyRange = KeyRange.max()
        self.localPeers: set[Address] = set()
        self.nextPeers: set[Address] = set()
        self.dataStorage: dict[int, str] = dict()

        self.server: Server = Server(port)
        self.dispatcher: Dispatcher = Dispatcher()

    @abstractmethod
    def new_client(self, name: str, address: Address):
        ...

    def _add_passive_handlers(self):
        self._add_register_handler()
        self._add_post_handler()

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

    def _add_post_handler(self):
        handler = Dispatcher.Handler(
            None,
            "POST",
            False,
            self._recv_post,
            None,
            0,
            None
        )
        self.dispatcher.add_handler(handler)

    def _recv_register(self, address: Address, msg: Prompt, _):
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
        self.localPeers.add(address)

        self.new_client(msg.NAME, address)


    def _recv_welcome(self, address: Address, msg: Prompt, _):
        assert msg.TYPE == "WELCOME"

        self.localPeers.add(address)
        for peer in msg.LOCAL_PEERS:
            self.localPeers.add(peer)
        for peer in msg.NEXT_PEERS:
            self.nextPeers.add(peer)

        self.keyRange = msg.KEYRANGE


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
            bootstrap,
        )

        self.dispatcher.add_handler(handler)
        self.server.send_udp(address, reg.serialize())


    def _recv_post(self, address: Address, msg: Prompt, _):
        assert msg.TYPE == "POST"
        if self.keyRange.contains(msg.KEY):
            self.dataStorage[msg.KEY] = msg.VALUE
            posted = (Prompt()
                .SET_TYPE("POSTED")
                .SET_KEY(msg.KEY)
            )
            self.server.send_udp(address, posted.serialize())
        else:
            enoent = (Prompt()
                .SET_TYPE("ENOENT")
                .SET_KEYRANGE(self.keyRange)
            )
            self.server.send_udp(address, enoent.serialize())


    def _recv_posted(self, address: Address, msg: Prompt, args: PostArgs):
        if msg.TYPE == "ENOENT":
            self._timeout_posted(None, RETRY_COUNT, args)
        elif msg.TYPE == "POSTED":
            pass
        else:
            assert False


    def _timeout_posted(self,
                      address: Address | None,
                      retry: int,
                      args: PostArgs):
        if retry >= RETRY_COUNT:
            if address is not None:
                print(f'FAILED to POST key to {address}')
            if len(args.peers):
                address = args.peers.pop()
                retry = 0
            else:
                raise RuntimeError("FAILED to POST key")

        post = (Prompt()
            .SET_TYPE("POST")
            .SET_KEY(args.key)
            .SET_SIZE(len(args.value))
            .SET_VALUE(args.value)
        )

        assert address is not None
        handler = Dispatcher.Handler(
                address,
                ["POSTED", "ENOENT"],
                True,
                self._recv_posted,
                self._timeout_posted,
                retry + 1,
                args,
        )

        self.dispatcher.add_handler(handler)
        self.server.send_udp(address, post.serialize())


class Peer(PeerCore, ABC):
    def run(self, bootstrap: list[Address]):
        if len(bootstrap):
            self._timeout_welcome(None, RETRY_COUNT, bootstrap.copy())
        self._add_passive_handlers()

        while True:
            recv = self.server.recv_udp()
            self.dispatcher.step(recv)
            time.sleep(0.1)

    def get(self, key: int) -> str:
        assert False

    def post(self, key: int, value: str):
        args = PeerCore.PostArgs(key, value, self.localPeers.copy())
        self._timeout_posted(None, RETRY_COUNT, args)



