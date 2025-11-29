from .schema import Road
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree


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

    # Aliases to not get confused with array operations
    def append(self, road: Road):
        self.add_road(road)

    def extend(self, roads: list[Road]):
        self.add_roads(roads)