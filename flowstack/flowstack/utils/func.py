from functools import partial, reduce
import itertools
from itertools import chain
from typing import Callable, Iterable, overload

_initial_missing = object()

def tpartial[Out](func: Callable[..., Out], /, *args, **kwargs) -> Callable[..., Out]:
    return partial(func, *args, **kwargs)

def tintersection[T](*s: Iterable[T]) -> set[T]:
    return set.intersection(*s)

def tmap[In, Out](func: Callable[[In], Out], *args: In) -> Iterable[Out]:
    return map(func, *args)

def treduce[T, S](func: Callable[[T, S], T], sequence: Iterable[S], initial: T = _initial_missing):
    return reduce(func, sequence, initial=initial)

def tproduct[T](*args: Iterable[T]) -> Iterable[tuple[T, ...]]:
    return itertools.product(*args)

def chain_iterables[T](iterables: Iterable[Iterable[T]]) -> Iterable[T]:
    return chain.from_iterable(iterables)

@overload
def tzip[A, B](
    iter1: Iterable[A],
    iter2: Iterable[B]
) -> Iterable[tuple[A, B]]: ...

@overload
def tzip[A, B, C](
    iter1: Iterable[A],
    iter2: Iterable[B],
    iter3: Iterable[C]
) -> Iterable[tuple[A, B, C]]: ...

@overload
def tzip[A, B, C, D](
    iter1: Iterable[A],
    iter2: Iterable[B],
    iter3: Iterable[C],
    iter4: Iterable[D]
) -> Iterable[tuple[A, B, C, D]]: ...

@overload
def tzip[A, B, C, D, E](
    iter1: Iterable[A],
    iter2: Iterable[B],
    iter3: Iterable[C],
    iter4: Iterable[D],
    iter5: Iterable[E]
) -> Iterable[tuple[A, B, C, D, E]]: ...

@overload
def tzip[A, B, C, D, E, F](
    iter1: Iterable[A],
    iter2: Iterable[B],
    iter3: Iterable[C],
    iter4: Iterable[D],
    iter5: Iterable[E],
    iter6: Iterable[F]
) -> Iterable[tuple[A, B, C, D, E, F]]: ...

@overload
def tzip[A, B, C, D, E, F, G](
    iter1: Iterable[A],
    iter2: Iterable[B],
    iter3: Iterable[C],
    iter4: Iterable[D],
    iter5: Iterable[E],
    iter6: Iterable[F],
    iter7: Iterable[G]
) -> Iterable[tuple[A, B, C, D, E, F, G]]: ...

@overload
def tzip[A, B, C, D, E, F, G, H](
    iter1: Iterable[A],
    iter2: Iterable[B],
    iter3: Iterable[C],
    iter4: Iterable[D],
    iter5: Iterable[E],
    iter6: Iterable[F],
    iter7: Iterable[G],
    iter8: Iterable[H]
) -> Iterable[tuple[A, B, C, D, E, F, G, H]]: ...

def tzip[*T](*iterables: Iterable[T]) -> Iterable[tuple[T]]:
    return zip(*iterables)