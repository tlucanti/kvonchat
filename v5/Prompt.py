
from typing import final
from abc import ABC
from enum import IntEnum

from PromptField import PromptField, TYPE, NAME, KEYRANGE, COUNT, PEER
from PromptField import KeyRange, PromptTypes
from Server import Address


class Prompt(ABC):
    def __init__(self, type: PromptTypes, fields: list[type[PromptField]], **kwargs):
        self.fields: list[PromptField] = []
        for field in fields:
            if field == TYPE:
                assert isinstance(type, PromptTypes)
                self.fields.append(TYPE(type))

            elif field == NAME:
                assert isinstance(kwargs['name'], str)
                name = str(kwargs['name'])
                assert isinstance(name, str)
                self.fields.append(NAME(name))
                self.name: str = name

            elif field == KEYRANGE:
                assert isinstance(kwargs['keyRange'], KeyRange)
                begin = int(kwargs['keyRange'].begin)
                end = int(kwargs['keyRange'].end)
                self.fields.append(KEYRANGE(begin, end))
                self.keyRange: KeyRange = KeyRange(begin, end)

            elif field == COUNT:
                assert isinstance(kwargs['count'], int)
                count = int(kwargs['count'])
                self.fields.append(COUNT(count))
                self.count: int = count

            elif field == PEER:
                assert isinstance(kwargs['peers'], list)
                peers: list[Address] = kwargs['peers']
                for peer in peers:
                    assert isinstance(peer, Address)
                    self.fields.append(PEER(peer))

            else:
                print('unexpected field type:', field)
                assert False


    def serialize(self) -> str:
        ret = ''
        for field in self.fields:
            ret += field.value + '\n'
        return ret


@final
class REGISTER(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            NAME,
        ]
        super().__init__(PromptTypes.REGISTER, fields, **kwargs)

@final
class WELCOME(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
            COUNT,
            list[PEER],
            COUNT,
            list[PEER],
        ]
        super().__init__(PromptTypes.WELCOME, fields, **kwargs)

@final
class NEWBORN(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
        ]
        super().__init__(PromptTypes.NEWBORN, fields, **kwargs)

@final
class PING(Prompt):
    def __init__(self, **kwargs):
        fields = [TYPE]
        super().__init__(PromptTypes.PING, fields, **kwargs)

@final
class PONG(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
        ]
        super().__init__(PromptTypes.PONG, fields, **kwargs)

@final
class LEFT(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
            PEER,
        ]
        super().__init__(PromptTypes.LEFT, **kwargs)

@final
class GETPEERS(Prompt):
    def __init__(self, **kwargs):
        fields = [TYPE]
        super().__init__(PromptTypes.GETPEERS, fields, **kwargs)

@final
class PEERS(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
            COUNT,
            list[PEER],
        ]
        super().__init__(PromptTypes.PEERS, fields, **kwargs)

@final
class MERGEREQUEST(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
        ]
        super().__init__(PromptTypes.MERGEREQUEST, fields, **kwargs)

@final
class BORROWREQUEST(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
            COUNT,
            list[PEER],
        ]
        super().__init__(PromptTypes.BORROWREQUST, fields, **kwargs)

