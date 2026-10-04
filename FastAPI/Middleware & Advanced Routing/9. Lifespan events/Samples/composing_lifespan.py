"""
PROBLEM: An app has TWO separate things to set up at statup (an HTTP client and
a fake cache) -- cramming both info into one big lifespan functions make it harder
to read and reason about each piece independently.

SOLUTION: Write one small lifespan context manager PER concern, then compose them 
together with AsyncExitStack, which gurantees correct setup/teardown ordering for 
all of them.
"""

from contextlib import AsyncExitStack, asynccontextmanager
import httpx
from fastapi import FastAPI,Request

@asynccontextmanager
async def http_client_lifespan(app:FastAPI):
    app.state.http_client=httpx.AsyncClient()
    print("HTTP client ready.")
    yield
    await app.state.http_client.aclose()
    print("HTTP client closed.")

@asynccontextmanager
async def fake_cache_lifespan(app:FastAPI):
    app.state.chache={"warmed":True,"items":["a","b","c"]}
    print("Cache warmed.")
    yield
    app.state.cache=None
    print("Cache cleared.")

@asynccontextmanager
async def lifespan(app:FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(http_client_lifespan(app))
        await stack.enter_async_context(fake_cache_lifespan(app))
        yield