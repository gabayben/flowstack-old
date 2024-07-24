from typing import Any, Callable, Literal, Protocol, Self, Union, runtime_checkable
import tenacity

CallableType = Literal['invoke', 'ainvoke', 'iter', 'aiter', 'effect']
StreamingChunk = tuple[str, dict[str, Any]]
StreamingCallback = Callable[[str, dict[str, Any]], None]
MetadataType = Union[dict[str, Any], list[dict[str, Any]]]

RetryStrategy = tenacity.retry_base | Callable[[tenacity.RetryCallState], bool]
StopStrategy = tenacity.stop.stop_base | Callable[[tenacity.RetryCallState], bool]
WaitStrategy = tenacity.wait.wait_base | Callable[[tenacity.RetryCallState], int | float]
AfterRetryFailure = Callable[[tenacity.RetryCallState], None]

@runtime_checkable
class Addable(Protocol):
    def __add__(self, other: Self) -> Self:
        pass