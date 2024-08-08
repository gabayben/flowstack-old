import logging
from typing import Optional

from wikipedia import wikipedia

from flowstack.artifacts import Artifact, ArtifactMetadata, Text
from flowstack.components.retrievers.base import BaseRetriever

logger = logging.getLogger(__name__)

class WikipediaQueryRetriever(BaseRetriever):
    def __init__(
        self,
        results: Optional[int] = None,
        replace_failed: Optional[bool] = None
    ):
        self._results = results if results is not None else 5
        self._replace_failed = replace_failed if replace_failed is not None else True

    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        titles = wikipedia.search(
            str(query),
            results=self._results if not self._replace_failed else self._results + 5
        )
        artifacts = []
        for title in titles:
            try:
                page = wikipedia.page(title=title)
                artifacts.append(Text(
                    page.content,
                    metadata=ArtifactMetadata(
                        pageid=page.pageid,
                        parent_id=page.parent_id,
                        title=page.title,
                        url=page.url
                    )
                ))
                if self._replace_failed and len(artifacts) == self._results:
                    break
            except:
                logger.info(f'Unable to fetch page with title {title}.')
        return artifacts