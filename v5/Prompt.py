from __future__ import annotations

import ast
from typing import final, override
from collections import OrderedDict

from Server import Address


PromptFields = OrderedDict[str, str]


@final
class KeyRange:
    def __init__(self, begin: int, end: int):
        self.begin = begin
        self.end = end


@final
class Prompt:
    field_table: dict[str, list[str]] = {
        "REGISTER": ["TYPE", "NAME"],
    }

    def __init__(self, fields: PromptFields):
        self._validate_order(fields)
        self.fields = fields


    @staticmethod
    def _validate_order(fields: PromptFields):
        types = list(fields.keys())[::-1]
        for field in Prompt.field_table[fields["TYPE"]]:
            assert types.pop() == field
        assert len(types) == 0


    def serialize(self):
        payload: list[str] = []

        for field, value in self.fields.items():
            if field == "TYPE":
                assert isinstance(value, str)
                payload.append(value)

            elif field == "NAME":
                assert isinstance(value, str)
                payload.append(value)

            else:
                raise AssertionError(f"unexpected field type {field}")

        return '\n'.join(payload)

    @classmethod
    def deserialize(cls, data: str):
        msg = PromptFields()

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
            value = lines.pop()

            if field == "TYPE":
                msg[field] = value

            elif field == "NAME":
                msg[field] = value

            else:
                raise AssertionError(f"unexpected field type {field}")

        if len(lines) != 0:
            print(f'DESERIALIZE: extra values in message')
            return None

        return Prompt(msg)

