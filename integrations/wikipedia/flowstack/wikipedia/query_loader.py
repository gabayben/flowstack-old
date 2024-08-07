from functools import partial
from typing import Optional

from flowstack.artifacts import Artifact
from flowstack.core import Effect, Effects
from flowstack.ingest import ArtifactLoader
from flowstack.wikipedia import WikipediaQueryRetriever

class WikipediaQueryLoader(ArtifactLoader):
    def __init__(
        self,
        query: str,
        results: Optional[int] = None,
        proceed_on_failure: Optional[bool] = None
    ):
        self._retriever = WikipediaQueryRetriever()
        self._query = query
        self._results = results
        self._proceed_on_failure = proceed_on_failure

    def __call__(self, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(
                self._retriever.invoke,
                self._query,
                results=self._results,
                proceed_on_failure=self._proceed_on_failure,
                **kwargs
            ),
            ainvoke=partial(
                self._retriever.ainvoke,
                self._query,
                results=self._results,
                proceed_on_failure=self._proceed_on_failure,
                **kwargs
            ),
            iter_=partial(
                self._retriever.stream,
                self._query,
                results=self._results,
                proceed_on_failure=self._proceed_on_failure,
                **kwargs
            ),
            aiter_=partial(
                self._retriever.astream,
                self._query,
                results=self._results,
                proceed_on_failure=self._proceed_on_failure,
                **kwargs
            )
        )