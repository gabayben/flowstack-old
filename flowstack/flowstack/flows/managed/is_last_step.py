"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/managed/is_last_step.py
"""

from typing import Annotated

from flowstack.flows.managed import ManagedValue
from flowstack.flows.typing import PregelTaskDescription
from flowstack.utils.constants import RECURSION_LIMIT

class IsLastStepValue(ManagedValue[bool]):
    def __call__(self, step: int, task: PregelTaskDescription) -> bool:
        return step == self.config[RECURSION_LIMIT] - 1

IsLastStep = Annotated[bool, IsLastStepValue]