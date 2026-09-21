import asyncio
import time
from datetime import datetime,timezone

import httpx

from fastapi import FastAPI,BackgroundTasks,Query

app=FastAPI(title="Async Weather Aggregator")

WEATHER_API_BASE="https://wttr.in"

REQUEST_LOGS:list[dict]=[]

def log_request(city:str,duration_seconds:float,success:bool):
    REQUEST_LOGS.append(
        {
            "city":city,
            "duration_seconds":duration_seconds,
            "success":success,
            "timestamp":datetime.now(timezone.utc).isoformat(),
        }
    )

async def fetch_weather(client:httpx.AsyncClient,city:str)->dict:
    start=time.perf_counter()
    try:
        response=await client.get(f"{WEATHER_API_BASE}/{city}?format=j1",timeout=10)
        response.raise_for_status()
        data=response.json()
        current=data["current_condition"][0]
        elapsed=time.perf_counter()-start
        return {
            "city":city,
            "success":True,
            "temperature_C":current["temp_C"],
            "description":current["weatherDesc"][0]["value"],
            "duration_seconds":round(elapsed,3),
        }
    except Exception as e:
        elapsed=time.perf_counter()-start
        return {
            "city":city,
            "success":False,
            "error":str(e),
            "duration_seconds":round(elapsed,3),
        }

@app.get("/weather/sequential")
async def get_weather_sequential(backgound_tasks:BackgroundTasks,cities:list[str]=Query(...,description="e.g. ?cities=London&cities=Paris&cities=Tokyo"),):
    start=time.perf_counter()
    results=[]
    async with httpx.AsyncClient() as client:
        for city in cities:
            result=await fetch_weather(client,city)
            results.append(result)
            backgound_tasks.add_task(log_request,city,result["duration_seconds"],result["success"])

    total_time=time.perf_counter()-start
    return {
        "mode":"sequential",
        "total_time_seconds":round(total_time,3),
        "results":results
        }



