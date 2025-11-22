from .schema import *
from typing import Optional
from pydantic import BaseModel, Field

class DispatchRequest(BaseModel):
    junctions: Optional[list[Junction]] = Field(default_factory=list)
    cars: list[Car] = Field(default_factory=list)