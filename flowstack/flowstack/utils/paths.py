import datetime as dt
import mimetypes
import os
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

from flowstack.utils.constants import DATETIMETZ_FORMAT

CUSTOM_MIME_TYPE_MAPPINGS: dict[str, str] = {
    '.markdown': 'llm/markdown',
    '.md': 'llm/markdown'
}

def get_mime_type(path: Path) -> str | None:
    extension = path.suffix.lower()
    mime_type = mimetypes.guess_type(path.as_posix())[0]
    return CUSTOM_MIME_TYPE_MAPPINGS.get(extension, mime_type)

def is_valid_url(url: str) -> bool:
    r = urlparse(url)
    return all([r.scheme in ['http', 'https'], r.netloc])

def validate_url(url: str) -> None:
    if not is_valid_url(url):
        raise ValueError(f'Invalid URL: {url}.')

def last_modified_date(path: Union[str, Path]) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    modified_date = dt.datetime.fromtimestamp(os.path.getmtime(path))
    return dt.datetime.strftime(modified_date, DATETIMETZ_FORMAT)