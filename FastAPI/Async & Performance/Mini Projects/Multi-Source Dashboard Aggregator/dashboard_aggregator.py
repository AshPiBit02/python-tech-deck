import asyncio
import time
from datetime import datetime,timezone

import httpx
from fastapi import FastAPI,BackgroundTasks,Query

app=FastAPI(title="Multi-Source Dashboard Aggregator")

REQUEST_LOGS:list[dict]=[]

def log_dashboard_request(sources_succeeded:list[str],sources_failed:list[str],total_time:float):
    REQUEST_LOGS.append({
        "succeeded":sources_succeeded,
        "failed":sources_failed,
        "total_time_seconds":round(total_time,3),
        "timestamp":datetime.now(timezone.utc).isoformat(),
    })

async def fetch_quote(client:httpx.AsyncClient)->dict:
    response=await client.get("https://api.quotable.io/random",timeout=10)
    response.raise_for_status()
    data=response.json()
    return {
        "source":"quote",
        "content":data["content"],
        "author":data["author"],
    }

async def fetch_fun_fact(client:httpx.AsyncClient)->dict:
    response=await client.get("https://catfact.ninja/fact",timeout=10)
    response.raise_for_status()
    data=response.json()
    return {
        "source":"fun_fact",
        "fact":data["fact"],
    }

async def fetch_city_weather(client:httpx.AsyncClient,city:str)->dict:
    response=await client.get("https://wttr.in/{city}?format=j1",timeout=10)
    response.raise_for_status()
    data=response.json()
    current=data["current_condition"][0]
    return {
        "source":"weather",
        "city":city,
        "temperature_C":current["temp_C"],
        "description":current["weatherDesc"][0]["value"],
    }

@app.get("/dashboard")
async def get_dashboard(backgound_tasks:BackgroundTasks,city:str=Query("Berlin")):
    start=time.perf_counter()
    async with httpx.AsyncClient() as client:
        results= await asyncio.gather(
            fetch_quote(client),
            fetch_fun_fact(client),
            fetch_city_weather(client,city),
            return_exceptions=True,
        )

    dashboard=[]
    successed=[]
    failed=[]

    source_names=["quote","fun_fact","weather"]
    for name,result in zip(source_names,results):
        if isinstance(result,Exception):
            dashboard[name]={"error":str(result)}
            failed.append(name)
        else:
            dashboard[name]=result
            successed.append(name)

    total_time=time.perf_counter()-start
    backgound_tasks.add_task(log_dashboard_request,successed,failed,total_time)

    return {
        "total_time_seconds":round(total_time,3),
        "sources_succeeded":successed,
        "sources_failed":failed,
        "dashboard":dashboard,
    }