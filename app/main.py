# Built-in packages import (e.g. os, math,...)
from contextlib import asynccontextmanager

# Imported packages imports
from fastapi import FastAPI
# Project module imports
from app.routes import alg_router
from app.models import RoadNetwork

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize state
    app.state.junctions = []
    app.state.roads = RoadNetwork()
    app.state.cars_cache = []
    app.state.hyperparams = {
        "slowdown_zone": 3.0,
        "slowdown_rate": 0.3,
    }
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(alg_router)

@app.get("/")
async def root():
    return {"status": "ok"}
