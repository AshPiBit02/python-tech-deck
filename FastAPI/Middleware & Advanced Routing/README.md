# Middleware & Advanced Routing

As a FastAPI application grows beyond a handful of routes — which is already true of the auth system built earlier in this roadmap — two organizational problems start to appear: repeated cross-cutting logic that every route needs (logging, timing, custom headers, request-wide checks) and a single flat file that becomes unwieldy to navigate as more routes are added. This phase addresses both: **middleware** solves the first problem by letting logic run around every request without repeating it per route; **advanced routing** (primarily `APIRouter`) solves the second by letting routes be organized into separate modules while still behaving as one application.

## What Middleware Actually Is

Middleware is code that sits **between** the raw incoming request and the route handler that will eventually process it — and again between the route handler's response and what actually gets sent back to the client. Every single request passes through registered middleware, in order, before reaching its matching route; every response passes back through that same middleware, in reverse order, before leaving the server.

This is fundamentally different from a dependency (`Depends()`). A dependency is attached to specific routes and only runs for requests hitting those routes. Middleware runs for **every request to the entire application**, regardless of which route it's ultimately headed to — including requests that don't match any route at all (a 404), since middleware sits at a layer above individual route resolution.

```python
from starlette.middleware.base import BaseHTTPMiddleware

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        print(f"Incoming: {request.method} {request.url}")
        response = await call_next(request)
        print(f"Outgoing: {response.status_code}")
        return response
```

The `dispatch` method receives the incoming `request` and a `call_next` function. Code written **before** `call_next(request)` runs on the way in, before the route handler executes; code written **after** it runs on the way out, once the route handler has already produced a response. This before/after structure is the defining shape of nearly all middleware.

## Why Middleware Belongs at This Point in the Roadmap

Two things already built earlier in this roadmap are natural candidates for middleware, in hindsight:

- **Request timing and logging** — nothing currently logs how long each request to the auth system takes, or which routes are being hit most. Middleware is the correct place for this, since it would otherwise mean adding the same logging code to every single route individually.
- **A consistent `X-Request-ID` header** — useful for tracing a specific request through logs, especially once multiple services or a real deployment are involved. Adding this via middleware means every response gets the header automatically, without each route needing to remember to set it.

## `APIRouter` — Splitting Routes Across Files

As covered conceptually back when planning the auth system's folder structure, `APIRouter` allows routes to be defined in separate files and then combined into the main application:

```python
# routers/auth.py
from fastapi import APIRouter
router = APIRouter(tags=["auth"])

@router.post("/register")
def register(...):
    ...
```

```python
# main.py
from routers import auth
app.include_router(auth.router)
```

This phase goes further than what was needed to build the auth system — covering `prefix` (automatically prepending a path segment to every route in that router, e.g. `/auth/register` instead of `/register`), `tags` (grouping routes together in the Swagger docs UI), and nested routers (a router that itself includes other routers, useful for deeply organized applications).

## Request/Response Lifecycle and the `Request` Object

Every request-response cycle in FastAPI passes through a defined sequence: middleware (incoming) → dependency resolution → route handler execution → middleware (outgoing) → response sent. Understanding this order matters for reasoning about *where* a piece of logic should live — something needed for literally every request belongs in middleware; something needed only for specific routes belongs in a dependency; something needed only inside one specific route's own logic belongs directly in that route function.

The `Request` object, when a route or middleware needs raw access to the incoming request beyond what FastAPI's automatic parameter parsing provides, exposes things like raw headers, the client's IP address, the request body as raw bytes, and the URL — useful in middleware especially, since middleware operates before FastAPI has parsed anything into typed parameters.

## Custom Exception Handlers

FastAPI allows registering application-wide handlers for specific exception types, so that raising a particular exception anywhere in the application produces a consistently formatted error response, without every route needing its own try/except:

```python
@app.exception_handler(SomeCustomException)
async def handle_custom_exception(request: Request, exc: SomeCustomException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
```

This is a different mechanism from middleware, though related in spirit — it intercepts a specific *exception type* being raised anywhere in the call stack, rather than wrapping every request unconditionally.

## Lifespan Events — `startup` / `shutdown`

Some setup needs to happen once, when the application starts (opening a shared resource like a connection pool or an `httpx.AsyncClient`, as seen in the Async & Performance phase's shared-client sample) and torn down once, when the application stops. Lifespan events are the mechanism for this — code that runs exactly once at the beginning and exactly once at the end of the application's life, rather than per-request like middleware or per-route like a dependency.

## How These Pieces Relate to Each Other

| Mechanism | Runs for | Typical use |
|---|---|---|
| Middleware | Every request to the entire app | Logging, timing, headers, request-wide checks |
| `Depends()` (dependency) | Only routes that declare it | Auth checks, DB sessions, shared per-route logic |
| Exception handler | Any route where a specific exception type is raised | Consistent error response formatting |
| Lifespan event | Once, at app startup/shutdown | Shared resource setup/teardown |
| `APIRouter` | N/A — an organizational tool, not a runtime mechanism | Splitting routes across files for maintainability |

## Key Points to Retain

- Middleware operates above the level of individual routes — it runs for every request regardless of which route (or no route) it eventually reaches, and has a clear before/after structure around `call_next()`.
- `APIRouter` is purely organizational; it doesn't change runtime behavior, only how routes are grouped and structured across files.
- Custom exception handlers provide consistent error formatting tied to exception *types*, independent of which route raised them.
- Lifespan events are for once-per-application-life setup and teardown, distinct from both per-request middleware and per-route dependencies.