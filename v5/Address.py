
from typing import final

@final
class Address:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
