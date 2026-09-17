from fastapi import FastAPI
import time
import asyncio

app=FastAPI()

@app.get("/bad")
async def bad_async_route():
    time.sleep(5) # blocking call inside async def - freezes the ENTIRE even loop
    return {"status":"done(bad)"}

@app.get("/good")
async def good_async_route():
    await asyncio.sleep(5) # non-blocking - even loop free to serve others meanwhile
    return {"status":"dome(good)"}
