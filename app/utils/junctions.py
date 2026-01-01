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