from typing import Optional
from functools import cached_property

from pydantic import BaseModel, constr, conint
from shapely.geometry import LineString

class Car(BaseModel):
    car_id: constr(min_length=1, max_length=64)
    x: float
    y: float
    next_junction_x: float
    next_junction_y: float
    next_junction_id: constr(min_length=1, max_length=64)
    speed: float
    acceleration: float
    road: constr(min_length=1, max_length=64) # TODO: Find what the fuck this means
    lane: constr(min_length=1, max_length=64) # TODO: Find what the fuck this means

    def __hash__(self):
        return hash(self.car_id)

    def __eq__(self, other):
        if not isinstance(other, Car):
            return False
        return self.car_id == other.car_id


class Road(BaseModel):
    id: constr(min_length=1, max_length=64)
    polyline: list[list[float]]

    @cached_property
    def geometry(self) -> LineString:
        return LineString(self.polyline)


class Junction(BaseModel):
    junction_id: constr(min_length=1, max_length=64)
    edge_count: conint(ge=0, le=2**32 - 1) # uint32_t
    edges: list[Road]
    x: Optional[float] = None
    y: Optional[float] = None

    def __hash__(self):
        return hash(self.junction_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Junction):
            return False
        return self.junction_id == other.junction_id

