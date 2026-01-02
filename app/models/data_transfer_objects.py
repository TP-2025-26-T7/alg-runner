from pydantic import BaseModel, Field, AliasChoices
from .schema import *

class DispatchRequest(BaseModel):
    """
    :param algorithm_name: Name of the dispatch algorithm to use
    :param cars: List of cars to be dispatched
    :param junctions: List of junctions in the road network
    :param next_request_in_seconds: Expected time until the next dispatch request. Default = 200ms
    """
    algorithm_name: str = Field(
        default="fifo",
        validation_alias=AliasChoices("algorithm_name", "alg_name", "algorithm", "alg"), # Support multiple alias names to prevent mistakes
    )
    cars: list[Car] = Field(default_factory=list)
    junctions: list[Junction] = Field(default_factory=list)
    next_request_in_seconds: Optional[float] = 0.2


class SetupRequest(BaseModel):
    """
    :param junctions: List of junctions to set up
    :param roads: List of roads to set up
    :param car_targets: Mapping of car IDs to their target road IDs
    :param overwrite: If True, overwrite existing junctions and roads instead of appending
    :param slowdown_zone: Distance from junctions where speed limit is lowered
    :param slowdown_rate: Rate at which speed is reduced in the slowdown zone (0 < rate < 1; e.g. 0.3 means 30% of original speed)
    """
    junctions: list[Junction] = Field(default_factory=list)
    roads: list[Road] = Field(default_factory=list)
    car_targets: dict[str, str] = Field(default_factory=dict) # car_id -> target_road_id
    overwrite: bool = False
    slowdown_zone: Optional[float] = 3.0
    slowdown_rate: Optional[float] = 0.3