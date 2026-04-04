from __future__ import annotations

import re
from typing import final
from collections import OrderedDict

from Server import Address

@final
class KeyRange:
    MAX_KEY = 1000

    def __init__(self, begin: int, end: int):
        self.begin = 0
        self.end = KeyRange.MAX_KEY

    @staticmethod
    def max():
        return KeyRange(0, KeyRange.MAX_KEY)


PromptField = str | KeyRange | int | Address | set[Address]

@final
class Prompt:
    field_table: dict[str, list[str]] = {
        "REGISTER": ["TYPE", "NAME"],
        "WELCOME": ["TYPE", "KEYRANGE", "COUNT", "LOCAL_PEERS", "COUNT", "NEXT_PEERS"],
    }

    def __init__(self):
        self.fields = None
        self.values: OrderedDict[str, PromptField] = OrderedDict()
        self.count = 0

    def serialize(self):
        payload: list[str] = []

        for field, value in self.values.items():
            if field == "TYPE":
                assert isinstance(value, str)
                payload.append(value)

            elif field == "NAME":
                assert isinstance(value, str)
                payload.append(value)

            elif field == "KEYRANGE":
                assert isinstance(value, KeyRange)
                payload.append(f"{value.begin} {value.end}")

            elif field == "COUNT":
                assert isinstance(value, int)
                payload.append(str(value))

            elif field == "PEER":
                assert isinstance(value, Address)
                payload.append(f"{value.ip} {value.port}")

            elif field in ("PEERS", "LOCAL_PEERS", "NEXT_PEERS"):
                assert isinstance(value, set)
                for peer in value:
                    assert isinstance(peer, Address)
                    payload.append(f"{peer.ip} {peer.port}")

            else:
                raise AssertionError(f"unexpected field type {field}")

        return '\n'.join(payload)

    @classmethod
    def deserialize(cls, data: str):
        msg = Prompt()
        count = 0

        lines = data.splitlines()[::-1]
        if len(lines) == 0:
            return None

        if lines[-1] not in Prompt.field_table:
            print(f'DESERIALIZE: unexpected message type {lines[0]}')
            return None

        for field in Prompt.field_table[lines[-1]]:
            if len(lines) == 0:
                print(f'DESERIALIZE: not enough values in message')
                return None
            value = lines.pop().strip()

            if field == "TYPE":
                _ = msg.SET_TYPE(value)

            elif field == "NAME":
                if not re.fullmatch(r"\w+", value):
                    print(f'DESERIALIZE: invalid NAME field')
                _ = msg.SET_NAME(value)

            elif field == "KEYRANGE":
                if not re.fullmatch(r"\d+ \d+", value):
                    print("DESERIALIZE: invalid KEYRANGE field")
                    return None
                begin, end = value.split()
                _ = msg.SET_KEYRANGE(KeyRange(int(begin), int(end)))

            elif field == "COUNT":
                if not re.fullmatch(r"\d+", value) or int(value) == 0:
                    print("DESERIALIZE: invalid COUNT field")
                    return None
                _ = msg.SET_COUNT(int(value))
                count = int(value)

            elif field == "PEER":
                try:
                    peer = Address.from_str(value)
                except ValueError:
                    print("DESERIALIZE: invalid PEER field")
                    return None
                _ = msg.SET_PEER(peer)

            elif field in ("PEERS", "LOCAL_PEERS", "NEXT_PEERS"):
                assert count != 0
                peers: set[Address] = {}
                lines.append(value)

                for i in range(count):
                    if len(lines) == 0:
                        print(f'DESERIALIZE: not enough values in message')
                        return None
                    value = lines.pop().strip()

                    try:
                        peer = Address.from_str(value)
                    except ValueError:
                        print("DESERIALIZE: invalid PEER field")
                        return None
                    peers.add(peer)

                if field == "PEERS":
                    _ = msg.SET_PEERS(peers)
                elif field == "LOCAL_PEERS":
                    _ = msg.SET_LOCAL_PEERS(peers)
                elif field == "NEXT_PEERS":
                    _ = msg.SET_NEXT_PEERS(peers)

            else:
                raise AssertionError(f"unexpected field type {field}")

        if len(lines) != 0:
            print(f'DESERIALIZE: extra values in message')
            return None

        return msg


    def _chain(self, field: str, value: PromptField) -> Prompt:
        assert self.fields
        fld = self.fields.pop()
        if fld != field:
            raise AssertionError(f"expected field {fld} got {field}")
        self.values[field] = value
        return self

    def SET_TYPE(self, type: str) -> Prompt:
        assert self.fields is None
        self.fields = self.field_table[type][::-1]
        return self._chain("TYPE", type)

    def SET_NAME(self, name: str) -> Prompt:
        ret = self._chain("NAME",name)
        assert isinstance(ret, Prompt | str)
        return ret

    def SET_KEYRANGE(self, keyRange: KeyRange) -> Prompt:
        return self._chain("KEYRANGE", keyRange)

    def SET_COUNT(self, count: int) -> Prompt:
        assert self.count == 0
        return self._chain("COUNT", count)

    def SET_PEER(self, address: Address) -> Prompt:
        return self._chain("PEER", address)

    def _SET_PEERS(self, tag: str, addresses: set[Address]) -> Prompt:
        assert self.count == len(addresses)
        self.count = 0
        return self._chain(tag + "PEERS", addresses)

    def SET_PEERS(self, addresses: set[Address]) -> Prompt:
        return self._SET_PEERS("", addresses)

    def SET_LOCAL_PEERS(self, addresses: set[Address]) -> Prompt:
        return self._SET_PEERS("LOCAL_", addresses)

    def SET_NEXT_PEERS(self, addresses: set[Address]) -> Prompt:
        return self._SET_PEERS("NEXT_", addresses)


    @property
    def TYPE(self) -> str:
        ret = self.values["TYPE"]
        assert isinstance(ret, str)
        return ret

    @property
    def NAME(self) -> str:
        ret = self.values["NAME"]
        assert isinstance(ret, str)
        return ret

    @property
    def KEYRANGE(self) -> KeyRange:
        ret = self.values["KEYRANGE"]
        assert isinstance(ret, KeyRange)
        return ret

    @property
    def COUNT(self) -> int:
        ret = self.values["COUNT"]
        assert isinstance(ret, int)
        return ret

    @property
    def PEER(self) -> Address:
        ret = self.values["PEER"]
        assert isinstance(ret, Address)
        return ret

    @property
    def PEERS(self) -> list[Address]:
        ret = self.values["PEERS"]
        assert isinstance(ret, list)
        return ret

    @property
    def LOCAL_PEERS(self) -> list[Address]:
        ret = self.values["LOCAL_PEERS"]
        assert isinstance(ret, list)
        return ret

    @property
    def NEXT_PEERS(self) -> list[Address]:
        ret = self.values["NEXT_PEERS"]
        assert isinstance(ret, list)
        return ret
