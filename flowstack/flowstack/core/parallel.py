from typing import Any, Mapping, Optional, TypeVar, Union

from flowstack.core import Component, ComponentLike, Effect, Effects, coerce_to_component

_Input = TypeVar('_Input')

class Parallel(Component[_Input, dict[str, Any]]):
    components: dict[str, Component[_Input, Any]]
    max_workers: Optional[int] = None

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
                name: comp.effect(input, **kwargs)
                for name, comp in self.components.items()
            },
            max_workers=self.max_workers
        )