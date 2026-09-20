from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI
import asyncio

app=FastAPI()

process_pool=ProcessPoolExecutor(max_workers=4)

def cpu_intensive_work(n:int):
    return sum(i*i for i in range(n))

@app.get("/parallel-calc")
async def parallel_calc_route(n:int=50_000_000):
    loop=asyncio.get_event_loop()
    result=await loop.run_in_executor(process_pool,cpu_intensive_work,n)
    return {"result":result}