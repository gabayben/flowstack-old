from abc import ABC
from typing import Generic, Optional, Sequence, Type, TypeVar, Union

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel import All
from pydantic import BaseModel

from flowstack.utils.reflection import get_type_arg

_State = TypeVar('_State')
_Input = TypeVar('_Input')
_Output = TypeVar('_Output')

class Workflow(BaseModel, Generic[_State, _Input, _Output], ABC):
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
    def graph(self) -> Optional[CompiledStateGraph]:
        return self._graph if hasattr(self, '_graph') else None

    @property
    def is_compiled(self) -> bool:
        return self.graph is not None

    def __init__(
        self,
        name: Optional[str] = None,
        config_schema: Optional[type] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._name = name or self.__class__.__name__
        self._config_schema = config_schema

    def __post_init__(self):
        self._builder = StateGraph(
            state_schema=self.state_schema,
            config_schema=self.config_schema,
            input=self.input_schema,
            output=self.output_schema
        )
        self._build()

    def _build(self) -> None:
        pass

    def compile(
        self,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        interrupt_before: Optional[Union[All, Sequence[str]]] = None,
        interrupt_after: Optional[Union[All, Sequence[str]]] = None,
        debug: bool = False
    ) -> CompiledStateGraph:
        if self.is_compiled:
            return self.graph
        try:
            self._graph = self.builder.compile(
                checkpointer=checkpointer,
                interrupt_before=interrupt_before,
                interrupt_after=interrupt_after,
                debug=debug
            )
            return self.graph
        except BaseException as e:
            raise RuntimeError(
                f'Unable to compile workflow {self._name}.'
            ) from e