# Lifespan Events — Real-World Use Cases

This document covers concrete problems lifespan events solve in production systems, each framed as problem → solution, followed by additional detail — composing multiple lifespans, readiness/health-check integration, and graceful shutdown — not covered in the conceptual document.

## Case 1 — Reusing a Database Connection Pool Instead of Reconnecting Per Request

**Problem:** Without lifespan, a naive implementation might open a new database connection inside every route that needs one:
```python
@app.get("/orders")
async def get_orders():
    engine = create_async_engine(settings.database_url)   # opened fresh, every single request
    async with engine.connect() as conn:
        result = await conn.execute(select(Order))
        return result.fetchall()
```
Establishing a new database connection involves a real network handshake and authentication round-trip — doing this on every single request adds meaningful latency to every response and can exhaust the database server's own connection limit under real traffic, since connections aren't being pooled or reused at all.

**Solution:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_engine = create_async_engine(settings.database_url, pool_size=10)
    yield
    await app.state.db_engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.get("/orders")
async def get_orders(request: Request):
    async with request.app.state.db_engine.connect() as conn:
        result = await conn.execute(select(Order))
        return result.fetchall()
```
The engine (and its internal connection pool) is created exactly once, at startup, and every request borrows a connection from that existing pool rather than establishing a new one from scratch — this is the same underlying principle as your own project's `SessionLocal`/`get_db` pattern, just at the engine level, set up once for the application's whole life instead of per-request.

## Case 2 — Loading a Large Machine Learning Model Once

**Problem:** An API endpoint uses a trained ML model to make predictions. Loading such a model from disk is often slow (seconds, sometimes longer for large models) and memory-intensive. Loading it inside the route function itself would repeat this slow, expensive work on every single request:
```python
@app.post("/predict")
def predict(data: dict):
    model = load_model_from_disk("model.pkl")   # slow, repeated every request
    return {"prediction": model.predict(data)}
```

**Solution:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = load_model_from_disk("model.pkl")   # loaded ONCE
    yield
    # models typically don't need explicit teardown, but some do (e.g. releasing GPU memory)

app = FastAPI(lifespan=lifespan)

@app.post("/predict")
def predict(data: dict, request: Request):
    return {"prediction": request.app.state.model.predict(data)}
```
The expensive load happens exactly once, when the server process starts, and every subsequent request simply uses the already-loaded model from memory — turning a potentially multi-second cost per request into a near-zero cost after the first startup.

## Case 3 — Warming a Cache Before Accepting Real Traffic

**Problem:** An application relies on an in-memory cache (e.g. a lookup table of product categories, rarely-changing reference data) to avoid hitting the database for every request needing that data. If the cache starts empty and only fills in lazily on first access, the very first requests after a deploy experience a slowdown (a "cold cache") while that initial population happens under real user traffic.

**Solution:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.category_cache = await load_categories_from_db()   # pre-warmed before traffic arrives
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/categories")
def get_categories(request: Request):
    return request.app.state.category_cache
```
Because lifespan setup completes *before* the application begins accepting any requests at all, the very first real request already benefits from a warm cache — there's no "unlucky first user" who pays the cold-cache cost that later users don't.

## Case 4 — Readiness/Health Checks Tied to Lifespan State

**Problem:** In a real deployment (especially container orchestration platforms like Kubernetes), a load balancer or orchestrator needs to know whether an application instance is actually ready to serve traffic — not just whether its process has started, but whether its critical dependencies (database, cache, external services) finished initializing successfully. Without this, traffic can be routed to an instance that's technically running but not genuinely ready, causing real request failures.

**Solution:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    app.state.db_engine = create_async_engine(settings.database_url)
    try:
        async with app.state.db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))   # confirm the DB is actually reachable
        app.state.ready = True
        yield
    finally:
        await app.state.db_engine.dispose()

app = FastAPI(lifespan=lifespan)

@app.get("/health/ready")
def readiness_check(request: Request):
    if not request.app.state.ready:
        raise HTTPException(status_code=503, detail="Not ready")
    return {"status": "ready"}
```
This directly builds on the "Concurrent Multi-API Health Checker" project from the Async & Performance phase, but ties readiness specifically to lifespan-managed state — a `/health/ready` route an orchestrator can poll, reporting `503` until lifespan setup has genuinely confirmed the database is reachable, not merely that the process has booted.

## Additional Detail — Composing Multiple Lifespans

For a larger application where different concerns each want their own lifespan logic (e.g. one for the database, one for a cache client, one for an ML model), a single application only accepts one `lifespan` function — but that function can internally compose several smaller async context managers using `contextlib.AsyncExitStack`, rather than cramming everything into one large, unstructured function:

```python
from contextlib import AsyncExitStack, asynccontextmanager

@asynccontextmanager
async def db_lifespan(app: FastAPI):
    app.state.db_engine = create_async_engine(settings.database_url)
    yield
    await app.state.db_engine.dispose()

@asynccontextmanager
async def cache_lifespan(app: FastAPI):
    app.state.cache_client = await create_cache_client()
    yield
    await app.state.cache_client.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(db_lifespan(app))
        await stack.enter_async_context(cache_lifespan(app))
        yield

app = FastAPI(lifespan=lifespan)
```
Each concern stays in its own clearly named, independently readable function, while `AsyncExitStack` guarantees all of them are properly entered and — critically — properly exited in the correct reverse order, even if something goes wrong partway through, without needing to hand-write a sprawling nested `try`/`finally` structure.

## Additional Detail — Lifespan and Graceful Shutdown

When a server process receives a shutdown signal (e.g. during a deploy, or a container orchestrator scaling down an instance), Uvicorn typically stops accepting *new* connections first, allows in-flight requests to finish, and only then triggers the lifespan's teardown section. This ordering matters: teardown code (closing a database engine, for instance) is written with the expectation that no requests are actively using that resource anymore by the time it runs — tearing down a connection pool while requests are still actively using it would cause those in-flight requests to fail. Understanding this ordering explains why lifespan teardown is a safe place to close shared resources without needing additional coordination logic to check "is anything still using this" — that coordination is already handled by the server's shutdown sequence before teardown code ever executes.

## Key Points to Retain

- Lifespan events solve a specific, recurring category of real-world problem: expensive, one-time setup work (connections, model loading, cache warming) that should never be repeated per request.
- Tying a readiness check's response to lifespan-set state is a practical, production-relevant pattern for integrating with load balancers and orchestrators correctly.
- `AsyncExitStack` allows composing several independent lifespan concerns into one application without sacrificing readability or risking improper cleanup ordering.
- The server's shutdown sequence (stop accepting new connections, drain in-flight requests, then run lifespan teardown) is what makes it safe to close shared resources in teardown without additional "is anything still using this" coordination.