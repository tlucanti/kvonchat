from __future__ import annotations

from typing import final
from abc import ABC
from enum import IntEnum
from collections.abc import Iterable

from PromptField import PromptField, TYPE, NAME, KEYRANGE, COUNT, PEER
from PromptField import KeyRange, PromptTypes
from Server import Address


class Prompt(ABC):
    fields: Iterable[type]
    prompt_type: PromptTypes

    def __init__(self, **kwargs: str):
        self.payload: list[PromptField] = []

        for field in self.fields:
            if field == TYPE:
                self.payload.append(TYPE(self.prompt_type))

            elif field == NAME:
                assert isinstance(kwargs['name'], str)
                name = str(kwargs['name'])
                assert isinstance(name, str)
                self.payload.append(NAME(name))
                self.name: str = name

            elif field == KEYRANGE:
                assert isinstance(kwargs['keyRange'], KeyRange)
                begin = int(kwargs['keyRange'].begin)
                end = int(kwargs['keyRange'].end)
                self.payload.append(KEYRANGE(begin, end))
                self.keyRange: KeyRange = KeyRange(begin, end)

            elif field == COUNT:
                assert isinstance(kwargs['count'], int)
                count = int(kwargs['count'])
                self.payload.append(COUNT(count))
                self.count: int = count

            elif field == list[PEER]:
                assert isinstance(kwargs['peers'], list)
                peers: list[Address] = kwargs['peers']
                for peer in peers:
                    assert isinstance(peer, Address)
                    self.payload.append(PEER(peer))

            elif field == PEER:
                assert isinstance(kwargs['peer'], Address)
                peer: Address = kwargs['peer']
                self.payload.append(PEER(peer))

            else:
                print('unexpected field type:', field)
                assert False


    def serialize(self) -> str:
        ret = ''
        for field in self.payload:
            ret += field.value + '\n'
        return ret

    @classmethod
    def parse(cls, data: str) -> Prompt | None:
        table: dict[PromptTypes, type[Prompt]] = {
            PromptTypes.REGISTER: REGISTER,
            PromptTypes.WELCOME: WELCOME,
            PromptTypes.NEWBORN: NEWBORN,
            PromptTypes.PING: PING,
            PromptTypes.PONG: PONG,
            PromptTypes.LEFT: LEFT,
            PromptTypes.GETPEERS: GETPEERS,
            PromptTypes.PEERS: PEERS,
            PromptTypes.MERGEREQUEST: MERGEREQUEST,
            PromptTypes.BORROWREQUEST: BORROWREQUEST,
        }

        lines = data.splitlines()
        if len(lines) == 0:
            return None

        msg_type = data.splitlines()[0]

        if msg_type in table:
            return table[msg_type].parse(lines)
        return None



@final
class REGISTER(Prompt):
    prompt_type = PromptTypes.REGISTER
    fields = [
        TYPE,
        NAME,
    ]

@final
class WELCOME(Prompt):
    prompt_type = PromptTypes.WELCOME
    fields = [
        TYPE,
        KEYRANGE,
        COUNT,
        list[PEER],
        COUNT,
        list[PEER],
    ]

@final
class NEWBORN(Prompt):
    prompt_type = PromptTypes.NEWBORN
    fields = [
        TYPE,
        KEYRANGE,
    ]

@final
class PING(Prompt):
    prompt_type = PromptTypes.PING
    fields = [TYPE]

@final
class PONG(Prompt):
    prompt_type = PromptTypes.PONG
    fields = [
        TYPE,
        KEYRANGE,
    ]

@final
class LEFT(Prompt):
    prompt_type = PromptTypes.LEFT
    fields = [
        TYPE,
        KEYRANGE,
        PEER,
    ]

@final
class GETPEERS(Prompt):
    prompt_type = PromptTypes.GETPEERS
    fields = [TYPE]

@final
class PEERS(Prompt):
    prompt_type = PromptTypes.PEERS
    fields = [
        TYPE,
        KEYRANGE,
        COUNT,
        list[PEER],
    ]

@final
class MERGEREQUEST(Prompt):
    prompt_type = PromptTypes.MERGEREQUEST
    fields = [
        TYPE,
        KEYRANGE,
    ]

@final
class BORROWREQUEST(Prompt):
    prompt_type = PromptTypes.BORROWREQUEST
    fields = [
        TYPE,
        KEYRANGE,
        COUNT,
        list[PEER],
    ]

