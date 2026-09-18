# I/O-Bound vs CPU-Bound Work

Understanding whether a given piece of work is I/O-bound or CPU-bound is the single most important judgment call in deciding whether `async` will help at all. This distinction determines everything downstream — whether to use `async def`, whether `asyncio.gather()` provides any benefit, and whether a thread pool or a process pool is the correct offloading tool.

## The Core Distinction

Every operation a program performs falls, broadly, into one of two categories based on where it spends most of its time:

- **I/O-bound work** spends most of its time **waiting** — waiting for a network response, waiting for a disk read/write to complete, waiting for a database to return query results. During that wait, the CPU itself is largely idle; it has nothing to compute because it's blocked on something external finishing first.
- **CPU-bound work** spends most of its time **actively computing** — running calculations, transforming data, executing loops. The CPU is continuously busy for the entire duration; there is no external event being waited on.

This distinction matters because `async`/`await` is specifically a mechanism for **not wasting idle waiting time** — while one operation is waiting on something external, the event loop can switch to progressing a different operation instead of sitting idle. If there is no waiting happening in the first place (as in CPU-bound work), there is nothing for async to usefully interleave.

## Why This Determines Whether Async Helps

Consider two operations, each taking roughly 2 seconds:

**I/O-bound example — calling an external API:**
```python
await httpx.AsyncClient().get("https://example.com/data")
```
For most of those 2 seconds, the program is doing essentially nothing except waiting for a response to travel across the network and come back. The CPU is free. If three such calls are issued concurrently via `asyncio.gather()`, all three waits can overlap — the total time is close to 2 seconds, not 6, because the CPU was never the bottleneck to begin with.

**CPU-bound example — a heavy calculation:**
```python
total = sum(i * i for i in range(50_000_000))
```
For the entire 2 seconds, the CPU is continuously occupied computing. There is no waiting to overlap with anything else — the CPU itself is the bottleneck. Running three such calculations "concurrently" via `async`/`await` provides no benefit, because a single CPU core can only execute one calculation at a time regardless of how the code is structured; `async` cannot make a busy CPU compute faster.

## Common Examples of Each Category

| I/O-bound | CPU-bound |
|---|---|
| Database queries | Image resizing/processing |
| External API calls (HTTP requests) | Video encoding |
| Reading/writing files on disk | Complex mathematical computation |
| Network socket communication | Cryptographic hashing at scale |
| Waiting on a message queue | Machine learning inference |
| Sending emails | Large in-memory data transformations |

Some operations are mixed — for example, processing an uploaded CSV file involves I/O (reading the file from disk or network) followed by CPU-bound work (parsing and transforming the data with pandas). Recognizing which *part* of a given task is I/O-bound versus CPU-bound allows applying the correct strategy to each part separately, rather than treating the whole operation as one category.

## Why Python's GIL Makes This Distinction Even More Important

Python's Global Interpreter Lock (GIL) ensures that only one thread executes Python bytecode at any given instant within a single process, regardless of how many threads exist. This has a direct consequence for CPU-bound work specifically:

- For **I/O-bound work**, the GIL is not a significant obstacle — while a thread is waiting on I/O (which happens outside the Python interpreter, at the operating system level), the GIL is released, allowing other threads or coroutines to proceed. This is why both `async`/`await` and traditional threading can meaningfully help I/O-bound work in Python.
- For **CPU-bound work**, the GIL prevents true parallel execution across threads within one process — even with multiple threads, only one can be actively running Python bytecode at a time. This means threading (and by extension, the automatic thread-pooling FastAPI applies to `def` routes) does **not** provide genuine parallelism for CPU-bound work; it only prevents one blocking call from freezing the entire application, without making the computation itself faster.

Genuine parallel speedup for CPU-bound work in Python requires a **process pool** (via `multiprocessing` or `concurrent.futures.ProcessPoolExecutor`) rather than a thread pool, since separate processes each have their own Python interpreter and their own GIL, allowing true simultaneous execution across CPU cores.

## Practical Decision Guide

| Question to ask | If yes |
|---|---|
| Does this operation spend most of its time waiting on a network response, disk I/O, or another external system? | I/O-bound — use `async def` with an async-compatible library, or `await`-based concurrency |
| Does this operation spend most of its time actively computing, with no external wait involved? | CPU-bound — use a process pool for genuine parallelism, or at minimum a thread pool (via `run_in_executor`) to avoid blocking the event loop |
| Does the operation involve both (e.g. fetch data, then process it heavily)? | Treat each part separately — async for the fetch, executor offloading for the processing |

## Key Points to Retain

- I/O-bound work benefits from async because the CPU is idle during waits, and that idle time can be reclaimed to progress other work.
- CPU-bound work does not benefit from async, because there is no idle waiting time to reclaim — the CPU is the bottleneck throughout.
- Python's GIL means threading provides safety/responsiveness for CPU-bound work (preventing one task from freezing everything) but not genuine speed — true parallel CPU work requires separate processes.
- Correctly identifying which category a given task belongs to — before choosing `async def` or a thread/process pool — is a prerequisite to writing performant code, not an afterthought.