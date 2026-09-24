import time
import logging
from fastapi import FastAPI

app=FastAPI()

logger=logging.getLogger("api")

@app.middleware("http")
async def log_requests(request,call_next):
    start=time.perf_counter()
    response= await call_next(request)
    duration=time.perf_counter()-start

    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ){duration:.3f}s")
    print(logger)
    return response