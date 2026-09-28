"""
PROBLEM: An ops team wants request-duration + status logging for Every request -- success,
handled errors, and unexpected crashes alike -- without writing separate try/except handling
in the middleware for each case.

SOLUTION: Middleware doesn't need any special-casing. By the time control returns to the
'after' section of middleware, FastAPI has already converted any exception into a normal
response object.
"""

import time
import asyncio
import random
from fastapi import FastAPI,HTTPException

app=FastAPI(title="Timing Survives Errors Demo")

@app.middleware("http")
async def timing_middlware(request,call_next):
    start=time.perf_counter()
    response=await call_next(request)
    duration=time.perf_counter()-start
    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.4f}s)")
    return response

@app.get("/success")
async def success_route():
    await asyncio.sleep(random.uniform(0.84,2.34))
    return {"message":"all good"}

@app.get("/handled-error")
async def handled_error_route():
    await asyncio.sleep(random.uniform(0.84,2.34))
    raise HTTPException(status_code=404,detail="Timing not found")

@app.get("/crash")
async def crash_route():
    await asyncio.sleep(random.uniform(0.84,2.34))
    return 1/0 # deliberate unhandled bug