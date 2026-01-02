from pydantic import BaseModel, Field, AliasChoices
from .schema import *

class DispatchRequest(BaseModel):
    algorithm_name: str = Field(
        default="fifo",
        validation_alias=AliasChoices("algorithm_name", "alg_name", "algorithm", "alg"), # Support multiple alias names to prevent mistakes
    )
    cars: list[Car] = Field(default_factory=list)
    junctions: list[Junction] = Field(default_factory=list)
    next_request_in_seconds: float = 0.2 # Time until the next dispatch request is expected, default to 200ms

class SetupRequest(BaseModel):
    junctions: list[Junction] = Field(default_factory=list)
    roads: list[Road] = Field(default_factory=list)
    car_targets: dict[str, str] = Field(default_factory=dict) # car_id -> target_road_id
    overwrite: bool = False