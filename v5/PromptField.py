
from abc import ABC
from enum import IntEnum
from typing import final

from Address import Address

@final
class KeyRange:
    def __init__(self, begin: int, end: int):
        self.begin = begin
        self.end = end


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
    def __init__(self, begin: int, end: int):
        super().__init__(f'{begin} {end}')

@final
class COUNT(PromptField):
    def __init__(self, count: int):
        super().__init__(str(count))

@final
class PEER(PromptField):
    def __init__(self, address: Address):
        super().__init__(f'{address.ip} {address.port}')

