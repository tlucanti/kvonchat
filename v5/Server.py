
from __future__ import annotations

import socket
import re
from typing import final, override


@final
class Address:
    def __init__(self, ip: str, port: int):
        assert port < 65535
        _ = socket.inet_aton(ip)

        self.ip = ip
        self.port = port

    @override
    def __hash__(self):
        return hash(self.addr())

    @override
    def __eq__(self, other: object):
        assert isinstance(other, Address)
        return self.ip == other.ip and self.port == other.port

    @override
    def __ne__(self, other: object):
        assert isinstance(other, Address)
        return self.ip != other.ip or self.port != other.port

    @staticmethod
    def from_str(s: str):
        if not re.fullmatch(r"\d+[.:]\d+[.:]\d+[.:]\d+:\d+", s):
            raise ValueError(f"invalid address-port string: {s}")
        ip, p = s.split(':')
        try:
            _ = socket.inet_aton(ip)
        except socket.error:
            raise ValueError(f"invalid address: {ip}")
        port = int(p)
        if port > 65535:
            raise ValueError(f"invalid port: {port}")
        return Address(ip, port)

    def addr(self):
        return (self.ip, self.port)

    def serialize(self):
        return f"{self.ip} {self.port}"

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
        self.soc.setblocking(False)

    def send_udp(self, address: Address, message: str):
        print(f"SENDING {address}:", message.splitlines())
        _ = self.soc.sendto(message.encode('utf-8'), address.addr())

    def recv_udp(self) -> Recv | None:
        addr: tuple[str, int]
        try:
            bytes, addr = self.soc.recvfrom(4096)
            print(f'GETTING {addr[0]}:{addr[1]}:', bytes.decode().splitlines())
            return Recv((bytes, addr))
        except BlockingIOError:
            return None

