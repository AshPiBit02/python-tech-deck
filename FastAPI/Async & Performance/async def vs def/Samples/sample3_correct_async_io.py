from fastapi import FastAPI
import asyncio
import httpx

app=FastAPI()

@app.get("/weather/{city}")
async def get_weather(city:str):
    async with httpx.AsyncClient() as client:
        response=await client.get(f"https://wttr.in/{city}?format=j1")
        return response.json()
    
