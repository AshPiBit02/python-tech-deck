"""
PROBLEM: Loading a large ML model is slow. Loading it inside the route function
requests that slow work on every single request.

SOLUTION: Load it ONCE in lifespan, before the app accepts any requests.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from pydantic import BaseModel

class FakeModel:
    """
    Stands in for a real ML model -- just doubles a number, but the loading step
    is deliberately slow to make the lifespan benefit visible."""
    def predict(self,value:float)->float:
        return value*2

def load_model_from_disk()->FakeModel:
    print("Loading model from disk...")
    time.sleep(3)
    print("Model loaded.")
    return FakeModel()

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.model=load_model_from_disk() # happens once
    yield
    print("Shutdown: releasing model.")


