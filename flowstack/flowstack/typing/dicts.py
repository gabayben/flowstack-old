"""
Credit to LangChain - https://github.com/langchain-ai/langchain/tree/main/libs/core/langchain_core/runnables/utils.py
"""

from typing import Any, Optional

class ModelDict(dict[str, Any]):
    def __getattr__(self, name: str) -> Optional[Any]:
        return self.get(name)

    def __setattr__(self, name: str, value: Optional[Any]) -> None:
        self[name] = value

class AddableDict(dict[str, Any]):
    """
    Dictionary that can be added to another dictionary.
    """

    def __add__(self, other: 'AddableDict') -> 'AddableDict':
        chunk = AddableDict(self)
        for key in other:
            if key not in chunk or chunk[key] is None:
                chunk[key] = other[key]
            elif other[key] is not None:
                try:
                    added = chunk[key] + other[key]
                except TypeError:
                    added = other[key]
                chunk[key] = added
        return chunk

    def __radd__(self, other: 'AddableDict') -> 'AddableDict':
        chunk = AddableDict(other)
        for key in self:
            if key not in chunk or chunk[key] is None:
                chunk[key] = self[key]
            elif self[key] is not None:
                try:
                    added = chunk[key] + self[key]
                except TypeError:
                    added = self[key]
                chunk[key] = added
        return chunk