
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import final, override

from Address import Address
from PromptField import KeyRange
from PromptField import PromptField, PromptTypes, TYPE, NAME, KEYRANGE, COUNT, PEER


class Prompt(ABC):
    @abstractmethod
    def field_list(self) -> list[PromptField]:
        ...

    def serialize(self) -> str:
        return '\n'.join([field.value for field in self.field_list()])

    @staticmethod
    def _peer_list(peers: list[Address]) -> list[PromptField]:
        return [PEER(peer) for peer in peers]


@final
class REGISTER(Prompt):
    def __init__(self, name: str):
        self.name = name

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.REGISTER),
            NAME(self.name),
        ]

@final
class WELCOME(Prompt):
    def __init__(self,
                 keyRange: KeyRange,
                 peerCount: int,
                 peers: list[Address],
                 nextCount: int,
                 nexts: list[Address]):
        self.keyRange = keyRange
        self.peerCount = peerCount
        self.peers = peers
        self.nextCount = nextCount
        self.nexts = nexts

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.WELCOME),
            KEYRANGE(self.keyRange),
            COUNT(self.peerCount),
            *self._peer_list(self.peers),
            COUNT(self.nextCount),
            *self._peer_list(self.nexts),
        ]

@final
class NEWBORN(Prompt):
    def __init__(self, keyRange: KeyRange):
        self.keyRange = keyRange

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.NEWBORN),
            KEYRANGE(self.keyRange),
        ]

@final
class PING(Prompt):
    def __init__(self):
        pass

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.PING),
        ]

@final
class PONG(Prompt):
    def __init__(self, keyRange: KeyRange):
        self.keyRange = keyRange

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.PONG),
            KEYRANGE(self.keyRange),
        ]

@final
class LEFT(Prompt):
    def __init__(self,
                 keyRange: KeyRange,
                 peer: Address):
        self.keyRange = keyRange
        self.peer = peer

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.LEFT),
            KEYRANGE(self.keyRange),
            PEER(self.peer),
        ]

@final
class GETPEERS(Prompt):
    def __init__(self):
        pass

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.GETPEERS),
        ]

@final
class PEERS(Prompt):
    def __init__(self,
                 keyRange: KeyRange,
                 count: int,
                 peers: list[Address]):
        self.keyRange = keyRange
        self.count = count
        self.peers = peers

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.PEERS),
            COUNT(self.count),
            *self._peer_list(self.peers),
        ]

@final
class MERGEREQUEST(Prompt):
    def __init__(self, keyRange: KeyRange):
        self.keyRange = keyRange

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.MERGEREQUEST),
            KEYRANGE(self.keyRange),
        ]

@final
class BORROWREQUST(Prompt):
    def __init__(self,
                 keyRange: KeyRange,
                 peerCount: int,
                 peers: list[Address]):
        self.keyRange = keyRange
        self.peerCount = peerCount
        self.peers = peers

    @override
    def field_list(self) -> list[PromptField]:
        return [
            TYPE(PromptTypes.BORROWREQUST),
            KEYRANGE(self.keyRange),
            COUNT(self.peerCount),
            *self._peer_list(self.peers),
        ]
