"""
PROBLEM: A route calling and external API creates a brand-new httpx.AsyncClient() on every
single request -- under real traffic, this means constantly opening and closing connection
pools instead of reusing one.

SOLUTION: Create the client ONCE, using the modern 'lifespan' context manager (the current,
non-deprecated replacement for @app.on_event), and reuse it across every request's lifetime.
"""

from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.http_client=httpx.AsyncClient()
    print("Shared HTTTP client created.")

    yield # The application runs here, handling requests, utill shutdown

    await app.state.http_client.aclose() # Runs ONCE, after the app stops accepting requests.
    print("Shared HTTP client closed.")

app=FastAPI(lifespan=lifespan)

@app.get("/quote")
async def get_quote():
    response=await app.state.http_client.get("https://api.quotable.io/random")
    response.raise_for_status()
    data=response.json()
    return {"quote":data["content"],"author":data["author"]}
