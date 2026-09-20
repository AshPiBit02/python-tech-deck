# `BackgroundTasks` — Work After the Response Is Sent

Not every operation triggered by a request needs to finish before that request's response is returned. `BackgroundTasks` is FastAPI's built-in mechanism for deferring such work to run **after** the response has already been sent back to the client, so the client isn't kept waiting on something it doesn't actually need to wait for.

## The Problem It Solves

Consider a registration route that, upon success, should also send a welcome email:

```python
def register(user_in: UserRegistration, db: Session = Depends(get_db)):
    db_user = create_user(db, user_in)
    send_welcome_email(db_user.email)   # this call blocks until the email is fully sent
    return db_user
```

If `send_welcome_email` takes even a second or two (connecting to an email provider's API, waiting for their response), the client submitting the registration form is forced to wait that entire extra duration before receiving a response — even though the actual registration itself was already complete. The email sending has no bearing on whether the response should be considered successful; it's a side effect the client doesn't need to wait on.

## The Fix

```python
from fastapi import BackgroundTasks

def send_welcome_email(email: str):
    ...  # this now runs AFTER the response has already gone out

@app.post("/register")
def register(user_in: UserRegistration, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = create_user(db, user_in)
    background_tasks.add_task(send_welcome_email, db_user.email)
    return db_user
```

`background_tasks.add_task(function, *args, **kwargs)` schedules `function` to be called with the given arguments, but that call only actually happens **after** the response body has been sent back over the network. The client receives their response immediately upon `return db_user`, without waiting for `send_welcome_email` to run at all.

## `BackgroundTasks` as a Dependency, Not Just a Parameter

`BackgroundTasks` is injected by simply declaring it as a parameter with that type annotation — no `Depends()` needed, since FastAPI recognizes this type specially, similar to how `Request` or `SecurityScopes` are recognized. Multiple calls to `add_task()` within the same route accumulate a queue of tasks, all of which run after the response, in the order they were added.

```python
@app.post("/register")
def register(user_in: UserRegistration, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = create_user(db, user_in)
    background_tasks.add_task(send_welcome_email, db_user.email)
    background_tasks.add_task(log_registration_event, db_user.id)
    return db_user
```

Both tasks run after the response, one after another, in the order `add_task` was called.

## Sync or Async Functions Both Work

The function passed to `add_task` can be either a regular synchronous function or an `async def` coroutine function — FastAPI handles both correctly:

```python
def sync_background_job(data: str):
    ...

async def async_background_job(data: str):
    await something()

background_tasks.add_task(sync_background_job, "some data")
background_tasks.add_task(async_background_job, "some data")
```

## `BackgroundTasks` vs `asyncio.gather()` — Different Purposes

These two are easy to conflate since both relate to running multiple things, but they solve opposite problems:

| | `asyncio.gather()` | `BackgroundTasks` |
|---|---|---|
| When it runs | Before the response — the route needs the result(s) | After the response — the route does not need the result |
| What it's for | Running independent operations concurrently so the *response* can be built from all their results together | Deferring work whose outcome the client doesn't need to know about at all |
| Does the client wait? | Yes — the response is only sent once all gathered operations complete | No — the response is sent immediately; background work happens afterward |

Using `gather()` for something that should be a background task (like an email send) would still make the client wait unnecessarily. Using `BackgroundTasks` for something the response actually depends on (like a lookup whose result appears in the response body) would be a bug — the response would have already been sent before that data was ever computed.

## Practical Considerations and Limits

- **Background tasks run within the same server process**, on the same event loop or thread pool as the rest of the application — they are not a separate, isolated worker system. For truly heavy or failure-sensitive background work (retryable jobs, work that must survive a server restart), a dedicated task queue system such as Celery with Redis is the appropriate tool, not `BackgroundTasks` — this is covered later in the roadmap under Background Workers.
- **If a background task raises an exception**, it does not affect the already-sent response (since the response has already gone out), but the exception will typically be logged by the server rather than silently disappearing — worth wrapping background task functions in their own error handling if a failure needs specific handling (e.g. retry logic, alerting).
- **A background task should not be relied upon to run within any specific guaranteed timeframe** relative to the response — it's scheduled to run after the response is sent, but exact timing depends on the server's current load and the state of the event loop.

## Key Points to Retain

- `BackgroundTasks` defers work to run after a response has already been returned to the client, avoiding unnecessary wait time for operations whose result the client doesn't need.
- It is injected as a plain type-annotated parameter, with `add_task(function, *args, **kwargs)` used to schedule work.
- Both sync and async functions work correctly with `add_task`.
- It solves a different problem than `asyncio.gather()` — deferred work after responding, versus concurrent work before responding whose results are needed in the response itself.
- For work requiring guarantees beyond what a single server process can provide (retries, persistence across restarts), a dedicated task queue is the correct tool, not `BackgroundTasks`.