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
