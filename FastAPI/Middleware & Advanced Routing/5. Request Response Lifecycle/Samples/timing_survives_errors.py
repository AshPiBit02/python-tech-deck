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
from random import random
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
def success_route():
    return {"message":"all good"}

@app.get("/handled-error")
def handled_error_route():
    raise HTTPException(status_code=404,detail="Timing not found")

@app.get("/crash")
def crash_route():
    return 1/0 # deliberate unhandled bug