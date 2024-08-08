from flowstack.artifacts import Artifact
from flowstack.interfaces import Retriever

class TavilyApiRetriever(Retriever):
    def retrieve(self, query: str, **kwargs) -> list[Artifact]:
        pass