from pydantic import BaseModel, ConfigDict

class Serializable(BaseModel):
    model_config = ConfigDict(
        extra='allow',
        arbitrary_types_allowed=True
    )