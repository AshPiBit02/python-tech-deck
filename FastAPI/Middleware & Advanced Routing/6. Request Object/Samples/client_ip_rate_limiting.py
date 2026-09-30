"""
PROBLEM: We want to rate-limit by client IP, but request.client.host is often WRONG
in production - behind a load balancer/reverse proxy(nginx, Cloudflare, ALB), that 
field holds the proxy's IP, not the real client's. Every looks like it's from the
same machine.

SOLUTION: Read the X-Forward-For header(set by the proxy) when present, falling back
to request.client.host for local/dev use. Use that resolved IP as the key for simple 
rate limiter.
"""

import time
from collections import defaultdict
from fastapi import FastAPI,HTTPException,Request,status

app=FastAPI(title="Client IP Rate Limiting Demo")

RATE_LIMIT=3
WINDOW_SECONDS=10

hits:dict[str,list[float]]=defaultdict(list)

def get_real_client_ip(request:Request)->str:
    forwarded_for=request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@app.get("/ping")
def ping(request:Request):
    ip=get_real_client_ip(request)
    now=time.time()
    recent_hits=[t for t in hits[ip] if now-t<WINDOW_SECONDS]
    if len(recent_hits)>=RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {ip}",
        )
    recent_hits.append(now)
    hits[ip]=recent_hits
    return {"ip":ip,"requests_in_window":len(recent_hits)}