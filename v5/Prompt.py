from __future__ import annotations

import re
from typing import final, override
from collections import OrderedDict

from Server import Address

@final
class KeyRange:
    MAX_KEY = 1000

    def __init__(self, begin: int, end: int):
        self.begin = 0
        self.end = KeyRange.MAX_KEY

    def contains(self, key: int):
        return key >= self.begin and key < self.end

    @staticmethod
    def max():
        return KeyRange(0, KeyRange.MAX_KEY)

    @override
    def __str__(self):
        return f"({self.begin}:{self.end})"

    @override
    def __repr__(self):
        return f"KeyRange{self.__str__()}"


PromptField = str | KeyRange | int | Address | set[Address]

@final
class Prompt:
    field_table: dict[str, list[str]] = {
        "REGISTER": ["TYPE", "NAME"],
        "WELCOME": ["TYPE", "KEYRANGE", "LOCAL_COUNT", "LOCAL_PEERS", "NEXT_COUNT", "NEXT_PEERS"],

        "POST": ["TYPE", "KEY", "SIZE", "VALUE"],
        "POSTED": ["TYPE", "KEY"],
        "ENOENT": ["TYPE", "KEYRANGE"],
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

            elif field in ("COUNT", "LOCAL_COUNT", "NEXT_COUNT"):
                assert isinstance(value, int)
                payload.append(str(value))

            elif field == "PEER":
                assert isinstance(value, Address)
                payload.append(value.serialize())

            elif field in ("PEERS", "LOCAL_PEERS", "NEXT_PEERS"):
                assert isinstance(value, set)
                for peer in value:
                    assert isinstance(peer, Address)
                    payload.append(peer.serialize())

            elif field == "KEY":
                assert isinstance(value, int)
                payload.append(hex(value))

            elif field == "SIZE":
                assert isinstance(value, int)
                payload.append(str(value))

            elif field == "VALUE":
                assert isinstance(value, str)
                payload.append(value)

            else:
                raise AssertionError(f"unexpected field type {field}")

        return '\n'.join(payload)

    @classmethod
    def deserialize(cls, data: str):
        msg = Prompt()
        count = None

        lines = data.splitlines()[::-1]
        if len(lines) == 0:
            return None

        if lines[-1] not in Prompt.field_table:
            print(f'DESERIALIZE: unexpected message type {lines[0]}')
            return None

        for field in Prompt.field_table[lines[-1]]:
            if len(lines) == 0:
                if count == 0:
                    value = None
                else:
                    print(f'DESERIALIZE: not enough values in message')
                    return None
            else:
                value = lines.pop().strip()

            if field == "TYPE":
                assert value is not None
                _ = msg.SET_TYPE(value)

            elif field == "NAME":
                assert value is not None
                if not re.fullmatch(r"\w+", value):
                    print(f'DESERIALIZE: invalid NAME field')
                _ = msg.SET_NAME(value)

            elif field == "KEYRANGE":
                assert value is not None
                if not re.fullmatch(r"\d+ \d+", value):
                    print("DESERIALIZE: invalid KEYRANGE field")
                    return None
                begin, end = value.split()
                _ = msg.SET_KEYRANGE(KeyRange(int(begin), int(end)))

            elif field in ("COUNT", "LOCAL_COUNT", "NEXT_COUNT"):
                assert value is not None
                if not re.fullmatch(r"\d+", value):
                    print(f"DESERIALIZE: invalid {field} field")
                    return None
                if field == "COUNT":
                    _ = msg.SET_COUNT(int(value))
                elif field == "LOCAL_COUNT":
                    _ = msg.SET_LOCAL_COUNT(int(value))
                elif field == "NEXT_COUNT":
                    _ = msg.SET_NEXT_COUNT(int(value))
                count = int(value)

            elif field == "PEER":
                assert value is not None
                try:
                    peer = Address.from_str(value)
                except ValueError:
                    print("DESERIALIZE: invalid PEER field")
                    return None
                _ = msg.SET_PEER(peer)

            elif field in ("PEERS", "LOCAL_PEERS", "NEXT_PEERS"):
                assert count is not None
                peers: set[Address] = set()
                if value is not None:
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

            elif field == "KEY":
                assert value is not None
                if not re.fullmatch(r"0x[0-9a-fA-F]+", value):
                    print(f"DESERIALIZE: invalid {field} field")
                    return None
                _ = msg.SET_KEY(int(value, 16))

            elif field == "SIZE":
                assert value is not None
                if not re.fullmatch(r"\d+", value):
                    print(f"DESERIALIZE: invalid {field} field")
                    return None
                _ = msg.SET_SIZE(int(value))

            elif field == "VALUE":
                assert value is not None
                _ = msg.SET_VALUE(value)

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
        assert field not in self.values
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

    def SET_LOCAL_COUNT(self, count: int) -> Prompt:
        assert self.count == 0
        return self._chain("LOCAL_COUNT", count)

    def SET_NEXT_COUNT(self, count: int) -> Prompt:
        assert self.count == 0
        return self._chain("NEXT_COUNT", count)

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

    def SET_KEY(self, key: int) -> Prompt:
        return self._chain("KEY", key)

    def SET_SIZE(self, size: int) -> Prompt:
        return self._chain("SIZE", size)

    def SET_VALUE(self, value: str) -> Prompt:
        return self._chain("VALUE", value)


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
    def LOCAL_PEERS(self) -> set[Address]:
        ret = self.values["LOCAL_PEERS"]
        assert isinstance(ret, set)
        return ret

    @property
    def NEXT_PEERS(self) -> set[Address]:
        ret = self.values["NEXT_PEERS"]
        assert isinstance(ret, set)
        return ret

    @property
    def KEY(self) -> int:
        ret = self.values["KEY"]
        assert isinstance(ret, int)
        return ret

    @property
    def SIZE(self) -> int:
        ret = self.values["SIZE"]
        assert isinstance(ret, int)
        return ret

    @property
    def VALUE(self) -> str:
        ret = self.values["VALUE"]
        assert isinstance(ret, str)
        return ret
