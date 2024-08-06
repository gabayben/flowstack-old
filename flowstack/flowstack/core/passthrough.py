from typing import TypeVar

from flowstack.core import Component

_Other = TypeVar('_Other')

class Passthrough(Component[_Other, _Other]):
    def __call__(self, input: _Other, **kwargs) -> _Other:
        return input