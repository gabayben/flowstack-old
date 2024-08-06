from functools import partial
from typing import Optional

from flowstack.artifacts import Artifact
from flowstack.core import Effect, Effects
from flowstack.ingest import ArtifactLoader
from flowstack.wikipedia import WikipediaRetriever

class WikipediaLoader(ArtifactLoader):
    def __init__(self, query: str, results: Optional[int] = None):
        self._retriever = WikipediaRetriever()
        self._query = query
        self._results = results if results is not None else 5

    def __call__(self, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._retriever.invoke, self._query, results=self._results, **kwargs),
            ainvoke=partial(self._retriever.ainvoke, self._query, results=self._results, **kwargs),
            iter_=partial(self._retriever.stream, self._query, results=self._results, **kwargs),
            aiter_=partial(self._retriever.astream, self._query, results=self._results, **kwargs)
        )