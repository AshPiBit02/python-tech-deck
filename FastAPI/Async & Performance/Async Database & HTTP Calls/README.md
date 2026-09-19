# Async Database and HTTP Calls

Declaring a route `async def` only delivers a real benefit if every I/O operation inside it is backed by a library that is genuinely non-blocking — meaning it uses `await` at the point where it would otherwise wait on the network or disk, yielding control back to the event loop during that wait. This document covers what makes a database call or an HTTP call actually async-compatible, as opposed to merely being called from inside an `async def` function.

## The Core Requirement: The Driver Itself Must Support Async

Wrapping a call to a synchronous library inside `async def` does not make that call non-blocking. The library itself has to be built around `async`/`await` internally — typically by using non-blocking sockets under the hood and exposing coroutine-based methods.

```python
# Looks async, but requests is fully synchronous — this still blocks the event loop
async def bad_route():
    response = requests.get("https://example.com")   # no await possible; blocking call
    return response.json()
```

```python
# Genuinely async — httpx.AsyncClient is built for this
async def good_route():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com")
    return response.json()
```

The difference is not stylistic — `requests` has no coroutine-based API at all; there is no `await`-able version of `requests.get()`. `httpx.AsyncClient`, by contrast, is specifically designed so that `.get()`, `.post()`, and similar methods return awaitables that yield control back to the event loop while the network round-trip is in progress.

## Async HTTP Calls — `httpx`

`httpx` is a modern HTTP client for Python that provides both a synchronous and an asynchronous API, chosen via which client class is instantiated:

```python
import httpx

# Synchronous — blocking, safe only inside `def` routes
def sync_call():
    with httpx.Client() as client:
        return client.get("https://example.com").json()

# Asynchronous — non-blocking, safe inside `async def` routes
async def async_call():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://example.com")
        return response.json()
```

Key points about `httpx.AsyncClient`:

- It should generally be used as an async context manager (`async with`), which ensures the underlying connection pool is properly opened and closed.
- Creating a new `AsyncClient()` for every single request is somewhat wasteful in a high-traffic application — a common production pattern is to create one shared `AsyncClient` instance at application startup (e.g. via FastAPI's lifespan events) and reuse it across requests, rather than opening and closing a new client per call.
- Multiple calls using the same or different `AsyncClient` instances can be run concurrently via `asyncio.gather()`, since each `await client.get(...)` yields control back to the event loop during its network wait.

## Async Database Access — Why the Default SQLAlchemy Session Isn't Async

A standard SQLAlchemy setup, using `Session` and a synchronous driver such as `psycopg2` (for Postgres) or `pymysql` (for MySQL), is entirely synchronous. Every query executed through it — `db.query(...)`, `db.execute(...)`, `db.commit()` — blocks until the database responds, with no `await` involved anywhere in the call chain. Using this kind of session inside an `async def` route provides no concurrency benefit whatsoever; the blocking call still blocks the event loop exactly as if it were any other synchronous operation with no async support.

```python
# This is fully synchronous underneath, regardless of the route being async def
async def get_user_route(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()   # blocks the event loop
    return user
```

## Making Database Access Genuinely Async

Two things must change together to get real async database behavior:

1. **An async-capable database driver** — for Postgres, this means `asyncpg` instead of `psycopg2`; for MySQL, `aiomysql` instead of `pymysql`.
2. **SQLAlchemy's async extension** — `AsyncSession` and `create_async_engine`, from `sqlalchemy.ext.asyncio`, replacing the standard `Session`/`sessionmaker`/`create_engine` combination.

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydb"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
```

Queries executed through an `AsyncSession` use `await` explicitly, and use `select()` (SQLAlchemy's query-construction function) rather than the older `Query` object style:

```python
from sqlalchemy import select

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

Notice the pattern: `await db.execute(...)` yields control back to the event loop while the database processes the query, and `.scalar_one_or_none()` then extracts a single result (or `None`) from the returned result object once the await completes.

## Async vs Sync Session — Side-by-Side Comparison

| | Synchronous (`Session`) | Asynchronous (`AsyncSession`) |
|---|---|---|
| Driver | `psycopg2`, `pymysql` | `asyncpg`, `aiomysql` |
| Query execution | `db.query(User).filter(...).first()` | `await db.execute(select(User).where(...))` |
| Route type it belongs in | `def` (or `async def`, but with no benefit) | `async def`, correctly awaited |
| Concurrency benefit | None — always blocks the calling thread | Real — yields to the event loop during the DB round-trip |

## A Note on Migrating an Existing Synchronous Project

Switching an already-built application (such as a project using `Session` throughout its `services/` layer) from sync to async database access is a substantial, cross-cutting change — every function touching the database needs to become `async def` with `await` on each query, every route calling those functions needs to become `async def` as well, and the driver/connection string need to change. This is not something to do incrementally in isolated spots; a partially-migrated codebase mixing sync `Session` calls and async `AsyncSession` calls in different places is a common source of confusion and bugs. This kind of migration is typically planned as its own deliberate piece of work, rather than folded into an unrelated feature change.

## Key Points to Retain

- A library must be purpose-built for async — with genuine coroutine-based methods — for `await` to provide any real benefit; wrapping a synchronous call in `async def` does not convert it.
- `httpx.AsyncClient` is the async-compatible counterpart to the synchronous `requests` library, for outbound HTTP calls.
- Genuine async database access requires both an async driver (`asyncpg`, `aiomysql`) and SQLAlchemy's `AsyncSession`/`create_async_engine` — swapping only one of the two does not work.
- A synchronous `Session`-based codebase gains nothing from being called inside `async def` routes; it should remain on plain `def` routes until and unless a deliberate, complete migration to async database access is undertaken.