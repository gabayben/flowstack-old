from abc import ABC
from typing import AsyncIterator, Generic, Iterator, Optional, Sequence, Type, TypeVar, Union, override

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import All

from flowstack.core import Component
from flowstack.utils.reflection import get_type_arg

_State = TypeVar('_State')
_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Workflow(Component[Union[_State, _Input], Union[_State, _Output]], Generic[_State, _Input, _Output], ABC):
    def __init__(
        self,
        name: Optional[str] = None,
        config_schema: Optional[type] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._name = name
        self._config_schema = config_schema

    @property
    def state_schema(self) -> Optional[Type[_State]]:
        return get_type_arg(self.__class__, 0)

    @property
    @override
    def input_schema(self) -> Optional[Type[_Input]]:
        return get_type_arg(self.__class__, 1)

    @property
    @override
    def output_schema(self) -> Optional[Type[_Output]]:
        return get_type_arg(self.__class__, 2)

    @property
    def graph_config_schema(self) -> Optional[type]:
        return self._config_schema

    @property
    def builder(self) -> StateGraph:
        return self._builder

    @property
    def graph(self) -> Optional[CompiledStateGraph]:
        return self._graph if hasattr(self, '_graph') else None

    @property
    def is_compiled(self) -> bool:
        return self.graph is not None

    def __post_init__(self):
        self._builder = StateGraph(
            state_schema=self.state_schema,
            config_schema=self.graph_config_schema,
            input=self.input_schema,
            output=self.output_schema
        )

    def compile(
        self,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        interrupt_before: Optional[Union[All, Sequence[str]]] = None,
        interrupt_after: Optional[Union[All, Sequence[str]]] = None,
        debug: bool = False
    ) -> None:
        self._graph = self.builder.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after,
            debug=debug
        )

    @override
    def get_name(
        self,
        suffix: Optional[str] = None,
        *,
        name: Optional[str] = None
    ) -> str:
        return self.get_name(suffix=suffix, name=name or self._name)

    def invoke(self, input: Union[_State, _Input], **kwargs) -> Union[_State, _Output]:
        self._check()
        return self.graph.invoke(input, **kwargs)

    @override
    async def ainvoke(self, input: Union[_State, _Input], **kwargs) -> Union[_State, _Output]:
        self._check()
        return await self.graph.ainvoke(input, **kwargs)

    @override
    def stream(self, input: Union[_State, _Input], **kwargs) -> Iterator[Union[_State, _Output]]:
        self._check()
        yield from self.graph.stream(input, **kwargs)

    @override
    async def astream(self, input: Union[_State, _Input], **kwargs) -> AsyncIterator[Union[_State, _Output]]:
        self._check()
        async for chunk in self.graph.astream(input, **kwargs):
            yield chunk

    def _check(self) -> None:
        if not self.is_compiled:
            raise RuntimeError(
                'Workflow is not compiled, call Workflow.compile(...) to compile it.'
            )