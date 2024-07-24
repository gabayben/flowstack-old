from typing import Any, Mapping, Optional, TypeVar, Union

from flowstack.core import Component, ComponentLike, SerializableComponent, coerce_to_component
from flowstack.typing import Effect, Effects

_Input = TypeVar('_Input')

class Parallel(SerializableComponent[_Input, dict[str, Any]]):
    components: dict[str, Component[_Input, Any]]
    max_workers: Optional[int]

    def __init__(
        self,
        steps: Mapping[
            str,
            Union[
                ComponentLike[_Input, Any],
                Mapping[str, ComponentLike[_Input, Any]]
            ]
        ],
        max_workers: Optional[int] = None
    ):
        super().__init__(
            components={
                name: coerce_to_component(step)
                for name, step in steps.items()
            },
            max_workers=max_workers
        )

    def run(self, input: _Input, **kwargs) -> Effect[dict[str, Any]]:
        return Effects.Parallel(
            {
                name: component.effect(input, **kwargs)
                for name, component in self.components.items()
            },
            max_workers=self.max_workers
        )