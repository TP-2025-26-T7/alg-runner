from typing import Callable

from fastapi import APIRouter, Request

from app.models import Car, DispatchRequest, Junction, RoadNetwork, SetupRequest
from app.algorithms import get_algorithm

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

    if overwrite:
        request.app.state.junctions = junctions_data.copy()
        request.app.state.roads = RoadNetwork(roads_data)
    else:
        request.app.state.junctions.extend(junctions_data)
        request.app.state.roads.extend(roads_data)

    return {"count": len(request.app.state.junctions)}


@router.post("/dispatch", response_model=list[Car])
def dispatch_cars(request: Request, payload: DispatchRequest) -> list[Car]:
    alg_name = payload.algorithm_name
    algorithm: Callable[[list[Car], list[Junction]], list[Car]] = get_algorithm(alg_name)

    junctions = request.app.state.junctions
    if not junctions:
        raise ValueError("No junctions provided for dispatching cars.")

    return algorithm(payload.cars, junctions)
