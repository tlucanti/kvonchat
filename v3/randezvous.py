# rendezvous.py
"""
Simple UDP rendez‑vous server.

Usage:
    python rendezvous.py <listen_port>
Example:
    python rendezvous.py 9999
"""

from __future__ import annotations

import socket
import sys
import time
from typing import final, override

from common import Address


@final
class Randezvous:
    KEEPALVE_TIMEOUT = 10

    def __init__(self, port: int):
        self.port = port
        self.peers: dict[str, Address] = dict()

        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soc.bind(('', self.port))
        self.soc.settimeout(1)


    def __del__(self):
        self.soc.close()


    def listen(self):
        print(f'[SERVER] Listening on UDP {self.soc.getsockname()}')

        while True:
            try:
                ret_addr: tuple[str, int]
                data, ret_addr = self.soc.recvfrom(1024)

                name = data.decode()
                addr = Address(ret_addr)

                print(f'[SERVER] Registered client {name} -> {addr}')
                self.peers[name] = addr

                self._update_online_peers()
                self._send_online_peers(addr)

            except socket.timeout:
                continue

            except KeyboardInterrupt:
                print("\n[SERVER] Shutting down")
                return


    def _update_online_peers(self):
        now = time.time()
        for name, addr in self.peers.items():
            if now - addr.time > Randezvous.KEEPALVE_TIMEOUT:
                print(f'[SERVER] Client {name} got offline')
                del self.peers[name]


    def _send_online_peers(self, peer: Address):
        msg = '\n'.join(f'{name} {addr}' for name, addr in self.peers.items())
        msg = str(len(self.peers)) + '\n' + msg
        _ = self.soc.sendto(msg.encode(), peer.addr())


def main(port: int):
    r = Randezvous(port)
    r.listen()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(int(sys.argv[1]))
