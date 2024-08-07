from enum import StrEnum
from typing import Union

from pydantic import StrictFloat, StrictInt, StrictStr

from flowstack.typing import Serializable

class FilterOperator(StrEnum):
    EQ = '=='
    NE = '!='
    GT = '>'
    GTE = '>='
    LT = '<'
    LTE = '<='
    IN = 'in'
    NIN = 'nin'
    ANY = 'any'
    ALL = 'all'
    CONTAINS = 'contains'
    TEXT_MATCH = 'text_match'

class FilterCondition(StrEnum):
    AND = 'and'
    OR = 'or'

class MetadataFilter(Serializable):
    key: str
    value: Union[StrictInt, StrictFloat, StrictStr, list[StrictStr]]
    operator: FilterOperator = FilterOperator.EQ

class MetadataFilters(Serializable):
    filters: list[Union[MetadataFilter, 'MetadataFilters']]
    condition: FilterCondition = FilterCondition.AND

class MetadataFilterInfo(Serializable):
    name: str
    type: str
    description: str