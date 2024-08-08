import enum
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, TypeVar, Union

from langchain_core.runnables.graph import Graph
from numpy import ndarray
import tenacity

_T = TypeVar('_T')
_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class SchemaType(enum.StrEnum):
    PYDANTIC = 'pydantic'
    TYPED_DICT = 'typed_dict'
    NAMED_TUPLE = 'named_tuple'
    VALUE = 'value'

MetadataType = Union[dict[str, Any], list[dict[str, Any]]]
Embedding = ndarray

SyncFunction = Callable[[_Input, ...], _Output]
AsyncFunction = Callable[[_Input, ...], Awaitable[_Output]]
BatchFunction = Callable[[list[_Input], ...], list[_Output]]
AsyncBatchFunction = Callable[[list[_Input], ...], Awaitable[list[_Output]]]
StreamFunction = Callable[[_Input, ...], Iterator[_Output]]
AsyncStreamFunction = Callable[[_Input, ...], AsyncIterator[_Output]]
TransformFunction = Callable[[Iterator[_Input], ...], Iterator[_Output]]
AsyncTransformFunction = Callable[[AsyncIterator[_Input], ...], AsyncIterator[_Output]]

RetryStrategy = tenacity.retry_base | Callable[[tenacity.RetryCallState], bool]
StopStrategy = tenacity.stop.stop_base | Callable[[tenacity.RetryCallState], bool]
WaitStrategy = tenacity.wait.wait_base | Callable[[tenacity.RetryCallState], int | float]
AfterRetryFailure = Callable[[tenacity.RetryCallState], None]

DrawableGraph = Graph