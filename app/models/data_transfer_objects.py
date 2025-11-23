from typing import Optional
from pydantic import BaseModel, Field, AliasChoices
from .schema import *

class DispatchRequest(BaseModel):
    algorithm_name: str = Field(
        default="fifo",
        validation_alias=AliasChoices("algorithm_name", "alg_name", "algorithm", "alg"), # Support multiple alias names to prevent mistakes
    )
    cars: list[Car] = Field(default_factory=list)

class JunctionsRequest(BaseModel):
    junctions: list[Junction] = Field(default_factory=list)
    overwrite: bool = False