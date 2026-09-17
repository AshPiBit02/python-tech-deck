# `async def` vs `def` in FastAPI

FastAPI is unusual among Python web frameworks in that it allows every route handler to be declared either as a plain synchronous function or as an asynchronous coroutine, side by side in the same application. Understanding exactly what each choice does under the hood — not just that "async is faster" — is essential before using either one correctly.

## What FastAPI Actually Does With Each

```python
@app.get("/sync-route")
def sync_route():
    ...

@app.get("/async-route")
async def async_route():
    ...
```

These two routes are handled through **completely different execution paths** inside FastAPI/Starlette, even though they look almost identical on the surface.

### `def` (synchronous) routes

When a route is declared as a plain `def`, FastAPI does not run it directly on the event loop. Instead, it automatically submits the function to run inside a **separate thread pool**, managed internally by Starlette (via `anyio`'s thread-offloading mechanism). The event loop itself is only responsible for scheduling that thread and waiting for its result — the function's actual body executes on a worker thread, not on the main async event loop.

This is a deliberate protective design: if a synchronous function performs a blocking operation (a blocking database call, `time.sleep()`, blocking file I/O), that blocking only ties up the *one thread* it's running on. The main event loop remains free to continue accepting and processing other requests concurrently, since it was never the one doing the blocking work in the first place.

### `async def` (asynchronous) routes

When a route is declared as `async def`, FastAPI treats it as a coroutine and runs it **directly on the main event loop** — no automatic thread offloading occurs. This is more efficient when done correctly, since coroutines are lightweight compared to spinning up threads, and the event loop can interleave many concurrent coroutines efficiently.

However, this efficiency depends entirely on the coroutine actually yielding control back to the event loop whenever it needs to wait on something — which only happens at points marked with `await`. If the coroutine's body contains a call to a blocking, synchronous operation with no `await` involved, that call executes directly on the event loop thread, and **the entire event loop freezes** for its duration — blocking not just that one request, but every other concurrent request the application is currently trying to serve.

## The Core Danger — Blocking Calls Inside `async def`

This is the single most important practical takeaway of this topic. Consider:

```python
import time

@app.get("/bad-async-route")
async def bad_async_route():
    time.sleep(5)   # blocking call, no await
    return {"status": "done"}
```

Even though this route is declared `async def`, `time.sleep(5)` is a fully synchronous, blocking call. Because it's not `await`-ed (and cannot be, since `time.sleep` isn't an async function), it runs directly on the event loop thread and blocks it for the full 5 seconds. During that window, **every other request hitting the application — regardless of which route they're calling — is stalled**, because there is only one event loop, and it is currently occupied.

Contrast this with the same mistake made in a `def` route:

```python
@app.get("/bad-sync-route")
def bad_sync_route():
    time.sleep(5)
    return {"status": "done"}
```

Here, the blocking `time.sleep(5)` still blocks — but only the *one worker thread* handling this specific request. Other concurrent requests, running in other threads or as other coroutines, are unaffected. This is precisely why FastAPI automatically thread-pools `def` routes: it's a safety net against exactly this kind of mistake.

**The counter-intuitive conclusion:** blindly converting a route to `async def` "to make it faster" is actively dangerous unless every operation inside it is genuinely non-blocking. A `def` route with a blocking call is contained to one thread; an `async def` route with the same blocking call can degrade the entire application's responsiveness.

## When `async def` Is Correctly Used

`async def` provides real benefit only when the operations inside it are implemented using `await` against genuinely asynchronous, non-blocking libraries:

```python
@app.get("/good-async-route")
async def good_async_route():
    await asyncio.sleep(5)   # non-blocking wait
    return {"status": "done"}
```

`asyncio.sleep()` (distinct from `time.sleep()`) is specifically designed to yield control back to the event loop while waiting, rather than blocking it — during those 5 seconds, the event loop is free to process other requests concurrently. This is the correct mental model: `async def` is a promise that the function will cooperate with the event loop by yielding at every wait point, not merely a syntactic label.

## Choosing Between Them in Practice

| Situation | Recommended choice |
|---|---|
| Route only does light computation, no I/O waiting | Either works; `def` is simpler and equally safe |
| Route performs I/O using a library with async support (`httpx`, `asyncpg`, async SQLAlchemy) | `async def`, using `await` on every I/O call |
| Route performs I/O using a library **without** async support (`requests`, synchronous `psycopg2`, blocking file operations) | `def` — let FastAPI's automatic thread-pooling protect the event loop |
| Route performs heavy CPU-bound computation | `def`, or `async def` combined with explicit thread/process pool offloading (`run_in_executor`) — never run CPU-heavy work directly inside `async def` with no offloading |
| Uncertain whether a given library is truly async-compatible | Default to `def` until confirmed — an incorrectly-assumed-async library blocking the event loop is a worse outcome than a slightly less optimal thread-pooled route |

## Key Points to Retain

- `def` routes run in a thread pool automatically; `async def` routes run directly on the event loop with no such protection.
- `async def` only delivers a benefit when every I/O operation inside it is genuinely awaited using an async-compatible library — declaring the function `async` does nothing by itself.
- A blocking call inside `async def` is more dangerous than the same blocking call inside `def`, because it can stall the entire application's event loop rather than just one thread.
- When in doubt about whether a library is safe to use inside `async def`, defaulting to a synchronous `def` route is the safer choice.