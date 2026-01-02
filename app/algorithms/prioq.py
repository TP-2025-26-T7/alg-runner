from typing import Callable, Literal

from app.models import Car, Junction, Road
import app.utils.transformations as transform
from app.utils.distance import max_target_speed


def calculate_priority(car: Car, cars_in_line: int,
                       required_junction_segments: int,
                       combine_mode: Literal["sum", "mult"] = "sum",
                       **attribute_weight_funcs: Callable[[float, ...], float]) -> float:
    """
    Calculate priority for a car based on:

    - number of cars in line behind it (more cars waiting for this one increase its priority)
    - number of junction segments the car will occupy (more segments block more traffic, increasing its priority)
    - how long the car has been waiting
    - speed (slowing the car down is less desirable, but not an important factor)

    :param car: models/schema/Car
    :param cars_in_line: number of cars waiting behind this car for the same junction
    :param required_junction_segments: number of junction segments the car will occupy
    :param combine_mode: how to combine weights of individual attributes ("sum" | "mult" )
    :param attribute_weight_funcs: functions that calculate weights for each attribute ["cars_in_line", "required_junction_segments", "seconds_in_traffic", "speed"]
    :return priority value (higher value => higher priority)
    """
    weights = []
    cars_in_line_weight_func = attribute_weight_funcs.get("cars_in_line", lambda x: transform.linear(x))
    required_junction_segments_weight_func = attribute_weight_funcs.get("required_junction_segments", lambda x: transform.linear(x, 3))
    waiting_time_weight_func = attribute_weight_funcs.get("seconds_in_traffic", lambda x: transform.exponential(x, max_value=10))
    speed_weight_func = attribute_weight_funcs.get("speed", lambda x: transform.logarithmic(x))

    weights.append(cars_in_line_weight_func(cars_in_line))
    weights.append(required_junction_segments_weight_func(required_junction_segments))
    weights.append(waiting_time_weight_func(car.seconds_in_traffic))
    weights.append(speed_weight_func(car.speed))

    if combine_mode == "sum":
        return sum(weights)
    elif combine_mode == "mult":
        priority = 1.0
        for weight in weights:
            priority *= weight
        return priority
    else:
        raise ValueError("Invalid combine_mode. Use 'sum' or 'mult'.")


def dispatch(cars: list[Car],
             junctions: list[Junction],
             duration_s: float = 0.2,
             junction_buffer_zone: float = 1.5,
             slowdown_zone: float = 10,
             slowdown_rate: float = 1,
             **kwargs) -> list[Car]:
    """
    :param cars: Array of cars to dispatch
    :param junctions: Array of junctions in the road network
    :param duration_s: Frequency of dispatching cars in seconds.
    :param junction_buffer_zone: How many units before the junction the car tries to go into the junction.
    :param slowdown_zone: Distance from junctions where speed limit is lowered.
    :param slowdown_rate: Rate at which speed is reduced in the slowdown zone (0 < rate < 1; e.g. 0.3 means 30% of original speed).
    :return: Cars with modified speeds according to priority-based dispatching.
    """
    # Group cars by upcoming junction
    junction_cars: dict[str, list[Car]] = {}
    cars_leaving_junction: dict[Road, list[Car]] = {} # cars leaving per road
    for car in cars:
        if not car.next_junction_id:
            cars_leaving_junction.setdefault(car.road, []).append(car)
        else:
            junction_cars.setdefault(car.next_junction_id, []).append(car)

    for road, cars in cars_leaving_junction.items():
        # !!! Note: Just sending them at speed limit for now. Fix later if safety issues arise. !!!
        for car in cars:
            car.speed = road.recommended_speed

    for junction in junctions:
        # No cars on this junction, skip it
        if junction.junction_id not in junction_cars:
            continue

        cars_at_junction = junction_cars[junction.junction_id]
        road_cars: dict[str, list[Car]] = {}
        is_car_inside = False # If cars are inside the junction, don't let others in until they leave

        for car in cars_at_junction:
            if not car.road_id:
                continue
            # if car already is inside the junction, the speed has been set already in previous iteration
            if junction.is_point_inside(car.x, car.y):
                is_car_inside = True
                continue
            road_cars.setdefault(car.road_id, list[Car]()).append(car)

        # For each road, sort cars by distance to junction
        for road_id, cars_on_road in road_cars.items():
            cars_on_road.sort(key=lambda c: c.distance_from_next_junction())

        prev_car_speed_per_road: dict[str, float] = {} # road_id -> speed of the previous car on this road
        prev_car_distance_per_road: dict[str, float] = {road_id: 0.0 for road_id in road_cars}

        # Send cars into the junction
        if not is_car_inside:
            taken_up_segments: set[int] = set() # segments occupied by cars in the junction
            # get cars waiting to go to the junction (within junction_buffer_zone, first in line)
            waiting_cars = []
            for road_id, cars_on_road in road_cars.items():
                try:
                    if cars_on_road[0].distance_from_next_junction(simple_mode=True) <= junction_buffer_zone:
                        waiting_cars.append(cars_on_road[0])
                except IndexError:
                    continue

            while len(waiting_cars):
                waiting_cars.sort(key=lambda c: calculate_priority(
                    c,
                    cars_in_line=len(road_cars.get(c.road_id, [])) - 1,
                    required_junction_segments=junction.crossing_segments_count(c.road_id, c.target_road_id),
                    **kwargs
                ), reverse=True)

                selected_car = waiting_cars.pop(0)
                prev_car_distance_per_road.setdefault(selected_car.road_id, selected_car.distance_from_next_junction())

                required_segments = junction.crossing_segments_count(selected_car.road_id, selected_car.target_road_id)
                # if none of the segments are in taken_up_segments set, let the car go
                if not any(seg in taken_up_segments for seg in range(required_segments)):
                    # let the car go at recommended speed
                    selected_road = selected_car.road
                    if selected_road and selected_road.recommended_speed:
                        selected_car.speed = selected_road.recommended_speed
                        # if recommended speed not defined, keep current speed

                    # mark segments as taken
                    for seg in range(required_segments):
                        taken_up_segments.add(seg)
                else:
                    selected_car.speed = 0

                prev_car_speed_per_road.setdefault(selected_car.road_id, selected_car.speed)

        # for each road, move the car as forward as possible.
        for road_id, cars_on_road in road_cars.items():
            while len(cars_on_road):
                car = cars_on_road.pop(0)
                prev_car_speed: float = prev_car_speed_per_road.setdefault(road_id, car.road.recommended_speed)
                prev_distance: float = prev_car_distance_per_road.setdefault(road_id, 0.0)

                if prev_car_speed > car.speed:
                    car.speed = prev_car_speed
                    continue

                distance_from_next = car.distance_from_next_junction()
                target_speed = max_target_speed(
                    duration_s = duration_s,
                    max_distance= distance_from_next - prev_distance,
                    curr_speed=car.speed,
                    speed_limit=car.road.recommended_speed if distance_from_next > slowdown_zone else car.road.recommended_speed * slowdown_rate,
                    acceleration=car.acceleration,
                    breaking=car.breaking)

                car.speed = target_speed
    return cars