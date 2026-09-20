import asyncio
from fastapi import FastAPI

app=FastAPI()

def heavy_calculation(n:int):
    return sum(i*i for i in range(n))

@app.get("/calc")
async def calc_route(n:int=10_0000_000):
    loop=asyncio.get_event_loop()
    result=await loop.run_in_executor(None,heavy_calculation,n)
    return {"result":result}