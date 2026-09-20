# Thread Pool for CPU-Bound Tasks — `run_in_executor`

As established in the I/O-bound vs CPU-bound topic, `async`/`await` provides no benefit for CPU-bound work, since there is no idle waiting time for the event loop to reclaim. However, CPU-bound work still needs to be handled carefully inside an `async def` route — running it directly, with no offloading, blocks the event loop for the entire duration of the computation. `run_in_executor` is the mechanism for correctly offloading such work.

## The Problem

```python
@app.get("/heavy-compute")
async def heavy_compute_route(n: int):
    total = sum(i * i for i in range(n))   # CPU-bound, no await anywhere
    return {"total": total}
```

Even though this route is declared `async def`, the summation loop runs entirely synchronously with no `await` inside it. For however long that loop takes, the event loop is fully occupied — every other concurrent request the application is trying to serve is stalled for that same duration, exactly as if a blocking I/O call had been made with no `await`.

## The Fix — Offloading to a Thread Pool

```python
import asyncio

def cpu_heavy_task(n: int):
    return sum(i * i for i in range(n))

@app.get("/heavy-compute")
async def heavy_compute_route(n: int):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, cpu_heavy_task, n)
    return {"total": result}
```

`loop.run_in_executor(executor, function, *args)` submits `function` to run in a separate thread (when `executor` is `None`, it uses the default thread pool executor), and returns an awaitable. `await`-ing that result yields control back to the event loop while the thread pool handles the actual computation — the event loop itself remains free to process other requests during that time, even though the CPU-bound work itself is not sped up by this change.

## What This Does and Doesn't Fix

It's important to be precise about what `run_in_executor` actually achieves:

- **It fixes:** event loop responsiveness. Other concurrent requests are no longer blocked while this one computation runs, because the computation has been moved off the event loop's thread entirely.
- **It does not fix:** the speed of the computation itself. The work still takes exactly as long; it has simply been relocated so that its duration no longer freezes everything else. If only one request is being processed at a time anyway, `run_in_executor` provides no visible speedup for that single request — its value appears specifically when multiple requests are happening concurrently, some CPU-bound and some not, and all need the event loop to remain responsive.

## Why a Thread Pool, Specifically — the GIL Reminder

As covered in the I/O-bound vs CPU-bound document, Python's Global Interpreter Lock means only one thread can execute Python bytecode at any instant within a single process. This means running two CPU-bound tasks in two different threads does **not** make them execute in true parallel — they still take turns, just as they would running sequentially, with some added overhead from thread switching. What a thread pool *does* provide, even under the GIL, is keeping the main event loop's thread free to keep accepting and dispatching other requests, rather than being the thread stuck running the computation itself.

## Using a Process Pool for Genuine Parallelism

When true parallel execution of CPU-bound work across multiple CPU cores is actually needed (not just event-loop responsiveness, but genuine speedup from running several heavy computations at once), a process pool is required instead of a thread pool, since each separate process has its own Python interpreter and its own GIL:

```python
from concurrent.futures import ProcessPoolExecutor

process_pool = ProcessPoolExecutor()

@app.get("/heavy-compute-parallel")
async def heavy_compute_parallel_route(n: int):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(process_pool, cpu_heavy_task, n)
    return {"total": result}
```

The usage pattern is nearly identical to the thread pool version — the difference is passing an explicit `ProcessPoolExecutor` instance instead of `None`. Process pools carry more overhead than thread pools (each worker is a full separate process, and arguments/results must be serialized to pass between processes), so they are generally reserved for work that is substantial enough to justify that overhead — a very short computation may actually run slower through a process pool than just running it directly, due to process-spawning and serialization costs outweighing the computation itself.

## Thread Pool vs Process Pool — Decision Summary

| | Thread Pool (`run_in_executor(None, ...)`) | Process Pool (`ProcessPoolExecutor`) |
|---|---|---|
| Keeps event loop responsive? | Yes | Yes |
| True parallel CPU execution? | No (limited by the GIL) | Yes (separate interpreters, separate GILs) |
| Overhead | Lower | Higher (process spawning, serialization) |
| Best suited for | Moderate CPU work, or work that's blocking mainly due to a library with no async support | Genuinely heavy, sustained CPU-bound computation |

## Key Points to Retain

- CPU-bound work placed directly inside an `async def` route with no offloading blocks the entire event loop for its full duration.
- `run_in_executor` offloads such work to a thread pool by default, keeping the event loop responsive to other requests — but does not make the computation itself faster.
- Python's GIL prevents genuine parallel execution of CPU-bound work across threads; a thread pool only isolates the blocking, it does not parallelize it.
- A `ProcessPoolExecutor` provides genuine parallel CPU execution by using separate processes, each with its own interpreter and GIL, at the cost of higher overhead — appropriate for substantial, sustained CPU-bound work rather than lightweight tasks.