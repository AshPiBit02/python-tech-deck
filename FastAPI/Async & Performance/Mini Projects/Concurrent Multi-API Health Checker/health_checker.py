import asyncio
import time
from datetime import datetime,timezone
import httpx
from fastapi import FastAPI

app=FastAPI(title="Concurrent Multi-API Health Checker")

DEPENDENCIES={
    "weather_api":"https://wttr.in/Berlin&format=j1",
    "quote_api":"https://api.quotable.io/random",
    "fact_api":"https://catfact.ninja/fact",
    "definitely_down":"https://this-domain-does-not-exists-xyz123.com",
}

async def check_one(client:httpx.AsyncClient,name:str,url:str)->dict:
    start=time.perf_counter()
    try:
        response=await client.get(url,timeout=5)
        elapsed=time.perf_counter()-start
        return {
            "name":name,
            "status":"up" if response.status_code<400 else "degraded",
            "http_status":response.status_code,
            "reponse_time_seconds":round(elapsed,3),
        }
    except Exception as e:
        elapsed=time.perf_counter()-start
        return{
            "name":name,
            "status":"down",
            "error":str(e),
            "response_time_seconds":round(elapsed,3),
        }