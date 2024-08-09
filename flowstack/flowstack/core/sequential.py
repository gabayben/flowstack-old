from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Iterator, Optional, Type, TypeVar, Union, override

from pydantic import BaseModel, Field

from flowstack.core import Component, ComponentLike, ComponentMapping, coerce_to_component

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')
_Other = TypeVar('_Other')
_CoercibleType = Union[ComponentLike[_Input, _Output], ComponentMapping[Any, Any]]

class SequentialSchema(ABC):
    @abstractmethod
    def seq_input_schema(self, next_schema: Type[BaseModel]) -> Type[BaseModel]:
        pass

    @abstractmethod
    def seq_output_schema(self, previous_schema: Type[BaseModel]) -> Type[BaseModel]:
        pass

class Sequential(Component[_Input, _Output]):
    first: Component[_Input, Any]
    middle: list[Component] = Field(default_factory=list)
    last: Component[Any, _Output]

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
        *steps: _CoercibleType,
        first: Optional[_CoercibleType[_Input, Any]] = None,
        middle: Optional[list[_CoercibleType]] = None,
        last: Optional[_CoercibleType[Any, _Output]] = None,
        name: Optional[str] = None
    ):
        steps_flat: list[Component] = []
        if not steps:
            if first and last:
                steps_flat = (
                    [coerce_to_component(first)] +
                    [coerce_to_component(step) for step in (middle or [])] +
                    [coerce_to_component(last)]
                )
        else:
            for step in steps:
                if isinstance(step, Sequential):
                    steps_flat.extend(step.steps)
                else:
                    steps_flat.append(coerce_to_component(step))
        if len(steps_flat) < 2:
            raise ValueError(f'Sequential must have at least 2 steps, got {len(steps_flat)} steps.')
        super().__init__(
            first=steps_flat[0],
            middle=steps_flat[1:-1],
            last=steps_flat[-1],
            name=name
        )

    @override
    def __or__(self, other: _CoercibleType[_Output, _Other]) -> Component[_Input, _Other]:
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
    def __ror__(self, other: _CoercibleType[_Other, _Input]) -> Component[_Other, _Output]:
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

    @override
    def get_input_schema(self, **kwargs) -> Type[BaseModel]:
        return _seq_input_schema(self.steps, **kwargs)

    @override
    def get_output_schema(self, **kwargs) -> Type[BaseModel]:
        return _seq_output_schema(self.steps, **kwargs)

    def invoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    async def ainvoke(self, input: _Input, **kwargs) -> _Output:
        pass

    @override
    def stream(self, input: _Input, **kwargs) -> Iterator[_Output]:
        pass

    @override
    async def astream(self, input: _Input, **kwargs) -> AsyncIterator[_Output]:
        pass

    @override
    def transform(self, inputs: Iterator[_Input], **kwargs) -> Iterator[_Output]:
        pass

    @override
    async def atransform(self, inputs: AsyncIterator[_Input], **kwargs) -> AsyncIterator[_Output]:
        pass

def _seq_input_schema(steps: list[Component], **kwargs) -> Type[BaseModel]:
    first = steps[0]
    if len(steps) == 1:
        return first.get_input_schema(**kwargs)
    elif isinstance(first, SequentialSchema):
        return first.seq_input_schema(_seq_input_schema(steps[1:]))
    return first.get_input_schema(**kwargs)

def _seq_output_schema(steps: list[Component], **kwargs) -> Type[BaseModel]:
    last = steps[-1]
    if len(steps) == 1:
        return last.get_input_schema(**kwargs)
    elif isinstance(last, SequentialSchema):
        return last.seq_output_schema(_seq_output_schema(steps[:-1]))
    return last.get_output_schema(**kwargs)