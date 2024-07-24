from typing import TypeVar

from flowstack.core import SerializableComponent

_Other = TypeVar('_Other')

class Passthrough(SerializableComponent[_Other, _Other]):
    def run(self, input: _Other, **kwargs) -> _Other:
        return input