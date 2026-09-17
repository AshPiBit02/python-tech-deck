import requests # synchronous library - no native async support
from fastapi import FastAPI

app=FastAPI()

@app.get("/bad-weather")
async def bad_weather(city:str):
    response=requests.get(f"https://wttr.in/{city}?format=j1")
    return response.json()

@app.get("/safe-weather-sync")
def safe_weather_sync(city:str):
    response=requests.get(f"https://wttr.in/{city}?format=j1")
    return response.json()
