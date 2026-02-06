from fastapi import APIRouter, HTTPException, Request

from app.models import Car, DispatchRequest, Junction, RoadNetwork, SetupRequest, CarCache, Algorithm
from app.algorithms import get_algorithm
from app.utils.distance import set_current_road, set_next_junction
router = APIRouter(tags=["algorithms"])

@router.post("/setup")
async def setup(request: Request, payload: SetupRequest):
    """
    Set or update junctions in the global application state.
    :param request: HTTP request object
    :param payload: Array of junctions to set or update
    :return:
    """
    junctions_data = payload.junctions
    roads_data = payload.roads
    overwrite = payload.overwrite

    # Ensure state attribute exists
    if not hasattr(request.app.state, "junctions") or overwrite:
        request.app.state.junctions = []

    if not hasattr(request.app.state, "roads") or overwrite:
        request.app.state.roads = RoadNetwork()

    if not hasattr(request.app.state, "cars_cache") or overwrite:
        request.app.state.cars_cache = []

    if overwrite:
        request.app.state.junctions = junctions_data.copy()
        request.app.state.roads = RoadNetwork(roads_data)
        for key, value in payload.car_targets.items():
            request.app.state.cars_cache.clear()
            request.app.state.cars_cache.append(CarCache(car_id=key, target_road_id=value))
    else:
        request.app.state.junctions.extend(junctions_data)
        request.app.state.roads.extend(roads_data)
        for key, value in payload.car_targets.items():
            request.app.state.cars_cache.append(CarCache(car_id=key, target_road_id=value))

    request.app.state.hyperparams = {
        "slowdown_zone": payload.slowdown_zone,
        "slowdown_rate": payload.slowdown_rate,
    }

    return {"status": "success"}


@router.post("/dispatch", response_model=list[Car])
def dispatch_cars(request: Request, payload: DispatchRequest) -> list[Car]:
    alg_name = payload.algorithm_name
    algorithm: Algorithm = get_algorithm(alg_name)

    junctions = getattr(request.app.state, "junctions", None)
    if not junctions:
        # Fallback to payload-provided junctions so we can work without a separate /setup call
        request.app.state.junctions = payload.junctions or []
        junctions = request.app.state.junctions

    cars: list[Car] = payload.cars
    # Populate cars with cached data
    cached_cars = request.app.state.cars_cache
    for car in cars:
        # Find cached data for the car
        cached_car = next((c for c in cached_cars if c.car_id == car.car_id), None)
        if not cached_car:
            continue
        car.seconds_in_traffic = cached_car.seconds_in_traffic
        if not car.target_road_id and cached_car.target_road_id:
            car.target_road_id = cached_car.target_road_id

        # recalculate road and junction in case the car crossed the junction
        # !!! note: possible performance issue - consider optimizing if needed !!!
        if len(request.app.state.roads) > 0:
            set_current_road(car, request.app.state.roads)

        if car.road:
            set_next_junction(car, junctions)

    next_dispatch_in_seconds = payload.next_request_in_seconds
    try:
        return algorithm(payload.cars, junctions, duration_s=next_dispatch_in_seconds, **request.app.state.hyperparams)
    except Exception as exc:  # Defensive: surface algorithm errors nicely
        raise HTTPException(status_code=400, detail=f"Dispatch failed: {exc}")
