from collections import defaultdict
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app=FastAPI()

request_counts:dict[str,list[float]]=defaultdict(list)
RATE_LIMIT=5
WINDOW_SECONDS=60

@app.middleware("http")
async def rate_limit(request,call_next):
    client_ip=request.client.host
    now=time.time()

    request_counts[client_ip]=[t for t in request_counts[client_ip] if now - t < WINDOW_SECONDS]

    if len(request_counts[client_ip])>=RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail":"Too many requests, try again later"},
        )
    request_counts[client_ip].append(now)
    return await call_next(request)