from typing import Any, TypeVar

_V = TypeVar('_V', int, float, str)
PendingWrite = tuple[str, str, Any]