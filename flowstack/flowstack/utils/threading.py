import asyncio
from concurrent.futures import Executor, Future, ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import copy_context
from functools import partial
from typing import Any, AsyncIterator, Callable, Coroutine, Generator, Iterable, Iterator, List, Optional, cast, override

from unsync import unsync

class ContextThreadPoolExecutor(ThreadPoolExecutor):
    """
    ThreadPoolExecutor that copies the context to the child thread.
    """

    @override
    def submit[**P, T](
        self,
        __fn: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Future[T]:
        """Submit a function to the executor.

        Args:
            __fn (Callable[..., T]): The function to submit.
            *args (Any): The positional arguments to the function.
            **kwargs (Any): The keyword arguments to the function.

        Returns:
            Future[T]: The future for the function.
        """
        return super().submit(cast(
            Callable[..., T],
            partial(copy_context().run, __fn, *args, **kwargs)
        ))

    @override
    def map[T](
        self,
        fn: Callable[..., T],
        *iterables: Iterable[Any],
        timeout: Optional[float] = None,
        chunksize: int = 1
    ) -> Iterator[T]:
        contexts = [copy_context() for _ in range(len(iterables[0]))] # type: ignore[arg-type]

        def _wrapped_fn(*args):
            return contexts.pop().run(fn, *args)

        return super().map(
            _wrapped_fn,
            *iterables,
            timeout=timeout,
            chunksize=chunksize
        )

async def gated_coroutine[T](semaphore: asyncio.Semaphore, coro: Coroutine[Any, Any, T]) -> Coroutine[Any, Any, T]:
    async with semaphore:
        return await coro

async def gather_with_concurrency[T](n: Optional[int], *coros: Coroutine[Any, Any, T]) -> List[T]:
    if n is None:
        return list(await asyncio.gather(*coros))

    semaphore = asyncio.Semaphore(value=n)

    return list(await asyncio.gather(
        *(gated_coroutine(semaphore, coro) for coro in coros)
    ))

@contextmanager
def get_executor(max_workers: Optional[int] = None) -> Generator[Executor, None, None]:
    """Get an executor for a config.

    Yields:
        Generator[Executor, None, None]: The executor.
    """
    with ContextThreadPoolExecutor(max_workers=max_workers) as executor:
        yield executor

def run_sync[T](
    coroutine: Coroutine[Any, Any, T],
    max_workers: int | None = None
) -> T:
    context = copy_context()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future: Future[T] = executor.submit(context.run, asyncio.run, coroutine) # type: ignore[call-args]
            return cast(T, future.result())
    else:
        return context.run(asyncio.run, coroutine)

async def run_async[T](
    func: Callable[..., T],
    *args,
    **kwargs
) -> T:
    return await asyncio.get_running_loop().run_in_executor(
        None,
        partial(func, **kwargs),
        *args
    )

def run_sync_iter[T](
    func: Callable[..., AsyncIterator[T]],
    *args,
    **kwargs
) -> Iterator[T]:
    @unsync
    async def _aiter() -> list[T]:
        return [item async for item in func(*args, **kwargs)]
    yield from _aiter().result()

async def run_async_iter[T](
    func: Callable[..., Iterator[T]],
    *args,
    **kwargs
) -> AsyncIterator[T]:
    loop = asyncio.get_running_loop()
    iterator = await loop.run_in_executor(None, partial(func, **kwargs), *args)
    while True:
        if item := await loop.run_in_executor(None, next, iterator, None):
            yield item
        else:
            break