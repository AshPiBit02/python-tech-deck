import time
import asyncio
from fastapi import FastAPI

app=FastAPI(title="Concurrency Demonstration API")

DELAY_SECONDS=2

@app.get("/bad-async")
async def bad_async_route():
    time.sleep(DELAY_SECONDS)
    return {"route":"bad-sync","status":"done"}

@app.get("/good-async")
async def good_async_route():
    await asyncio.sleep(DELAY_SECONDS)
    return {"route":"good-async","status":"done"}

@app.get("/sync-blocking")
def sync_blocking_route():
    time.sleep(DELAY_SECONDS)
    return {"route":"sync-blocking","status":"done"}

@app.get("/bad-cpu")
async def bad_cpu_route(n:int=20_000_000):
    total=0
    for i in range(n):
        total+=i
    return {"route":"bad-cpu","total":total}

@app.get("/ok-cpu-sync")
def ok_cpu_route(n:int=20_000_000):
    total=0
    for i in range(n):
        total+=i
    return {"route":"ok-cpu-sync","total":total}

@app.get("/instant")
def instant_route():
    return {"route":"instant","status":"always fast like flash"}