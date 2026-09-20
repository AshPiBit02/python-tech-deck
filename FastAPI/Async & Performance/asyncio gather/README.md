# `asyncio.gather()` — Running Independent Async Operations Concurrently

Once a route's I/O operations are genuinely async — using `await` against async-compatible libraries such as `httpx.AsyncClient` or SQLAlchemy's `AsyncSession` — the next question is how to run *multiple* such operations at once, when they don't depend on each other's results. `asyncio.gather()` is the primary tool for this.

## The Problem It Solves

Consider a route that needs to fetch data from three independent external sources before responding:

```python
async def get_dashboard_data():
    weather = await fetch_weather()      # takes ~1 second
    stock_price = await fetch_stock()    # takes ~1 second
    news = await fetch_news()            # takes ~1 second
    return {"weather": weather, "stock": stock_price, "news": news}
```

Even though each individual `await` correctly yields control back to the event loop, this code still runs the three calls **sequentially** — `fetch_weather()` must fully complete before `fetch_stock()` even starts, because each line waits for the previous one to finish before moving to the next. Total time: roughly 3 seconds (1 + 1 + 1), even though none of these three calls depend on each other's output at all.

## The Fix — Launching Them Together

```python
import asyncio

async def get_dashboard_data():
    weather, stock_price, news = await asyncio.gather(
        fetch_weather(),
        fetch_stock(),
        fetch_news(),
    )
    return {"weather": weather, "stock": stock_price, "news": news}
```

`asyncio.gather()` takes multiple awaitables (coroutines, in this case) and schedules all of them to run **concurrently** on the event loop, rather than one after another. Since none of the three depend on each other, their waiting periods overlap — total time becomes roughly 1 second (the duration of the slowest one), not 3.

## How It Actually Works

`asyncio.gather()` does not create separate threads or processes — everything still runs on the single event loop. What it does is schedule all the passed coroutines as concurrent tasks; whenever one of them hits an `await` point and yields control (waiting on a network response, for instance), the event loop uses that idle moment to progress one of the *other* coroutines instead of sitting idle. This is why the benefit only applies to I/O-bound work — if any of the three functions were CPU-bound instead, there would be no idle waiting moment for the event loop to fill with other work, and `gather()` would provide no speedup for that particular call.

## Return Value Ordering

```python
result_a, result_b, result_c = await asyncio.gather(coro_a(), coro_b(), coro_c())
```

The results are returned in a list, in the **same order the coroutines were passed in** — regardless of which one actually finished first internally. This makes unpacking predictable: `result_a` always corresponds to `coro_a()`'s return value, even if `coro_c()` happened to complete before it.

## Error Handling Behavior

By default, if any one of the gathered coroutines raises an exception, `asyncio.gather()` immediately propagates that exception to the caller — but the other coroutines that were still running are **not automatically cancelled**; they continue running in the background unless explicitly handled. This can be a source of subtle bugs (background work continuing after the function has already "failed" from the caller's perspective).

To gather results while tolerating individual failures rather than aborting on the first one, `return_exceptions=True` changes the behavior:

```python
results = await asyncio.gather(coro_a(), coro_b(), coro_c(), return_exceptions=True)
```

With this flag, if any coroutine raises, the exception object itself is placed into the results list at that position instead of being raised immediately — allowing the caller to inspect which specific calls succeeded and which failed, rather than the whole operation aborting because of one failure.

## When `gather()` Does Not Help

- **When operations depend on each other's results** — if `fetch_stock()` needed the result of `fetch_weather()` as an input, they cannot run concurrently regardless of any tooling, since one genuinely cannot start before the other finishes.
- **When the operations are CPU-bound** — as covered in the I/O-bound vs CPU-bound topic, there is no idle waiting time in CPU-bound work for the event loop to fill with other progress; `gather()` provides no benefit here (and combining it with CPU-bound coroutines can still block the event loop for the full duration of whichever one runs first, since neither can yield mid-computation).
- **When there is only one operation to perform** — `gather()` exists specifically to combine *multiple* concurrent awaitables; with a single coroutine, plain `await` is sufficient and clearer.

## Key Points to Retain

- `asyncio.gather()` runs multiple independent async operations concurrently on the same event loop, reducing total wait time to roughly the duration of the slowest operation rather than their sum.
- It only provides benefit for genuinely async, I/O-bound operations — it does not parallelize CPU-bound work, and does not create threads or processes.
- Results are returned in the same order the coroutines were passed in, not in completion order.
- By default, one failing coroutine propagates its exception immediately without cancelling the others; `return_exceptions=True` changes this to collect all outcomes, successes and failures alike, into the results list.