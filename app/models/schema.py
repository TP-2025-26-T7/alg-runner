from typing import Optional, Protocol
from functools import cached_property
from math import pi, dist

from pydantic import BaseModel, ConfigDict, Field, constr, conint, confloat, model_validator
from shapely.geometry import LineString, Polygon, Point

class Road(BaseModel):
    id: constr(min_length=1, max_length=64)
    polyline: tuple[tuple[float, float], ...]
    recommended_speed: float

    junction_start_id: Optional[constr(min_length=1, max_length=64)] = None
    junction_end_id: Optional[constr(min_length=1, max_length=64)] = None

    @cached_property
    def geometry(self) -> LineString:
        return LineString(self.polyline)

    def __len__(self) -> int:
        return len(self.polyline)

    def __getitem__(self, index: int) -> tuple[float, float]:
        return self.polyline[index]

    def __hash__(self) -> int:
        return hash(self.id)

    def __iter__(self):
        return iter(self.polyline)

    def __contains__(self, item) -> bool:
        return item in self.polyline


class RoadConnection(Road):
    """
    Pseudo road on the inside of the junction connecting two roads
    """
    road_a_id: constr(min_length=1, max_length=64)
    road_b_id: constr(min_length=1, max_length=64)


class Junction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    junction_id: constr(min_length=1, max_length=64)
    connected_roads_count: conint(ge=0, le=2**32 - 1) = 0 # uint32_t
    connected_roads_ids: list[constr(min_length=1, max_length=64)] = Field(default_factory=list)
    road_connections: list[RoadConnection] = Field(default_factory=list) # pseudo roads between connected paths
    x: Optional[float] = None
    y: Optional[float] = None

    junction_size: float = Field(default=1)

    polygon: Optional[Polygon] = None

    @model_validator(mode="after")
    def _default_polygon(self):
        if self.polygon is None:
            half = self.junction_size / 2
            self.polygon = Polygon([(self.x - half, self.y - half),
                                    (self.x + half, self.y - half),
                                    (self.x + half, self.y + half),
                                    (self.x - half, self.y + half)])
        return self

    def __hash__(self):
        return hash(self.junction_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Junction):
            return False
        return self.junction_id == other.junction_id

    def is_point_inside(self, x: float, y: float) -> bool:
        if not self.polygon:
            return False
        return self.polygon.contains(Point(x, y))

    def get_roads_connection(self, road_a_id: str, road_b_id: str) -> Optional[RoadConnection]:
        for connection in self.road_connections:
            if (connection.road_a_id == road_a_id and connection.road_b_id == road_b_id) \
                    or (connection.road_a_id == road_b_id and connection.road_b_id == road_a_id):
                return connection

    def crossing_segments_count(self, start_road_id: str, target_road_id: str) -> int:
        """
        Going from S to T requires the car to go through segments D, B and A (3 segments), occupying 3/4 of the junction capacity.

        Example::

                |  |  |
            ____|__|__|____
            T   | A| B|
            ____|__|__|____
                | C| D|
            ____|__|__|____
                |  |  |
                |  | S|

        The connected roads are arranged in clockwise order, so it's easy to calculate the segments.

        :param start_road_id: ID of the road the car is coming from
        :param target_road_id: ID of the road the car is going to
        :return: Number of segments the car will cross inside the junction
        """

        if not self.connected_roads_ids:
            return 0

        start_index = -1
        target_index = -1
        for i, road_id in enumerate(self.connected_roads_ids):
            if road_id == start_road_id:
                start_index = i
            if road_id == target_road_id:
                target_index = i
        if start_index == -1 or target_index == -1:
            return 0
        if target_index >= start_index:
            return target_index - start_index
        else:
            return len(self.connected_roads_ids) - (start_index - target_index)


class Car(BaseModel):
    """
    Representation of a car in the algorithm.

    Notes:

    - **speed** & **acceleration**: units per second

    - **wheel_rotation**: radians (0 to 2pi)

    - **rotation**: radians (0 to 2pi); Geographical orientation

    - **target_road_id**: Provide only when sending the car first time.

    - **target_road_id** & **seconds_in_traffic**: Loaded from cache.

    - **road** & **next_junction** are calculated at runtime, CAN'T be provided by the user
    """
    model_config = ConfigDict(extra="ignore")

    car_id: constr(min_length=1, max_length=64)
    x: float
    y: float
    speed: float = 0.0  # in units per second
    wheel_rotation: confloat(ge=0, le=2 * pi) = 0.0
    rotation: confloat(ge=0, le=2 * pi) = 0.0
    acceleration: float = 0.0

    # Optional routing data coming from SUMO / central-unit
    next_junction_id: Optional[str] = None
    next_junction_x: Optional[float] = None
    next_junction_y: Optional[float] = None
    lane_id: Optional[str] = None
    road_id: Optional[str] = None

    target_road_id: Optional[constr(min_length=1, max_length=64)] = None
    seconds_in_traffic: float = 0.0

    next_junction: Optional[Junction] = Field(default=None, exclude=True)
    road: Optional[Road] = Field(default=None, exclude=True)

    def distance_from_next_junction(self, simple_mode: bool = True) -> Optional[float]:
        """
        Calculate distance from the car to its next junction.
        :param simple_mode: If True, use simple airline distance. If False, use road geometry for more precise calculation.
        :return: Distance in units, or None if next_junction or road is not set.
        """
        if not self.next_junction or not self.road:
            return None
        if simple_mode:
            return ((self.x - self.next_junction.x) ** 2 + (self.y - self.next_junction.y) ** 2) ** 0.5

        line = self.road.geometry
        # how far along the road the car is
        car_distance = line.project((self.x, self.y))

        # how far along the road the junction is (0 or the end)
        start_dist = dist((self.next_junction.x, self.next_junction.y), line.coords[0])
        end_dist = dist((self.next_junction.x, self.next_junction.y), line.coords[-1])
        junction_distance = 0 if start_dist < end_dist else line.length

        return abs(junction_distance - car_distance)

    def __hash__(self):
        return hash(self.car_id)

    def __eq__(self, other):
        if not isinstance(other, Car):
            return False
        return self.car_id == other.car_id


class CarCache(BaseModel):
    """
    Stores cached data for a car to optimize calculations during the algorithm run.
    """
    car_id: constr(min_length=1, max_length=64)
    seconds_in_traffic: float = 0.0
    target_road_id: Optional[str] = None

    def __hash__(self):
        return hash(self.car_id)

    def __eq__(self, other):
        if not isinstance(other, Car):
            return False
        return self.car_id == other.car_id


class Algorithm(Protocol):
    def __call__(self, cars: list[Car], junctions: list[Junction], duration_s: float, **kwargs) -> list[Car]:
        ...