
import socket
from typing import final, override

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

    @override
    def __str__(self):
        return f'{self.ip}:{self.port}'

    @override
    def __repr__(self):
        return f'Address({self.__str__()})'


@final
class Recv:
    def __init__(self, data_address: tuple[bytes, tuple[str, int]]):
        self.data = data_address[0].decode()
        ip, port = data_address[1]
        self.address = Address(ip, port)


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
            return Recv((bytes, addr))
        except TimeoutError as e:
            return None

