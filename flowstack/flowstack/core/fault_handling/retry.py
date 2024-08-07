from functools import partial
from typing import Any, Optional, TypeVar, override

from tenacity import AsyncRetrying, Retrying, retry_if_exception_type, stop_after_attempt, wait_none

from flowstack.core import Component, DecoratorBase, Effect, Effects
from flowstack.typing import AfterRetryFailure, RetryStrategy, StopStrategy, WaitStrategy

_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Retry(DecoratorBase[_Input, _Output]):
    retry: RetryStrategy
    stop: StopStrategy
    wait: WaitStrategy
    after: Optional[AfterRetryFailure] = None

    @property
    def _retry_kwargs(self) -> dict[str, Any]:
        return {
            'reraise': True,
            'retry': self.retry,
            'stop': self.stop,
            'wait': self.wait,
            'after': self.after
        }

    def __init__(
        self,
        bound: Component[_Input, _Output],
        retry: Optional[RetryStrategy] = None,
        stop: Optional[StopStrategy] = None,
        wait: Optional[WaitStrategy] = None,
        after: Optional[AfterRetryFailure] = None
    ):
        super().__init__(
            bound=bound,
            retry=retry or retry_if_exception_type((Exception,)),
            stop=stop or stop_after_attempt(3),
            wait=wait or wait_none(),
            after=after
        )

    @override
    def run(self, input: _Input, **kwargs) -> Effect[_Output]:
        return Effects.From(
            invoke=partial(self._invoke, input, **kwargs),
            ainvoke=partial(self._ainvoke, input, **kwargs)
        )

    def _invoke(self, input: _Input, **kwargs) -> _Output:
        for attempt in Retrying(**self._retry_kwargs):
            with attempt:
                result = super().invoke(input, retry_state=attempt.retry_state, **kwargs)
            if attempt.retry_state.outcome and not attempt.retry_state.outcome.failed:
                attempt.retry_state.set_result(result)
        return result

    async def _ainvoke(self, input: _Input, **kwargs) -> _Output:
        async for attempt in AsyncRetrying(**self._retry_kwargs):
            with attempt:
                result = await super().ainvoke(input, retry_state=attempt.retry_state, **kwargs)
            if attempt.retry_state.outcome and not attempt.retry_state.outcome.failed:
                attempt.retry_state.set_result(result)
        return result