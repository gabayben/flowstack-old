from abc import ABC
from typing import (
    Any,
    AsyncIterator,
    Generic,
    Iterator,
    Optional,
    Sequence,
    Type,
    TypeVar,
    TypedDict,
    Union,
    Unpack,
    final
)

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import All
from pydantic import BaseModel

from flowstack.utils.reflection import get_type_arg
from flowstack.workflows import WorkflowOptions

_State = TypeVar('_State', TypedDict, BaseModel)
_Input = TypeVar('_Input', TypedDict, BaseModel)
_Output = TypeVar('_Output', TypedDict, BaseModel)

class Workflow(BaseModel, Generic[_State, _Input, _Output], ABC):
    _builder: StateGraph
    _graph: CompiledStateGraph

    @property
    def name(self) -> str:
        return self._name

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
    def config_schema(self) -> Optional[type]:
        return self._config_schema

    @property
    def builder(self) -> StateGraph:
        return self._builder

    @property
    def graph(self) -> CompiledStateGraph:
        if not self.is_compiled:
            raise RuntimeError(
                'Workflow is not compiled, run Workflow.compile(...) to compile the graph.'
            )
        return self._graph

    @property
    def is_compiled(self) -> bool:
        return hasattr(self, '_graph')

    def __init__(
        self,
        name: Optional[str] = None,
        config_schema: Optional[type] = None,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        interrupt_before: Optional[Union[All, Sequence[str]]] = None,
        interrupt_after: Optional[Union[All, Sequence[str]]] = None,
        debug: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._name = name or self.__class__.__name__
        self._config_schema = config_schema
        self._checkpointer = checkpointer
        self._interrupt_before = interrupt_before
        self._interrupt_after = interrupt_after
        self._debug = debug

    def __post_init__(self):
        self._builder = StateGraph(
            state_schema=self.state_schema,
            config_schema=self.config_schema,
            input=self.input_schema,
            output=self.output_schema
        )
        self._build()
        self._compile()

    def _build(self) -> None:
        pass

    def _compile(self) -> None:
        if self.is_compiled:
            return
        try:
            self._graph = self.builder.compile(
                checkpointer=self._checkpointer,
                interrupt_before=self._interrupt_before,
                interrupt_after=self._interrupt_after,
                debug=self._debug
            )
        except BaseException as e:
            raise RuntimeError(
                f'Unable to compile workflow {self.name}.'
            ) from e

    @final
    def invoke(
        self,
        input: Union[_State, _Input],
        **kwargs: Unpack[WorkflowOptions]
    ) -> Union[_State, _Output]:
        return self.graph.invoke(_to_dict(input), **kwargs)

    @final
    async def ainvoke(
        self,
        input: Union[_State, _Input],
        **kwargs: Unpack[WorkflowOptions]
    ) -> Union[_State, _Output]:
        return await self.graph.ainvoke(_to_dict(input), **kwargs)

    @final
    def batch(
        self,
        inputs: list[Union[_State, _Input]],
        **kwargs: Unpack[WorkflowOptions]
    ) -> list[Union[_State, _Output]]:
        return self.graph.batch(_to_dicts(inputs), **kwargs)

    @final
    async def abatch(
        self,
        inputs: list[Union[_State, _Input]],
        **kwargs: Unpack[WorkflowOptions]
    ) -> list[Union[_State, _Output]]:
        return await self.graph.abatch(_to_dicts(inputs), **kwargs)

    @final
    def stream(
        self,
        input: Union[_State, _Input],
        **kwargs: Unpack[WorkflowOptions]
    ) -> Iterator[Union[_State, _Output]]:
        yield from self.graph.stream(_to_dict(input), **kwargs)

    @final
    async def astream(
        self,
        input: Union[_State, _Input],
        **kwargs: Unpack[WorkflowOptions]
    ) -> AsyncIterator[Union[_State, _Output]]:
        async for chunk in self.graph.astream(_to_dict(input), **kwargs):
            yield chunk

    @final
    def transform(
        self,
        inputs: Iterator[Union[_State, _Input]],
        **kwargs: Unpack[WorkflowOptions]
    ) -> Iterator[Union[_State, _Output]]:
        yield from self.graph.transform(_dict_iter(inputs), **kwargs)

    @final
    async def atransform(
        self,
        inputs: AsyncIterator[Union[_State, _Input]],
        **kwargs: Unpack[WorkflowOptions]
    ) -> AsyncIterator[Union[_State, _Output]]:
        async for chunk in self.graph.atransform(await _adict_iter(inputs), **kwargs):
            yield chunk

def _to_dict(input: Union[_State, _Input]) -> dict[str, Any]:
    if isinstance(input, dict):
        return input
    elif isinstance(input, BaseModel):
        return input.model_dump()
    return {'value': input}

def _to_dicts(inputs: list[Union[_State, _Input]]) -> list[dict[str, Any]]:
    return [_to_dict(input) for input in inputs]

def _dict_iter(inputs: Iterator[Union[_State, _Input]]) -> Iterator[dict[str, Any]]:
    for chunk in inputs:
        yield _to_dict(chunk)

async def _adict_iter(inputs: AsyncIterator[Union[_State, _Input]]) -> AsyncIterator[dict[str, Any]]:
    async for chunk in inputs:
        yield _to_dict(chunk)