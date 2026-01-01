from app.models import Car, RoadNetwork, Junction, get_road_end_coordinates
from math import sqrt

def sq_distance_from_junction(car: Car) -> float:
    """
    Calculate squared distance from car to its next junction.
    Squared distance is used to avoid unnecessary square root calculations as we use the distances relatively for sorting.
    """
    if car.next_junction_x is None or car.next_junction_y is None:
        return float("inf")

    return (car.x - car.next_junction_x) ** 2 + (car.y - car.next_junction_y) ** 2


def distance_from_junction(car: Car) -> float:
    """
    Calculate Euclidean distance from car to its next junction.
    """
    distance_sq = sq_distance_from_junction(car)
    return sqrt(distance_sq) if distance_sq != float("inf") else float("inf")


def set_next_junction(car: Car, junctions: list[Junction]):
    target_point = get_road_end_coordinates(car.x, car.y, car.angle, road=car.road)
    closest_junction = min(
        junctions,
        key=lambda junction: (junction.x - target_point[0]) ** 2 + (junction.y - target_point[1]) ** 2,
        default=None
    )
    if closest_junction is None:
        return

    car.next_junction = closest_junction
    car.next_junction_id = closest_junction.junction_id


def set_current_road(car: Car, road_network: RoadNetwork) -> None:
    road = road_network.get_road_for_point(car.x, car.y)
    if road:
        car.road = road
        car.road_id = road.road_id


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


def _should_accelerate_to(curr_speed: float, duration: float, distance: float, speed_limit: float, acceleration: float, deceleration: float) -> float:
    """
    Calculate the target speed to reach within a given duration and distance. Assumes constant acceleration.
    :return: Speed to try to reach, in order to travel the given distance in the given duration.
    """
    def bin_search(low_speed: float=0, high_speed: float=speed_limit, itr = 0, max_itr = 5, epsilon: float = 0.1) -> float:
        mid = (low_speed + high_speed) / 2

        if itr >= max_itr or low_speed*(1+epsilon) > high_speed:
            return mid

        distance_accelerating = _required_distance_to_speed(curr_speed, mid, acceleration=acceleration, deceleration=deceleration)
        time_accelerating = distance_accelerating / ((curr_speed + mid) / 2)

        if time_accelerating > duration or distance_accelerating > distance:
            return bin_search(low_speed, mid, itr + 1, max_itr, epsilon)

        time_cruising = duration - time_accelerating
        distance_cruising = mid * time_cruising

        traveled_distance = distance_accelerating + distance_cruising

        # if close enough the final distance, return mid
        if traveled_distance < distance:
            if distance * (1 - epsilon) < traveled_distance:
                return mid

            return bin_search(mid, high_speed, itr + 1, max_itr, epsilon)

        return bin_search(low_speed, mid, itr + 1, max_itr, epsilon)

    if duration <= 0:
        raise RuntimeError('Duration must be positive.')


    target_speed = bin_search()
    return target_speed


def max_target_speed(duration_s: float, max_distance: float, speed_limit: float, curr_speed: float, acceleration: float, breaking: float = 0, break_epsilon: float = 0.25) -> float:
    """
    Calculate the maximum target speed a car can reach within a given duration and distance, considering acceleration and breaking limits.

    !!! Note: Edge cases with car going way above speed limit are not handled. !!!
    :param duration_s: time duration in seconds
    :param max_distance: maximum distance the car can travel before hitting an obstacle
    :param acceleration: acceleration rate in units per second squared
    :param breaking: breaking rate in units per second squared. 0 by default, in case we break just with negative acceleration.
    :param speed_limit: maximum speed limit in units per second
    :param curr_speed: current speed of the car in units per second
    :param break_epsilon: leeway to account for the error in breaking distance calculation. Value between 0 and 1.
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

    target_speed = _should_accelerate_to(curr_speed, duration_s, max_distance - break_distance, speed_limit, acceleration, breaking)

    # clamp the target speed to (0, speed_limit)
    return max(0.0, min(target_speed, speed_limit))

