from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar, cast, override

from pydantic import BaseModel, Field, PrivateAttr

from flowstack.core import Component, SerializableComponent, coerce_to_component
from flowstack.core import ComponentLike
from flowstack.typing import Effect

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')
_Other = TypeVar('_Other')

class SequentialSchema(ABC):
    @abstractmethod
    def seq_input_schema(self, next_schema: Type[BaseModel]) -> Type[BaseModel]:
        pass

    @abstractmethod
    def seq_output_schema(self, previous_schema: Type[BaseModel]) -> Type[BaseModel]:
        pass

class Sequential(SerializableComponent[_Input, _Output]):
    first: Component[_Input, Any]
    middle: list[Component] = Field(default_factory=list)
    last: Component[Any, _Output]
    _name: Optional[str] = PrivateAttr()

    @property
    @override
    def name(self) -> str:
        return self._name or super().name

    @property
    @override
    def InputType(self) -> Type[_Input]:
        return self.first.InputType

    @property
    @override
    def OutputType(self) -> Type[_Output]:
        return self.last.OutputType

    @property
    def steps(self) -> list[Component]:
        return [self.first] + self.middle + [self.last]

    def __init__(
        self,
        *steps: Component,
        first: Optional[Component[_Input, Any]] = None,
        middle: Optional[list[Component]] = None,
        last: Optional[Component[Any, _Output]] = None,
        name: Optional[str] = None
    ):
        steps_flat: list[Component] = []
        if not steps:
            if first and last:
                steps_flat = [first] + (middle or []) + [last]
        else:
            for step in steps:
                if isinstance(step, Sequential):
                    steps_flat.extend(step.steps)
                else:
                    steps_flat.append(step)
        if len(steps_flat) < 2:
            raise ValueError(f'Sequential must have at least 2 steps, got {len(steps_flat)} steps.')
        super().__init__(
            first=steps_flat[0],
            middle=list(steps_flat[1:-1]),
            last=steps_flat[-1]
        )
        self._name = name

    @override
    def __or__(self, other: 'ComponentLike[_Output, _Other]') -> 'Component[_Input, _Other]':
        if isinstance(other, Sequential):
            return Sequential(
                self.first,
                *self.middle,
                self.last,
                other.first,
                *other.middle,
                other.last,
                name=self.name or other.name
            )
        return Sequential(
            self.first,
            *self.middle,
            self.last,
            coerce_to_component(other),
            name=self.name
        )

    @override
    def __ror__(self, other: 'ComponentLike[_Other, _Input]') -> 'Component[_Other, _Output]':
        if isinstance(other, Sequential):
            return Sequential(
                other.first,
                *other.middle,
                other.last,
                self.first,
                *self.middle,
                self.last,
                name=other.name or self.name
            )
        return Sequential(
            coerce_to_component(other),
            self.first,
            *self.middle,
            self.last,
            name=self.name
        )

    def run(self, input: _Input, **kwargs) -> Effect[_Output]:
        try:
            effect = self.steps[0].effect(input, **kwargs)
            for step in self.steps[1:]:
                effect = effect.flat_map(lambda out: step.effect(out, **kwargs))
        except:
            raise
        else:
            return cast(Effect[_Output], effect)

    @override
    def input_schema(self) -> Type[BaseModel]:
        return _seq_input_schema(self.steps)

    @override
    def output_schema(self) -> Type[BaseModel]:
        return _seq_output_schema(self.steps)

def _seq_input_schema(steps: list[Component]) -> Type[BaseModel]:
    first = steps[0]
    if len(steps) == 1:
        return first.input_schema()
    elif isinstance(first, SequentialSchema):
        return first.seq_input_schema(_seq_input_schema(steps[1:]))
    return first.input_schema()

def _seq_output_schema(steps: list[Component]) -> Type[BaseModel]:
    last = steps[-1]
    if len(steps) == 1:
        return last.input_schema()
    elif isinstance(last, SequentialSchema):
        return last.seq_output_schema(_seq_output_schema(steps[:-1]))
    return last.output_schema()