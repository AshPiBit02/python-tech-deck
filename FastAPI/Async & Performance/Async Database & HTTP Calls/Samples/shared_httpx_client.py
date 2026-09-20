from fastapi import FastAPI
import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.http_client=httpx.AsyncClient()
    print("HTTP client created")

    yield

    await app.state.http_client.aclose()
    print("HTTP client closed")

app=FastAPI(lifespan=lifespan)

@app.get("/proxy-data")
async def proxy_data():
    response = await app.state.http_client.get("https://jsonplaceholder.typicode.com/posts/1")
    return response.json()
