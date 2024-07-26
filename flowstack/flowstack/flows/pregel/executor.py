"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/executor.py
"""

import asyncio
import concurrent.futures
from contextlib import ExitStack
import sys
from types import TracebackType
from typing import AsyncContextManager, Callable, ContextManager, Optional, Protocol, Type

from flowstack.utils.threading import get_executor

class Submit[**P, T](Protocol):
    def __call__(
        self,
        function: Callable[P, T],
        *args: P.args,
        __name__: Optional[str] = None,
        __cancel_on_exit__: bool = False,
        **kwargs: P.kwargs
    ) -> concurrent.futures.Future[T]:
        pass

class BackgroundExecutor(ContextManager):
    def __init__(self, max_workers: Optional[int] = None):
        self.stack = ExitStack()
        self.executor = self.stack.enter_context(get_executor(max_workers=max_workers))
        self.tasks: dict[concurrent.futures.Future, bool] = {}

    def __enter__(self) -> 'submit':
        self.submit

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        pass

    def submit[**P, T](
        self,
        function: Callable[P, T],
        *args: P.args,
        __name__: Optional[str] = None,
        __cancel_on_exit__: bool = False,
        **kwargs: P.kwargs
    ) -> concurrent.futures.Future[T]:
        task = self.executor.submit(function, *args, **kwargs)
        self.tasks[task] = __cancel_on_exit__
        task.add_done_callback(task)
        return task

    def done(self, task: concurrent.futures.Future) -> None:
        pass

class AsyncBackgroundExecutor(AsyncContextManager):
    def __init__(self):
        self.tasks: dict[asyncio.Task, bool] = {}
        self.context_not_supported = sys.version_info < (3, 11)
        self.sentinel = object()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        pass