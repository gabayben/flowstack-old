from functools import partial
from typing import Iterator, Optional, Sequence, Type, TypeVar, override

from flowstack.core import Component, ComponentLike, DecoratorBase, Effect, Effects, coerce_to_component

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Fallbacks(DecoratorBase[_Input, _Output]):
    fallbacks: Sequence[Component[_Input, _Output]]
    exceptions_to_handle: tuple[Type[BaseException], ...]

    @property
    def _components(self) -> Iterator[Component[_Input, _Output]]:
        yield self.bound
        yield from self.fallbacks

    def __init__(
        self,
        bound: Component[_Input, _Output],
        fallbacks: Sequence[ComponentLike[_Input, _Output]],
        exceptions_to_handle: Optional[tuple[Type[BaseException], ...]] = None
    ):
        super().__init__(
            bound=bound,
            fallbacks=[coerce_to_component(fallback) for fallback in fallbacks],
            exceptions_to_handle=exceptions_to_handle or (Exception,)
        )

    @override
    def run(self, input: _Input, **kwargs) -> Effect[_Output]:
        return Effects.From(
            invoke=partial(self._invoke, input, **kwargs),
            ainvoke=partial(self._ainvoke, input, **kwargs)
        )

    def _invoke(self, input: _Input, **kwargs) -> _Output:
        first_error: Optional[BaseException] = None
        last_error: Optional[BaseException] = None

        for comp in self._components:
            try:
                output = comp.invoke(
                    input,
                    first_error=first_error,
                    last_error=last_error,
                    **kwargs
                )
            except self.exceptions_to_handle as e:
                first_error = first_error or e
                last_error = e
            else:
                return output

        if first_error is None:
            raise ValueError('No error stored at end of fallbacks.')
        raise first_error

    async def _ainvoke(self, input: _Input, **kwargs) -> _Output:
        first_error: Optional[BaseException] = None
        last_error: Optional[BaseException] = None

        for comp in self._components:
            try:
                output = await comp.ainvoke(
                    input,
                    first_error=first_error,
                    last_error=last_error,
                    **kwargs
                )
            except self.exceptions_to_handle as e:
                first_error = first_error or e
                last_error = e
            except BaseException as e:
                raise e
            else:
                return output

        if first_error is None:
            raise ValueError('No error stored at end of fallbacks.')
        raise first_error