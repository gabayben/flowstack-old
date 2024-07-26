"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/graphs/state.py
"""

from flowstack.flows.builders import CompiledFlow, Flow

class StateFlow(Flow):
    pass

class CompiledStateFlow(CompiledFlow):
    builder: StateFlow