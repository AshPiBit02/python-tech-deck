# Custom Middleware in FastAPI

Middleware is code that runs around every request the application receives, regardless of which route handles it. This document covers everything needed to write middleware correctly — the two ways to register it, the request/response flow through `dispatch`, common use cases, and the specific pitfalls that trip people up (especially around reading the request body and streaming responses).

## Two Ways to Add Middleware

### 1. `BaseHTTPMiddleware` subclass (most common, most flexible)

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI

app = FastAPI()

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        return response

app.add_middleware(TimingMiddleware)
```

### 2. `@app.middleware("http")` decorator (simpler, function-based)

```python
@app.middleware("http")
async def timing_middleware(request, call_next):
    response = await call_next(request)
    return response
```

Both achieve the same result. The decorator form is more concise for a single, simple middleware; the class-based form is preferable when the middleware needs its own configuration (constructor arguments) or when several related middleware pieces are being organized together, since a class can be instantiated with parameters (`app.add_middleware(SomeMiddleware, some_option=True)`), while the decorator form cannot easily accept configuration.

## The `dispatch` Method and `call_next` — Core Mechanics

```python
class ExampleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # ---- Code here runs BEFORE the route handler ----
        print(f"Incoming: {request.method} {request.url.path}")

        response = await call_next(request)   # <-- hands off to the next layer
                                                #     (another middleware, or the route itself)

        # ---- Code here runs AFTER the route handler ----
        print(f"Outgoing status: {response.status_code}")

        return response
```

- **Everything before `await call_next(request)`** executes on the way *in* — before the request has reached its matching route, before FastAPI has even resolved dependencies for that route.
- **`call_next(request)`** is what actually triggers the rest of the pipeline — the next middleware in the chain, or, if this is the last middleware, the route handler itself. It's `await`-ed because request handling is itself async.
- **Everything after `call_next(...)` returns** executes on the way *out* — the response object already exists at this point; this is where headers can be added, timing can be recorded, or (carefully — see below) the response can be inspected.
- **The middleware must `return response`** at the end — omitting this, or returning something other than the response object, breaks the response pipeline for the client.

## Ordering With Multiple Middleware

When several middleware are registered, they wrap around each other and around the route handler, forming layers:

```python
app.add_middleware(MiddlewareA)
app.add_middleware(MiddlewareB)
```

With this registration order, the actual execution order is: **B's "before" code → A's "before" code → route handler → A's "after" code → B's "after" code**. Middleware registered later wraps *outside* middleware registered earlier — the last one added is the outermost layer, seeing the request first and the response last. This "last added, first to run on the way in" ordering is a common source of confusion and worth testing deliberately if the order of several middleware matters for correctness.

## Common Use Cases

### Request timing

```python
import time

@app.middleware("http")
async def add_timing_header(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Process-Time"] = str(round(duration, 4))
    return response
```

### Request ID for tracing

```python
import uuid

@app.middleware("http")
async def add_request_id(request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### Blocking requests based on a header (a simple gate before routes run at all)

```python
@app.middleware("http")
async def require_user_agent(request, call_next):
    if not request.headers.get("user-agent"):
        return JSONResponse(status_code=400, content={"detail": "User-Agent header required"})
    return await call_next(request)
```

This last example demonstrates that middleware can **short-circuit** the pipeline entirely — returning a response directly, without ever calling `call_next(request)`, meaning the route handler never runs at all for that request. This is how middleware can reject requests outright before any route-specific logic (or even dependency resolution) happens.

## The Built-In Example — `CORSMiddleware`

The `CORSMiddleware` used in the earlier HTTPS & CORS document is itself an example of this same pattern, just pre-built by FastAPI/Starlette rather than hand-written:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
)
```

Recognizing this as "just middleware, with configuration options" — rather than as some entirely separate FastAPI feature — helps connect it to everything else in this document; it inspects incoming request headers (the `Origin` header) and adds specific response headers accordingly, exactly like the hand-written examples above.

## Important Pitfall — Reading the Request Body Inside Middleware

A subtle and common mistake: reading `request.body()` (or similar) inside middleware, intending to log or inspect it, can **prevent the route handler from being able to read the body at all** — request bodies in ASGI applications are typically a one-time-readable stream, not a value that can be freely re-read. If middleware consumes the body stream first, the route handler's own body parsing (a Pydantic model, `await request.body()` inside the route) may receive nothing.

This is why body-inspecting middleware needs care — either avoiding reading the body in middleware entirely, or explicitly re-injecting a readable body back into the request object afterward (a more advanced technique, generally only necessary when body inspection in middleware is unavoidable, such as computing a request signature for verification).

## Important Pitfall — Modifying a Streaming Response

If a route returns a `StreamingResponse` (used for large files or server-sent events), the "after" section of middleware runs before the stream has actually finished sending — because `call_next()` returns as soon as the response object exists, not once all its content has been fully transmitted. Middleware attempting to inspect or modify a streaming response's *content* (as opposed to just its headers, which is safe) may not behave as expected, since the content hasn't fully passed through yet at that point in the middleware's execution.

## Key Points to Retain

- Middleware wraps every request/response cycle for the entire application; code before `call_next()` runs on the way in, code after runs on the way out.
- Multiple middleware layer around each other — the most recently registered middleware becomes the outermost layer.
- Middleware can short-circuit the pipeline by returning a response directly without calling `call_next()`, preventing the route (and any dependency resolution) from running at all.
- Reading the request body inside middleware can interfere with the route's own ability to read it, since request bodies are typically single-read streams in ASGI.
- Built-in tools like `CORSMiddleware` are ordinary middleware under the hood, following the exact same `dispatch`/`call_next` pattern as hand-written examples.