"""
PROBLEM: A load balancer/orchestrator needs to know if the app is truly read to 
serve traffic -- not just that the process started, but that its critical depencies
actually initialized successfully.

SOLUTION: Track readiness as state set during lifespan startup, and expose it through
a dedicated /health/ready route the orchestrator call poll.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request,HTTPException

def check_dependency_is_reachable()->bool:
    print("Checking critical dependency is reachable...")
    time.sleep(3)
    print("Dependency check passed.")
    return True

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.ready=False
    app.state.ready=check_dependency_is_reachable()
    yield
    app.state.ready=False

app=FastAPI(lifespan=lifespan)

@app.get("/health/ready")
def readiness_check(request:Request):
    if not request.app.state.ready:
        raise HTTPException(status_code=503,detail="Not ready")
    return {"status":"ready"}