import importlib
from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel

from flowstack.utils.constants import SCHEMA_TYPE

_T = TypeVar('_T', bound=BaseModel)

class PydanticRegistry(Generic[_T]):
    def __init__(self):
        self.types: dict[str, Type[_T]] = {}

    def deserialize(self, data: dict[str, Any], name: Optional[str] = None) -> _T:
        name = name or data.pop(SCHEMA_TYPE, None)
        if name is None:
            raise ValueError(f"'{SCHEMA_TYPE}' field not found in data.")

        if name not in self.types:
            modname, _, clsname = name.rpartition('.')
            mod = importlib.import_module(modname)
            self.types[name] = getattr(mod, clsname)

        return self.types[name].model_validate(data)