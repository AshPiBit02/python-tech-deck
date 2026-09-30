"""
PROBLEM: Middleware often computes something useful (a request ID for
tracing, a decoded-but-not-yet-validated user, request start time) and
your endpoint funcitons need that value too - but middleware and path
operation functions don't share arguments directly.

SOLUTION: Attach line value to 'request.state' inside the middleware.
'request.state' is a plain namespace that's scoped to a single request
and readable from anywhere downstream, including inside the endpoint
by declaring a 'request:Request' parameter.
"""

import time
import uuid

from fastapi import FastAPI,Request

app=FastAPI(title="request.state Demo")

@app.middleware("http")
async def add_request_context(request: Request,call_next):
    request.state.request_id=str(uuid.uuid4())
    request.state.start_time=time.perf_counter()

    print(f"[{request.state.request_id}] START {request.method} {request.url.path}")
    response=await call_next(request)
    duration_ms=(time.perf_counter() - request.state.start_time)*1000
    print(f"[{request.state.request_id}] END {duration_ms:.2f}ms")

    response.headers["X-Request-ID"]=request.state.request_id
    return response
