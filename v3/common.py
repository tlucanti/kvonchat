
import time
from typing import final, override

@final
class Address:
    def __init__(self, addr: tuple[str, int] | str):
        if isinstance(addr, str):
            ip, port = addr.split(':')
            self.ip = ip
            self.port = int(port)
        else:
            self.ip = addr[0]
            self.port = addr[1]
        self.time = time.time()

    def addr(self):
        return (self.ip, self.port)

    @override
    def __str__(self):
        return f'{self.ip}:{self.port}'

    @override
    def __repr__(self):
        return f'Address({self.ip}:{self.port})'

