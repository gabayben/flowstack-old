import inspect
from typing import Any, Callable, Type, Union, get_args, get_origin

from overrides.typing_utils import get_type_hints, issubtype

from flowstack.typing import CallableType, Effect

def get_callable_type(func: Callable) -> CallableType:
    if is_return_type(func, Effect):
        return 'effect'
    elif inspect.isasyncgenfunction(func):
        return 'aiter'
    elif inspect.isgeneratorfunction(func):
        return 'iter'
    elif inspect.iscoroutinefunction(func):
        return 'ainvoke'
    return 'invoke'

def get_return_type[R](func: Callable[..., R]) -> Type[R]:
    return get_type_hints(func)['return']

def is_return_type[R, T](func: Callable[..., R], type_: Type[T]) -> bool:
    return issubtype(get_return_type(func), type_)

def get_members[T](obj: object, type_: Type[T]) -> list[tuple[str, T]]:
    return inspect.getmembers(obj, lambda x: isinstance(x, type_))

def is_typed_dict(type_: Type) -> bool:
    return type_.__class__.__name__ == '_TypedDictMeta'

def is_named_tuple(type_: Type) -> bool:
    return issubclass(type_, tuple) and hasattr(type_, '_asdict') and hasattr(type_, '_fields')

def is_not_required(type_: Type) -> bool:
    return type_.__name__ == 'NotRequired'

def types_are_compatible(source, target) -> bool:
    if source == target or target is Any:
        return True
    if source is Any:
        return False

    try:
        if issubclass(source, target):
            return True
    except TypeError:
        pass

    source_origin = get_origin(source)
    target_origin = get_origin(target)

    if source_origin is not Union and target_origin is Union:
        return any(types_are_compatible(source, union_arg) for union_arg in get_args(target))

    if not source_origin or not target_origin or source_origin != target_origin:
        return False

    source_args = get_args(source)
    target_args = get_args(target)
    if len(source_args) > len(target_args):
        return False

    return all(types_are_compatible(*args) for args in zip(source_args, target_args))