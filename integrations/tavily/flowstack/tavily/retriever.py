from flowstack.artifacts import Artifact
from flowstack.core import Component

class TavilyApiRetriever(Component[str, list[Artifact]]):
    def run(self, query: str, **kwargs) -> list[Artifact]:
        pass