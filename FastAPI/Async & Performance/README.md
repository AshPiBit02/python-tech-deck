# Async & Performance in FastAPI

FastAPI is built on top of Starlette and the ASGI standard, which means it natively supports asynchronous request handling. This phase covers how and when to use `async def`, how to run multiple I/O operations concurrently, how to offload work without blocking the response, and how to handle CPU-bound work correctly in an otherwise async framework.

---

## `async def` vs `def` in FastAPI

FastAPI allows route handlers to be declared either as a regular synchronous function or as an `async` coroutine function:

```python
@app.get("/sync-route")
def sync_route():
    ...

@app.get("/async-route")
async def async_route():
    ...
```

Both work, but they behave very differently under the hood:

- **`async def` routes** run directly on the main event loop. FastAPI awaits them as coroutines, meaning the event loop is free to handle other requests while an `async def` route is waiting on something (a database query, an HTTP call, `asyncio.sleep`), as long as that "waiting" is itself implemented using `await`.
- **`def` (synchronous) routes** are automatically run in a separate thread pool, managed by Starlette, so that a blocking synchronous call inside them doesn't freeze the entire event loop for other requests. This is a deliberate safety net — FastAPI protects the application from a naive blocking call inside a `def` route by offloading it to a thread.

**The critical rule:** declaring a route `async def` does **not** automatically make it non-blocking. If an `async def` route calls a blocking, synchronous operation internally (a synchronous database driver, `time.sleep()`, a blocking file read) without `await`, that blocking call freezes the **entire event loop** — not just that one request, but every other concurrent request being served by the application. This is a common and serious mistake: mixing sync blocking calls inside `async def` routes is worse than just using `def` in the first place, since `def` routes get automatic thread-pool protection that `async def` routes do not.

## When Async Actually Helps

Async provides a real benefit specifically for **I/O-bound** work — operations that spend most of their time waiting on something external (network responses, disk I/O, database round-trips) rather than actively computing. During that wait, the event loop can switch to handling other requests instead of sitting idle.

Async provides **no benefit** for **CPU-bound** work — operations that spend their time actively computing (image processing, heavy numeric calculations, complex data transformations). Making a CPU-bound function `async` does nothing useful, since there's no waiting for the event loop to fill with other work; the CPU is busy the entire time regardless of whether the function is a coroutine or not.

| Workload type | Examples | Benefits from `async`? |
|---|---|---|
| I/O-bound | Database queries, external API calls, file/network I/O | Yes |
| CPU-bound | Image processing, encryption, complex calculations, ML inference | No — use a thread pool or process pool instead |

## `await` with Database Calls and HTTP Requests

To get a real benefit from `async def`, the operations inside the route must themselves support async — meaning they use `await` internally and are backed by a non-blocking driver.

- **Database calls** — using a synchronous SQLAlchemy session (`Session`, blocking `psycopg2` driver) inside an `async def` route provides no concurrency benefit and can block the event loop; genuine async database access requires an async driver (e.g. `asyncpg` for Postgres) and `AsyncSession` from SQLAlchemy's async extension.
- **HTTP calls to other services** — the standard `requests` library is synchronous and blocking; using it inside `async def` blocks the event loop. `httpx` is the async-capable equivalent, supporting `await client.get(...)` for genuinely non-blocking outbound HTTP calls.

## `asyncio.gather()` — Running Independent Tasks Concurrently

When a route needs to perform multiple independent async operations — calling several external APIs, querying multiple unrelated data sources — running them one after another sequentially wastes the very benefit async is meant to provide:

```python
# Sequential — total time ≈ sum of each call's duration
result_a = await fetch_a()
result_b = await fetch_b()
result_c = await fetch_c()
```

```python
# Concurrent — total time ≈ the duration of the SLOWEST call, not the sum
result_a, result_b, result_c = await asyncio.gather(fetch_a(), fetch_b(), fetch_c())
```

`asyncio.gather()` schedules all provided coroutines to run concurrently on the event loop and returns their results together, in the same order they were passed in, once all have completed. This is the core mechanism behind meaningful async performance gains — the improvement doesn't come from any single operation being faster, but from multiple independent waits overlapping instead of stacking.

## `BackgroundTasks` — Work After the Response Is Sent

Some operations don't need to complete before a response is returned to the client — sending a confirmation email after registration, writing an audit log entry, notifying an external system. `BackgroundTasks` lets such work run **after** the response has already been sent back, without making the client wait for it:

```python
from fastapi import BackgroundTasks

def send_email(email: str):
    ...  # runs after the response has already been returned

@app.post("/register")
def register(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com")
    return {"message": "Registered"}
```

The function passed to `add_task` can be either synchronous or asynchronous; FastAPI handles both correctly. This is distinct from `asyncio.gather()` — `gather()` is for running things concurrently *before* responding (because the response depends on their results), while `BackgroundTasks` is for running things *after* responding (because the response doesn't depend on their results at all).

## Thread Pool for CPU-Bound Work — `run_in_executor`

Since async provides no benefit for CPU-bound work, and running such work directly inside an `async def` route would block the event loop, CPU-bound operations should be explicitly offloaded to a separate thread (or process) pool:

```python
import asyncio

def cpu_heavy_task(data):
    ...  # blocking, CPU-intensive work

@app.post("/process")
async def process(data: dict):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, cpu_heavy_task, data)
    return {"result": result}
```

`run_in_executor` submits the blocking function to a thread pool (the default executor, when `None` is passed) and returns an awaitable — the event loop remains free to handle other requests while the CPU-bound function runs in its own thread. For genuinely CPU-intensive work in Python, a **process pool** is often more effective than a thread pool, due to the Global Interpreter Lock (GIL) limiting true parallel CPU execution across threads within a single process — worth knowing as a further distinction once this pattern becomes necessary in practice.

## Key Points to Retain

- `async def` is not a performance guarantee by itself — it only helps when every I/O operation inside the route is genuinely awaited using async-compatible libraries.
- Mixing a blocking synchronous call inside an `async def` route is a serious anti-pattern — it can stall the entire application's event loop, not just the single request making the blocking call.
- `def` routes are automatically thread-pooled by FastAPI as a safety mechanism; `async def` routes receive no such automatic protection.
- `asyncio.gather()` is for concurrent execution of multiple awaitables whose results are all needed before responding.
- `BackgroundTasks` is for fire-and-forget work that should happen after the response, not before it.
- CPU-bound work should never be placed directly inside an `async def` route without offloading it to a thread or process pool via `run_in_executor` or a similar mechanism.