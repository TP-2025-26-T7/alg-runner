from app.models import Car
from math import sqrt

def sq_distance_from_junction(car: Car) -> float:
    """
    Calculate squared distance from car to its next junction.
    Squared distance is used to avoid unnecessary square root calculations as we use the distances relatively for sorting.
    """
    return (car.x - car.next_junction_x) ** 2 + (car.y - car.next_junction_y) ** 2


def distance_from_junction(car: Car) -> float:
    """
    Calculate Euclidean distance from car to its next junction.
    """
    return sqrt(sq_distance_from_junction(car))


def binary_search(min_value: float, max_value: float, func) -> float:
    """
    Perform binary search to find the maximum value in the range [min_value, max_value] for which func(value) is True.
    :param min_value: minimum value of the search range
    :param max_value: maximum value of the search range
    :param func: function that takes a float and returns a boolean
    :return: maximum value for which func(value) is True
    """
    left = min_value
    right = max_value

    while right - left > 1e-5:
        mid = (left + right) / 2
        if func(mid):
            left = mid
        else:
            right = mid

    return left


def _required_distance_to_speed(curr_speed: float, target_speed: float, acceleration: float = 0,
                               deceleration: float = 0) -> float:
    """
    Calculate the required distance to reach target speed from current speed with given acceleration/deceleration.
    :param curr_speed: distance unit / time unit
    :param target_speed: distance unit / time unit
    :param acceleration: distance unit / time unit^2
    :param deceleration: distance unit / time unit^2
    :return: required distance in distance units
    """
    if target_speed == curr_speed:
        return 0

    should_accelerate = target_speed > curr_speed

    if should_accelerate and acceleration <= 0:
        return float('inf')

    if not should_accelerate and deceleration <= 0:
        if acceleration < 0: # if someone passed negative acceleration as deceleration
            deceleration = -acceleration
        else:
            return float('inf')

    a = acceleration if should_accelerate else deceleration

    required_distance = abs(target_speed ** 2 - curr_speed ** 2) / (2 * a)

    return required_distance


def _should_accelerate_to(curr_speed: float, duration: float, distance: float) -> float:
    """
    Calculate the target speed to reach within a given duration and distance. Assumes constant acceleration.
    :return: Speed to try to reach, in order to travel the given distance in the given duration.
    """
    if duration <= 0:
        raise RuntimeError('Duration must be positive.')

    target_speed = (2 * distance / duration) - curr_speed

    should_accelerate = target_speed > curr_speed
    if should_accelerate:
        return target_speed

    else:
        return max(0.0, target_speed)


def max_target_speed(duration_s: float, max_distance: float, speed_limit: float, curr_speed: float, acceleration: float, breaking: float = 0, break_epsilon: float = 0.25) -> float:
    """
    Calculate the maximum target speed a car can reach within a given duration and distance, considering acceleration and breaking limits.
    :param duration_s: time duration in seconds
    :param max_distance: maximum distance the car can travel before hitting an obstacle
    :param acceleration: acceleration rate in units per second squared
    :param breaking: breaking rate in units per second squared. 0 by default, in case we break just with negative acceleration.
    :param speed_limit: maximum speed limit in units per second
    :param curr_speed: current speed of the car in units per second
    :param break_epsilon: leeway to account for the error in breaking distance calculation. Value between 0 and 1. Fraction of
    :return: maximum target speed in units per second
    """

    # If negative time passed, something is wrong, slow down for safety.
    if duration_s <= 0:
        return 0

    if curr_speed < speed_limit and speed_limit * duration_s < max_distance:
        return speed_limit

    # distance at which we are sure to be able to stop if needed (because the car won't go above speed_limit)
    break_distance = _required_distance_to_speed(speed_limit, 0, deceleration=breaking) * (1 + break_epsilon)
    if break_distance >= max_distance:
        return 0.0

    target_speed = _should_accelerate_to(curr_speed, duration_s, max_distance - break_distance)

    # clamp the target speed to (0, speed_limit)
    return max(0.0, min(target_speed, speed_limit))