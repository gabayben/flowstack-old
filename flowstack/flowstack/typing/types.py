import enum
from typing import Any, Callable, Literal, TypeVar, Union

from numpy import ndarray
import tenacity

_T = TypeVar('_T')

class SchemaType(enum.StrEnum):
    PYDANTIC = 'pydantic'
    TYPED_DICT = 'typed_dict'
    NAMED_TUPLE = 'named_tuple'
    VALUE = 'value'

CallableType = Literal['invoke', 'ainvoke', 'iter', 'aiter', 'effect']
MetadataType = Union[dict[str, Any], list[dict[str, Any]]]
Embedding = ndarray

RetryStrategy = tenacity.retry_base | Callable[[tenacity.RetryCallState], bool]
StopStrategy = tenacity.stop.stop_base | Callable[[tenacity.RetryCallState], bool]
WaitStrategy = tenacity.wait.wait_base | Callable[[tenacity.RetryCallState], int | float]
AfterRetryFailure = Callable[[tenacity.RetryCallState], None]