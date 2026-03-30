
from abc import ABC
from enum import IntEnum
from typing import final

from Address import Address

@final
class KeyRange:
    def __init__(self, begin: int, end: int):
        self.begin = begin
        self.end = end

@final
class PromptTypes(IntEnum):
    # registration prompts
    REGISTER = 0
    WELCOME  = 1
    NEWBORN  = 2

    # keepalive prompts
    PING     = 50
    PONG     = 51
    LEFT     = 52
    GETPEERS = 53
    PEERS    = 54

    # borrow-merge prompts
    MERGEREQUEST = 100
    BORROWREQUST = 101


class PromptField(ABC):
    def __init__(self, value: str):
        self.value: str = value


@final
class TYPE(PromptField):
    def __init__(self, type: PromptTypes):
        super().__init__(str(type))

@final
class NAME(PromptField):
    def __init__(self, name: str):
        super().__init__(name)

@final
class KEYRANGE(PromptField):
    def __init__(self, keyRange: KeyRange):
        super().__init__(f'{keyRange.begin} {keyRange.end}')

@final
class COUNT(PromptField):
    def __init__(self, count: int):
        super().__init__(str(count))

@final
class PEER(PromptField):
    def __init__(self, address: Address):
        super().__init__(f'{address.ip} {address.port}')

