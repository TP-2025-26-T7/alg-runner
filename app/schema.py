from pydantic import BaseModel, constr, conint

class Car(BaseModel):
    car_id: constr(min_length=1, max_length=64)
    x: float
    y: float
    next_junction_x: float
    next_junction_y: float
    next_junction_id: constr(min_length=1, max_length=64)
    speed: float
    acceleration: float
    road: constr(min_length=1, max_length=64)
    lane: constr(min_length=1, max_length=64)


class Edge(BaseModel):
    value: constr(min_length=1, max_length=64)


class Junction(BaseModel):
    junction_id: constr(min_length=1, max_length=64)
    edge_count: conint(ge=0, le=2**32 - 1) # uint32_t
    edges: list[Edge]