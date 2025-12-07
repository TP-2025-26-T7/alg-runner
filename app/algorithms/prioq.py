from app.models import Car
import math
from typing import Callable, Literal

def logistic(x: float, multiplier=1) -> float:
    """
    Logistic function to normalize values between 0 and 1.
    :param x: input value
    :param multiplier: Changes range from (0, 1) to (0, multiplier)
    :return: normalized value
    """
    return (1 / (1 + math.exp(-x))) * multiplier


def linear(x: float, multiplier=1, max_value: float = None) -> float:
    """
    Linear normalization function to normalize values between 0 and max_value.
    :param multiplier: Multiplies the output :)
    :param x: input value
    :param max_value: maximum value for normalization
    :return: normalized value
    """
    if max_value is None:
        return x * multiplier
    return min(x, max_value) * multiplier


def exponential(x: float, base: float = 2, multiplier=1, max_value: float = None) -> float:
    """
    Exponential normalization function to normalize values.
    :param x: input value
    :param base: exponential base
    :param multiplier: Multiplies the output :)
    :param max_value: maximum value for normalization
    :return: normalized value
    """
    value = (base ** x) * multiplier
    if max_value is None:
        return value
    return min(value, max_value)


def logarithmic(x: float, base: float = 10, multiplier=1) -> float:
    """
    Logarithmic normalization function to normalize values.
    :param x: input value
    :param base: logarithm base
    :param multiplier: Multiplies the output :)
    :return: normalized value
    """
    if x <= 0:
        return 0
    return math.log(x, base) * multiplier


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
    cars_in_line_weight_func = attribute_weight_funcs.get("cars_in_line", lambda x: linear(x))
    required_junction_segments_weight_func = attribute_weight_funcs.get("required_junction_segments", lambda x: linear(x, 3))
    waiting_time_weight_func = attribute_weight_funcs.get("seconds_in_traffic", lambda x: exponential(x, max_value=10))
    speed_weight_func = attribute_weight_funcs.get("speed", lambda x: logarithmic(x))

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

