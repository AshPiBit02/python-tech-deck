"""
PROBLEM: Creating a new httpx.AsyncClient() inside every route means opening and closing
a connection pool per request -- wasteful under real traffic.

SOLUTION: Create the client ONCE via lifespan, reuse it for every request.
"""

from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI,Request

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.http_client=httpx.AsyncClient()
    print("Startup: shared HTTP client created.")
    yield
    await app.state.http_client.aclose()
    print("Shutdown: shared HTTP client closed.")

app=FastAPI(lifespan=lifespan)

@app.get("/quote")
async def get_quote(request:Request):
    response=await request.app.state.http_client.get("https://api.quotable.io/random")
    data=await response.json()
    return {"quote":data["content"],"author":data["author"]}