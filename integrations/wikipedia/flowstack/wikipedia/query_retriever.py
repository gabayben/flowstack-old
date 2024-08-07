import logging
from typing import Optional

from wikipedia import wikipedia

from flowstack.artifacts import Artifact, ArtifactMetadata, Text
from flowstack.core import Component

logger = logging.getLogger(__name__)

class WikipediaQueryRetriever(Component[str, list[Artifact]]):
    def __call__(
        self,
        query: str,
        results: Optional[int] = None,
        proceed_on_failure: Optional[bool] = None,
        **kwargs
    ) -> list[Artifact]:
        results = results if results is not None else 5
        proceed_on_failure = proceed_on_failure if proceed_on_failure is not None else True
        titles = wikipedia.search(query, results=results if proceed_on_failure else results + 5)
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
                if proceed_on_failure and len(documents) == results:
                    break
            except:
                logger.info(f'Unable to fetch page with title {title}.')
        return documents