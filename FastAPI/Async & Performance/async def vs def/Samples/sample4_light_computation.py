from fastapi import FastAPI
import asyncio

app=FastAPI()

@app.get("/add-def")
def add_numbers_sync(a:int,b:int):
    return {"result":a+b}

@app.get("/add-async")
async def add_numbers_async(a:int,b:int):
    return {"result":a+b}
