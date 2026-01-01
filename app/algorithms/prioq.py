from typing import Callable, Literal

from app.models import Car, Junction
import app.utils.transformations as transform


def calculate_priority(car: Car, cars_in_line: int, required_junction_segments, combine_mode: Literal["sum", "mult"] = "sum" ,**attribute_weight_funcs: Callable[[float, ...], float]) -> float:
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


def dispatch(cars: list[Car], junctions: list[Junction]) -> list[Car]:
    # Group cars by upcoming junction
    junction_to_cars: dict[str, list[Car]] = {}
    for car in cars:
        if not car.next_junction_id:
            continue
        junction_to_cars.setdefault(car.next_junction_id, []).append(car)

    for junction in junctions:
        car_queue = junction_to_cars.get(junction.junction_id, [])
        if not car_queue:
            continue

        # Sort by priority (higher first) based on waiting time, distance, and current speed
        scored = []
        for c in car_queue:
            required_segments = max(1, junction.crossing_segments_count(junction.connected_roads_ids[0], junction.connected_roads_ids[-1]) if junction.connected_roads_ids else 1)
            score = calculate_priority(
                c,
                cars_in_line=len(car_queue),
                required_junction_segments=required_segments,
                seconds_in_traffic=lambda x: transform.exponential(x, max_value=10),
                speed=lambda x: transform.logarithmic(x, base=5, multiplier=0.5),
            )
            scored.append((c, score))

        scored.sort(key=lambda item: item[1], reverse=True)

        # Assign speeds: highest priority keeps its speed, others slow down progressively
        for idx, (car, _) in enumerate(scored):
            decay = max(0.0, idx * 1.5)
            car.speed = max(1.0, car.speed - decay)

    return cars