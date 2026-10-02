# Lifespan Events — Advanced Usage

Briefly, as groundwork: lifespan events are code that runs exactly once when the application starts, and exactly once when it stops — distinct from middleware (runs per request) and dependencies (runs per route that declares them). The current, correct way to define them is the `lifespan` context manager via `@asynccontextmanager`; the older `@app.on_event("startup")` / `@app.on_event("shutdown")` decorators are deprecated and should not be used in new code.

## The Current Pattern, in Full

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Code here runs ONCE, before the app accepts any requests ----
    print("Starting up...")

    yield   # <- the application runs here, handling requests, until shutdown

    # ---- Code here runs ONCE, after the app stops accepting requests ----
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
```

The function is an async generator wrapped with `@asynccontextmanager`, following the same `yield`-splits-setup-from-teardown shape already familiar from `get_db()`-style dependencies elsewhere in this roadmap — everything before `yield` is setup, everything after is teardown, and the application serves requests during the period `yield` is paused.

## Why This Replaced `@app.on_event`

The older decorator-based approach registered `startup` and `shutdown` as two entirely separate functions, with no structural link between them:

```python
# DEPRECATED — do not use in new code
@app.on_event("startup")
async def startup():
    app.state.http_client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown():
    await app.state.http_client.aclose()
```

The problem this created: nothing enforced that a resource set up in `startup` was properly torn down in a matching `shutdown` — the two functions lived independently, and it was easy for teardown logic to drift out of sync with setup logic, or be forgotten entirely for a newly added resource. The `lifespan` context manager fixes this structurally: setup and teardown for the *same* resource live in the *same* function, with `yield` as the dividing line — there's no way to write setup code without the corresponding teardown code sitting right below it in the same block.

## Managing Multiple Resources Correctly

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()
    app.state.db_engine = create_async_engine(settings.database_url)
    print("All resources initialized.")

    yield

    await app.state.http_client.aclose()
    await app.state.db_engine.dispose()
    print("All resources cleaned up.")
```

For straightforward cases, listing setup calls before `yield` and their corresponding teardown calls after `yield`, in reverse order, is sufficient. For resources where setup itself might fail partway through (e.g. the second resource fails to initialize after the first succeeded), a `try`/`finally` structure ensures teardown still runs for whatever *did* get set up:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()
    try:
        app.state.db_engine = create_async_engine(settings.database_url)
        yield
    finally:
        await app.state.http_client.aclose()
        if hasattr(app.state, "db_engine"):
            await app.state.db_engine.dispose()
```

## Accessing Lifespan-Created Resources Inside Routes

Resources set on `app.state` during lifespan setup are accessible from any route or dependency via the request's `app` reference:

```python
@app.get("/quote")
async def get_quote(request: Request):
    response = await request.app.state.http_client.get("https://api.quotable.io/random")
    return response.json()
```

`request.app` refers back to the same `FastAPI` instance the lifespan function configured — this is how a single, shared resource (one connection pool, one HTTP client) ends up reused across every request's lifetime, rather than being recreated per request as covered in the Async & Performance phase's `httpx.AsyncClient` discussion.

## Lifespan Events and Testing

A detail worth knowing once testing (as already built for the auth system) enters the picture: `TestClient`, when used as a context manager, correctly triggers lifespan startup and shutdown around the test session:

```python
with TestClient(app) as test_client:
    response = test_client.get("/quote")
```

Using `TestClient(app)` *without* the `with` block does **not** reliably trigger lifespan events in the same way — this is why the auth system's own `conftest.py` fixture wraps `TestClient` in a `with` statement rather than instantiating it directly, ensuring any lifespan-managed resources are genuinely available during tests rather than silently `None` or unset.

## What Belongs in Lifespan vs What Doesn't

| Belongs in lifespan | Does NOT belong in lifespan |
|---|---|
| Creating a shared `httpx.AsyncClient` or connection pool | Per-request logic (that's middleware or a dependency) |
| Opening a database engine/connection pool | Logic specific to one route |
| Loading a large ML model into memory once | Anything needing fresh data per request |
| Warming a cache at startup | Request-specific authentication/authorization checks |

The defining test: if something should happen exactly once for the application's entire lifetime, regardless of how many requests come and go, it belongs in lifespan. If it needs to happen per request, it belongs in middleware or a dependency instead — conflating the two is a common early mistake, already flagged in the Request/Response Lifecycle document.

## Key Points to Retain

- The current, correct pattern is the `lifespan` context manager via `@asynccontextmanager`, passed to `FastAPI(lifespan=lifespan)` — the older `@app.on_event` decorators are deprecated.
- `yield` divides setup (before) from teardown (after), structurally linking the two for the same resource in one function, unlike the old two-separate-functions approach.
- Resources set on `app.state` during lifespan setup are accessible in routes via `request.app.state`, enabling genuine reuse across every request rather than per-request recreation.
- `TestClient` must be used as a context manager (`with TestClient(app) as client:`) for lifespan events to reliably trigger during tests.
- Lifespan is for once-per-application-life setup/teardown only — anything needing to run per request belongs in middleware or a dependency instead.