from typing import Any, Optional, TypedDict

class GraphNodeQuery(TypedDict, total=False):
    ids: Optional[list[str]]
    properties: Optional[dict[str, Any]]

class GraphTripletQuery(TypedDict, total=False):
    ids: Optional[list[str]]
    entity_names: Optional[list[str]]
    relation_names: Optional[list[str]]
    sources: Optional[list[str]]
    targets: Optional[list[str]]
    properties: Optional[dict[str, Any]]