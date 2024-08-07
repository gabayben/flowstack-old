from langchain_core.runnables import RunnableSerializable

from flowstack.artifacts import Artifact

class TavilyApiRetriever(RunnableSerializable[str, list[Artifact]]):
    def invoke(self, query: str, **kwargs) -> list[Artifact]:
        pass