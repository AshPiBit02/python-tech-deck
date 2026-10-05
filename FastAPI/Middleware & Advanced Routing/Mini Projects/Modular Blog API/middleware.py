"""
A single middleware that:
  1. Blocks any request missing a User-Agent header (400).
  2. Times the request and logs "METHOD /path -> status (Xms)".
  3. Stamps every response with a unique X-Request-ID header.
 
Implemented as a Starlette BaseHTTPMiddleware subclass (rather than
the @app.middleware("http") function decorator) so it's a reusable,
testable class with clear single-responsibility ordering.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse,Response

logger=logging.getLogger("blog_api")
logging.basicConfig(level=logging.info,format="%(message)s")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request:Request,call_next)->Response:
        if "user-agent" not in request.headers:
            return JSONResponse(
                status_code=400,
                content={"detail":"User-Agent header is required"},
            )

        request_id=str(uuid.uuid4())
        start=time.perf_counter()

        response=await call_next(request)

        duration_ms=(time.perf_counter()-start)*1000
        response.headers["X-Request-ID"]=request_id

        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response