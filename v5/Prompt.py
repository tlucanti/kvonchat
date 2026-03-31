
from typing import final
from abc import ABC
from enum import IntEnum

from PromptField import PromptField, TYPE, NAME, KEYRANGE, COUNT, PEER
from PromptField import KeyRange
from Address import Address

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


class Prompt(ABC):
    def __init__(self, type: PromptTypes, fields: list[PromptField], **kwargs):
        self.fields: list[PromptField] = []
        for field in fields:
            if isinstance(field, TYPE):
                assert isinstance(type, PromptTypes)
                self.fields.append(TYPE(type))

            elif isinstance(field, NAME):
                assert isinstance(kwargs['name'], str)
                name = str(kwargs['name'])
                assert isinstance(name, str)
                self.fields.append(NAME(name))
                self.name: str = name

            elif isinstance(field, KEYRANGE):
                assert isinstance(kwargs['keyRange'], KeyRange)
                begin = int(kwargs['keyRange'].begin)
                end = int(kwargs['keyRange'].end)
                self.fields.append(KEYRANGE(begin, end))
                self.keyRange: KeyRange = KeyRange(begin, end)

            elif isinstance(field, COUNT):
                assert isinstance(kwargs['count'], int)
                count = int(kwargs['count'])
                self.fields.append(COUNT(count))
                self.count: int = count

            elif isinstance(field, PEER):
                assert isinstance(kwargs['peers'], list)
                peers: list[Address] = kwargs['peers']
                for peer in peers:
                    assert isinstance(peer, Address)
                    self.fields.append(PEER(peer))

            else:
                assert False


@final
class REGISTER(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            NAME,
        ]
        super().__init__(type(self), fields, **kwargs)

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
        super().__init__(type(self), fields, **kwargs)

@final
class NEWBORN(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
        ]
        super().__init__(type(self), fields, **kwargs)

@final
class PING(Prompt):
    def __init__(self, **kwargs):
        fields = [TYPE]
        super().__init__(type(self), fields, **kwargs)

@final
class PONG(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
        ]
        super().__init__(type(self), fields, **kwargs)

@final
class LEFT(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
            PEER,
        ]
        super().__init__(type(self), **kwargs)

@final
class GETPEERS(Prompt):
    def __init__(self, **kwargs):
        fields = [TYPE]
        super().__init__(type(self), fields, **kwargs)

@final
class PEERS(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
            COUNT,
            list[PEER],
        ]
        super().__init__(type(self), fields, **kwargs)

@final
class MERGEREQUEST(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
        ]
        super().__init__(type(self), fields, **kwargs)

@final
class BORROWREQUEST(Prompt):
    def __init__(self, **kwargs):
        fields = [
            TYPE,
            KEYRANGE,
            COUNT,
            list[PEER],
        ]
        super().__init__(type(self), fields, **kwargs)

