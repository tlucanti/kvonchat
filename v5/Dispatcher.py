

from abc import ABC, abstractmethod
from typing import final
import queue
import threading

from Server import Address, Server

class Handler(ABC):
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher



@final
class Dispatcher:


    def __init__(self, server: Server):
        """ Runs on main thread """
        self.thread = threading.Thread(target=self._run)
        self.queue: queue.Queue[Dispatcher.Request] = queue.Queue()
        self.server = server

    def run(self):
        """ Runs on main thread """
        self.thread.start()

    def _get(self) -> Request | None:
        """ Runs on Dispatcher thread """
        try:
            return self.queue.get(block=False)
        except queue.Empty:
            return None

    def _run(self):
        """ Runs on Dispatcher thread """
        while True:
            req = self._get()

    def send_upd(self, address: Address, data: str,
                 recv_cb: function | None = None,
                 timeout_cb: function | None = None):
        """ Runs on Handler thread """
        assert (recv_cb is None) == (timeout_cb is None)

        req = Dispatcher.Request(address, data, recv_cb, timeout_cb)
        self.queue.put(req, block=False)


