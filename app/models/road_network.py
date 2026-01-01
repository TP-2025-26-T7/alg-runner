from .schema import Road
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
import math


class RoadNetwork:
    def __init__(self, roads: list[Road] = None):
        self.roads: list[Road] = roads if roads is not None else [] # roads == null ? roads : []

        if len(self.roads):
            self.tree: STRtree = STRtree([road.geometry for road in self.roads])
        else:
            self.tree: STRtree = STRtree([])

    def add_road(self, road: Road):
        self.roads.append(road)
        # Rebuild the spatial index, as it does not support add/append
        self.tree = STRtree([road.geometry for road in self.roads])

    def add_roads(self, roads: list[Road]):
        self.roads.extend(roads)
        # Rebuild the spatial index, as it does not support add/append
        self.tree = STRtree([road.geometry for road in self.roads])

    def get_road_for_point(self, x: float, y: float, buffer_radius: float = 1) -> Road | None:
        point_buffer = Point(x, y).buffer(buffer_radius)
        possible_roads = self.tree.query(point_buffer)

        if not possible_roads:
            return None

        # Need to find the closes road within the buffer in case near a junction
        closest_road = possible_roads[0]
        for road_geometry in possible_roads:
            if point_buffer.distance(road_geometry) < point_buffer.distance(closest_road):
                closest_road = road_geometry

        for road in self.roads:
            if road.geometry == closest_road:
                return road

        return None

    def get_road_end_coordinates(self, car_x, car_y, angle, buffer=0.5) -> tuple[float, float]:
        """
        :param car_x: unit consistent across the system
        :param car_y: unit consistent across the system
        :param buffer: when checking if the point is on the line segment, how far from the line it can be (gps errors etc.)
        :param angle: radians
        :return: Coordinates of either the start or the end of the road segment, based on which direction the angle is going towards
        """
        road = self.get_road_for_point(car_x, car_y)
        if road is None:
            raise ValueError("No road found near the provided point.")

        def point_on_line(segment_start: tuple[float, float], segment_end: tuple[float, float]) -> bool:
            """
            Returns True if the car position is within `buffer`
            """
            line = LineString([segment_start, segment_end])
            point = Point(car_x, car_y)
            return point.distance(line) < buffer

        before: tuple[float, float] | None = None
        after: tuple[float, float] | None = None

        for i in range(len(road.geometry.coords) - 1):
            maybe_before = road.geometry.coords[i]
            maybe_after = road.geometry.coords[i + 1]

            if not point_on_line(maybe_before, maybe_after):
                continue

            before = maybe_before
            after = maybe_after
            break

        if before is None or after is None:
            raise ValueError("Point is not on any road segment within the buffer.")

        road_angle = math.atan2(after[1] - before[1], after[0] - before[0])
        angle_diff = (angle - road_angle + math.pi) % (2 * math.pi) - math.pi
        # if rotated closer to the road direction, return the end, else the start
        if abs(angle_diff) < math.pi / 2:
            return road[-1]
        else:
            return road[0]


    # Aliases to not get confused with array operations
    def append(self, road: Road):
        self.add_road(road)

    def extend(self, roads: list[Road]):
        self.add_roads(roads)

    def __len__(self):
        return len(self.roads)

    def __getitem__(self, index: int) -> Road:
        return self.roads[index]

    def __iter__(self):
        return iter(self.roads)

    def __contains__(self, road: Road) -> bool:
        return road in self.roads
