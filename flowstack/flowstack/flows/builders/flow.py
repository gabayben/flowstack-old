"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/graphs/graph.py
"""

from flowstack.flows.pregel import Pregel

class Flow:
    pass

class CompiledFlow(Pregel):
    builder: Flow