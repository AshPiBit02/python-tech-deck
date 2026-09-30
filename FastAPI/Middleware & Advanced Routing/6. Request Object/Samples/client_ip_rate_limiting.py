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

hints:dict[str,list[float]]=defaultdict(list)
