# Built-in packages import (e.g. os, math,...)

# Imported packages imports
from fastapi import FastAPI
# Project module imports
from app.routes import alg_router

app = FastAPI()
app.include_router(alg_router)

@app.get("/")
async def root():
    return {"status": "ok"}
