from typing import AsyncIterator, Generic, Iterator, Optional, Sequence, Type, TypeVar, TypedDict, Union

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import All
from pydantic import BaseModel

from flowstack.utils.reflection import get_type_arg

_State = TypeVar('_State', bound=(TypedDict, BaseModel, None))
_Input = TypeVar('_Input', bound=(TypedDict, BaseModel, None))
_Output = TypeVar('_Output', bound=(TypedDict, BaseModel, None))
_Config = TypeVar('_Config')

class Workflow(BaseModel, Generic[_State, _Input, _Output, _Config]):
    @property
    def state_schema(self) -> Optional[Type[_State]]:
        return get_type_arg(self.__class__, 0)

    @property
    def input_schema(self) -> Optional[Type[_Input]]:
        return get_type_arg(self.__class__, 1)

    @property
    def output_schema(self) -> Optional[Type[_Output]]:
        return get_type_arg(self.__class__, 2)

    @property
    def config_schema(self) -> Optional[Type[_Config]]:
        return get_type_arg(self.__class__, 3)

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
            config_schema=self.config_schema,
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

    def invoke(self, input: _State, **kwargs) -> _Output:
        self._check()
        return self.graph.invoke(input, **kwargs)

    async def ainvoke(self, input: _State, **kwargs) -> _Output:
        self._check()
        return await self.graph.ainvoke(input, **kwargs)

    def stream(self, input: _State, **kwargs) -> Iterator[_Output]:
        self._check()
        yield from self.graph.stream(input, **kwargs)

    async def astream(self, input: _State, **kwargs) -> AsyncIterator[_Output]:
        self._check()
        async for chunk in self.graph.astream(input, **kwargs):
            yield chunk

    def _check(self) -> None:
        if not self.is_compiled:
            raise RuntimeError(
                'Workflow is not compiled, call Workflow.compile(...) to compile it.'
            )