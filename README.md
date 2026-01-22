# Setup
This services works as a FastAPI server.
It is a python library, so make sure to have python 3.10+ installed (either system-wide or in a virtual environment).

Before starting the server, install the dependencies:
```shell
pip install -r requirements.txt
```

Also make sure to have the environmental variables set up.
Follow the `.env.example` file to create your own `.env` file.

To start the server, run:
```shell
uvicorn api.main:app --host YOUR_HOST --port YOUR_PORT
```

# Endpoints
## /setup
- type: POST
- body:
    ```
    {
        junctions: {
            junction_id: string
            connected_roads_count: int
            connected_roads_ids: string[]
            x: float
            y: float
            junction_size: float // radius of the junction
            polygon: { x: float, y: float }[] // optional, square around x,y with side junction_size if not provided
        }[]
        
        roads: {
            id: string
            polyline: { x: float, y: float }[]
            recommended_speed: float
            
            junction_start_id: string
            junction_end_id: string
        }[]
        
        car_targets: { [car_id: string]: string } // map<car_id, target_road_id>, optional
        
        overwrite: boolean // whether to overwrite existing setup
        
        slowdown_zone: float // optional, buffer before junction where cars should start slowing down
        slowdown_rate: float // optional, rate at which cars should slow down in slowdown zone
    
    }
    ```
## /dispatch
- type: POST
- body:
```
{
    algoritm_name: string // name of the algorithm to use for dispatching cars
    
    cars: {
        car_id: string
        x: float
        y: float
        speed: float
        wheel_rotation: float // in radians
        rotation: float // rotation in respect to the map axis, in radians
        acceleration: float
        breaking: float // breaking force, deceleration
        target_road_id: string
    }
    
    next_request_in_seconds: float // optional, time until next dispatch request
}
```
- response: 
```
{
    cars: {
        car_id: string
        speed: float
        wheel_rotation: float
    }
}
```
# Algorithms
## FIFO
legacy algorithm by previous team, translated from C++ to python
