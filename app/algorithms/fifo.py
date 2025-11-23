from app.models.schema import Car, Junction
from .utils import sq_distance_from_junction

def dispatch(cars: list[Car], junctions: list[Junction], speed_decay: float = 3.0) -> None:
    """
    Original algorithm from stocars repository.
    Removed unnecessary parts and compacted the code.
    """
    for junction in junctions:
        queue = [car for car in cars if car.next_junction_id == junction.junction_id]
        queue.sort(key=lambda car: sq_distance_from_junction(car))
        if not queue:
            continue
        base_speed = queue[0].speed
        for i, car in enumerate(queue[1:], start=1):
            car.speed = max(1.0, base_speed - i * speed_decay)


