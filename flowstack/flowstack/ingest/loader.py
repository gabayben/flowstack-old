from abc import ABC, abstractmethod
from functools import cached_property, partial
from typing import AsyncIterator, Iterator, final

from flowstack.artifacts import Artifact
from flowstack.core import Effect, Effects, ReturnType
from flowstack.typing import CallableType
from flowstack.utils.reflection import get_callable_type

class ArtifactLoader(ABC):
    @cached_property
    def callable_type(self) -> CallableType:
        return get_callable_type(self.__call__)

    @abstractmethod
    def __call__(self, **kwargs) -> ReturnType[list[Artifact]]:
        pass

    @final
    def effect(self, **kwargs) -> Effect[list[Artifact]]:
        callable_type = self.callable_type
        if callable_type == 'effect':
            return self(**kwargs)
        function = partial(self, **kwargs)
        if callable_type == 'aiter':
            return Effects.AsyncIterator(function)
        elif callable_type == 'iter':
            return Effects.Iterator(function)
        elif callable_type == 'ainvoke':
            return Effects.Async(function)
        return Effects.Sync(function)

    @final
    def load(self, **kwargs) -> list[Artifact]:
        return self.effect(**kwargs).invoke()

    @final
    async def aload(self, **kwargs) -> list[Artifact]:
        return await self.effect(**kwargs).ainvoke()

    @final
    def lazy_load(self, **kwargs) -> Iterator[list[Artifact]]:
        yield from self.effect(**kwargs).iter()

    @final
    async def alazy_load(self, **kwargs) -> AsyncIterator[list[Artifact]]:
        async for chunk in self.effect(**kwargs).aiter(): #type: ignore
            yield chunk