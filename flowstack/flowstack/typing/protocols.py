from typing import Protocol, Self, runtime_checkable

@runtime_checkable
class Addable(Protocol):
    def __add__(self, other: Self) -> Self:
        pass