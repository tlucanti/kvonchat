# client.py
"""
UDP NAT‑hole‑punching client.

Usage:
    python client.py <server_ip> <server_port>
Example:
    python client.py 203.0.113.42 9999
"""

import socket
import sys
from typing import final

from common import Address


@final
class PeerGetter:
    def __init__(self, name: str, addr: str, port: int):
        self.name = name
        self.addr = Address((addr, port))
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soc.settimeout(1)


    def _register(self):
        _ = self.soc.sendto(self.name.encode(), self.addr.addr())


    def get_peers(self) -> dict[str, Address]:
        while True:
            try:
                self._register()

                data, _ = self.soc.recvfrom(4096)
                n, *lines = data.decode().splitlines()
                peers: dict[str, Address] = dict()

                for i in range(int(n)):
                    name, addr = lines[i].strip().split()
                    peers[name] = Address(addr)

                return peers

            except socket.timeout:
                continue


def main(name: str, server: str, port: int):
    pg = PeerGetter(name, server, port)
    peers = pg.get_peers()
    print(peers)


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))

