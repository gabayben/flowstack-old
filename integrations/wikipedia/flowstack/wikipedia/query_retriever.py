import logging
from typing import Optional

from langchain_core.runnables import RunnableSerializable
from wikipedia import wikipedia

from flowstack.artifacts import Artifact, ArtifactMetadata, Text

logger = logging.getLogger(__name__)

class WikipediaQueryRetriever(RunnableSerializable[str, list[Artifact]]):
    def __init__(
        self,
        results: Optional[int] = None,
        proceed_on_failure: Optional[bool] = None
    ):
        self._results = results if results is not None else 5
        self._proceed_on_failure = proceed_on_failure if proceed_on_failure is not None else True

    def invoke(self, query: str, **kwargs) -> list[Artifact]:
        titles = wikipedia.search(query, results=self._results if self._proceed_on_failure else self._results + 5)
        documents = []
        for title in titles:
            try:
                page = wikipedia.page(title=title)
                documents.append(Text(
                    page.content,
                    metadata=ArtifactMetadata(
                        pageid=page.pageid,
                        parent_id=page.parent_id,
                        title=page.title,
                        url=page.url
                    )
                ))
                if self._proceed_on_failure and len(documents) == self._results:
                    break
            except:
                logger.info(f'Unable to fetch page with title {title}.')
        return documents