"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/executor.py
"""

import asyncio
import concurrent.futures
from contextlib import ExitStack
from contextvars import copy_context
import sys
from types import TracebackType
from typing import AsyncContextManager, Awaitable, Callable, ContextManager, Optional, Protocol, Type

from flowstack.flows.errors import GraphInterrupt
from flowstack.utils.threading import get_executor

class Submit[**P, T](Protocol):
    def __call__(
        self,
        function: Callable[P, T],
        *args: *P.args,
        __name__: Optional[str] = None,
        __cancel_on_exit__: bool = False,
        **kwargs: P.kwargs
    ) -> concurrent.futures.Future[T]:
        pass

class AsyncSubmit[**P, T](Protocol):
    def __call__(
        self,
        function: Callable[P, Awaitable[T]],
        *args: *P.args,
        __name__: Optional[str] = None,
        __cancel_on_exit__: bool = False,
        **kwargs: P.kwargs
    ) -> asyncio.Task[T]:
        pass

class BackgroundExecutor(ContextManager):
    def __init__(self, max_workers: Optional[int] = None):
        self.stack = ExitStack()
        self.executor = self.stack.enter_context(get_executor(max_workers=max_workers))
        self.tasks: dict[concurrent.futures.Future, bool] = {}

    def __enter__(self) -> Submit:
        return self._submit

    def _submit[**P, T](
        self,
        function: Callable[P, T],
        *args: *P.args,
        __name__: Optional[str] = None,
        __cancel_on_exit__: bool = False,
        **kwargs: P.kwargs
    ) -> concurrent.futures.Future[T]:
        task = self.executor.submit(function, *args, **kwargs)
        self.tasks[task] = __cancel_on_exit__
        task.add_done_callback(task)
        return task

    def _done(self, task: concurrent.futures.Future) -> None:
        try:
            task.result()
        except GraphInterrupt:
            self.tasks.pop(task)
        except BaseException:
            pass
        else:
            self.tasks.pop(task)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        # cancel all tasks that should be cancelled
        for task, cancel in self.tasks.items():
            if cancel:
                task.cancel()
        # wait for all tasks to finish
        if tasks := {task for task in self.tasks if not task.done()}:
            concurrent.futures.wait(tasks)
        # shutdown the executor
        self.stack.__exit__(exc_type, exc_val, exc_tb)
        # re-raise the first exception that occured in a task
        if exc_type is None:
            # is there's already an exception being raised, don't raise another one
            for task in self.tasks:
                try:
                    task.result()
                except concurrent.futures.CancelledError:
                    pass
        return None

class AsyncBackgroundExecutor(AsyncContextManager):
    def __init__(self):
        self.tasks: dict[asyncio.Task, bool] = {}
        self.context_not_supported = sys.version_info < (3, 11)
        self.sentinel = object()

    async def __aenter__(self) -> AsyncSubmit:
        return self._submit

    def _submit[**P, T](
        self,
        function: Callable[P, Awaitable[T]],
        *args: *P.args,
        __name__: Optional[str] = None,
        __cancel_on_exit__: bool = False,
        **kwargs: P.kwargs
    ) -> asyncio.Task[T]:
        coro = function(*args, **kwargs)
        if self.context_not_supported:
            task = asyncio.create_task(coro, name=__name__)
        else:
            task = asyncio.create_task(coro, name=__name__, context=copy_context())
        self.tasks[task] = __cancel_on_exit__
        task.add_done_callback(self._done)
        return task

    def _done(self, task: asyncio.Task) -> None:
        try:
            task.result()
        except GraphInterrupt:
            self.tasks.pop(task)
        except BaseException:
            pass
        else:
            self.tasks.pop(task)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        return await asyncio.shield(self._exit(exc_type, exc_val, exc_tb))

    async def _exit(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        # cancel all tasks that should be cancelled
        for task, cancel in self.tasks.items():
            if cancel:
                task.cancel(self.sentinel)
        # wait for all tasks to finish
        if tasks := {task for task in self.tasks if not task.done()}:
            await asyncio.wait(tasks)
        # re-raise the first exception that occured in a task
        if exc_type:
            for task in self.tasks:
                try:
                    task.result()
                except asyncio.CancelledError:
                    pass