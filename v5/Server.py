
import socket
from typing import final

RECEIVE_TIMEOUT = 1

@final
class Address:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @classmethod
    def from_str(cls, s: str):
        ip, port = s.split(':')
        return Address(ip, int(port))

    def addr(self):
        return (self.ip, self.port)

    def set_port(self, port: int):
        self.server_port = port

    def send_udp(self, message: str):
        print("SENDING:", message.splitlines())
        _ = self.soc.sendto(message.encode('utf-8'), self.addr())


@final
class Server:
    def __init__(self, port: int):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soc.bind(('', port))
        self.soc.settimeout(RECEIVE_TIMEOUT)

    def recv_udp(self):
        try:
            addr: tuple[str, int]
            bytes, addr = self.soc.recvfrom(4096)
            print(f'GETTING {addr[0]}:{addr[1]}:', bytes.decode().splitlines())
            return bytes.decode(), Address(addr[0], addr[1])
        except TimeoutError as e:
            return None, None

