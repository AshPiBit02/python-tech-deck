# Request/Response Lifecycle — Advanced Usage

Briefly, as groundwork: a request passes through middleware, then dependency resolution, then the route handler itself, then back out through middleware again on the way to the response. This document goes past that basic ordering into why the ordering matters for real decisions, illustrated with concrete code at each stage, and where things commonly go wrong once several of the mechanisms covered in this phase are combined in one application.

## The Lifecycle as a Decision Tool, Not Just a Diagram

The practical value of understanding the lifecycle in detail isn't being able to recite the order — it's using that order to decide, correctly and quickly, *where a given piece of logic belongs* when building something new. Every mechanism covered elsewhere in this phase (middleware, dependencies, exception handlers, lifespan events) occupies a specific position in this lifecycle, and placing logic in the wrong position produces subtle, hard-to-diagnose bugs rather than an obvious failure.

Consider a concrete instance: a check for "is this request coming from a banned IP address."

**Placed as middleware — runs before anything else, including before a DB session is opened:**
```python
BANNED_IPS = {"203.0.113.7"}

@app.middleware("http")
async def block_banned_ips(request, call_next):
    if request.client.host in BANNED_IPS:
        return JSONResponse(status_code=403, content={"detail": "Access denied"})
    return await call_next(request)
```
A banned request is rejected here at essentially zero cost — no dependency has resolved yet, no database connection has been opened, nothing beyond reading `request.client.host` has happened.

**Placed instead as a per-route dependency:**
```python
def block_banned_ips_dependency(request: Request, db: Session = Depends(get_db)):
    # by the time this line runs, get_db has ALREADY opened a real DB connection
    if request.client.host in BANNED_IPS:
        raise HTTPException(status_code=403, detail="Access denied")

@app.get("/notes")
def read_notes(_: None = Depends(block_banned_ips_dependency)):
    ...
```
Because `db: Session = Depends(get_db)` is declared alongside the ban check in the same route's dependency list, FastAPI resolves `get_db` regardless of ordering in the function signature — the database connection is opened and then immediately discarded for a request that was always going to be rejected. Same logic, same outcome, meaningfully different cost — purely because of *where in the lifecycle* the check was placed.

## Dependency Resolution Order Within a Single Request

Multiple dependencies on one route, and dependencies-of-dependencies, form their own internal ordering — this is exactly the shape already built in the auth system:

```python
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access Denied")
    return current_user
```

Since `require_admin` declares `current_user: dict = Depends(get_current_user)`, FastAPI resolves `get_current_user` **first**, fully, before `require_admin`'s own body ever executes. This produces a guaranteed ordering for a given request:

- **A request with an invalid token** → fails inside `get_current_user` → `401` is raised → `require_admin`'s role check is **never reached at all**.
- **A request with a valid token but a non-admin role** → `get_current_user` succeeds → `require_admin`'s own check then runs → `403` is raised.

This is why, for any route protected by `Security(require_admin)` or `Depends(require_admin)`, a `403` can only ever occur for a request that already has a genuinely valid token — the two error codes are not just conventionally different, they're structurally guaranteed to occur in that order by the dependency graph itself, not by any explicit ordering logic anyone wrote.

## Where Middleware, Dependencies, and Exception Handlers Interact

```python
@app.middleware("http")
async def timing_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)        # <- an exception raised anywhere
                                                  #    inside here still results in
                                                  #    a normal `response` object by
                                                  #    the time execution reaches here
    duration = time.perf_counter() - start
    print(f"{request.url.path} took {duration:.3f}s -> status {response.status_code}")
    return response
```

- **An exception raised inside a dependency** (e.g. `HTTPException` inside `get_current_user`) is caught by FastAPI's own exception-handling layer, which sits *inside* the middleware layer from the request's perspective. This means `timing_middleware`'s code after `call_next()` still runs, and `response.status_code` will correctly show `401` — even though the actual route function's body never executed at all. The middleware needs no special-casing for this; by the time control returns to it, the exception has already become a normal response object.

- **A custom exception handler** intercepts a given exception type regardless of which layer raised it:
```python
class OutOfStockError(Exception):
    def __init__(self, product_id: str):
        self.product_id = product_id

@app.exception_handler(OutOfStockError)
async def handle_out_of_stock(request: Request, exc: OutOfStockError):
    return JSONResponse(status_code=409, content={"detail": f"Product {exc.product_id} is out of stock"})
```
Whether `OutOfStockError` is raised directly inside a route, or several layers deep inside a dependency that route depends on, this handler catches it either way and produces the response *before* it reaches `timing_middleware`'s "after" section — middleware always sees a fully-formed response, never a raw unhandled exception, as long as some handler exists for whatever was raised.

- **An exception with no matching handler at all** results in FastAPI's default handling (typically a `500`), which still passes back out through middleware the same way any other response does. `timing_middleware` above would print `status 500` for this case, exactly as it would for an intentional `409` from `OutOfStockError` — middleware generally cannot distinguish "the route succeeded and deliberately returned an error" from "something crashed unexpectedly," which is a real limitation worth knowing if middleware logic ever needs to react differently to those two situations (e.g. alerting only on genuine crashes, not on routine `404`s).

## Lifespan Events Sit Outside the Per-Request Lifecycle Entirely

```python
@app.on_event("startup")
async def startup():
    app.state.http_client = httpx.AsyncClient()   # created ONCE, before any request arrives

@app.on_event("shutdown")
async def shutdown():
    await app.state.http_client.aclose()          # closed ONCE, after the last request finishes
```

It's worth being precise that this is not part of the per-request lifecycle at all — `startup` runs once, before the application begins accepting any requests, and `shutdown` runs once, after it stops accepting them. `app.state.http_client` is expected to already exist and be ready by the time the very first request's lifecycle begins, and to still exist through the very last request's lifecycle before shutdown teardown runs. Conflating "runs once, before any request" with "runs at the start of every request" is a common early confusion — a lifespan event and a middleware's "before" section look superficially similar in that both run "early," but operate on entirely different timescales (once per application life, versus once per individual request).

## Reasoning About Ordering When Debugging

When something behaves unexpectedly in an application using several of these mechanisms together, the lifecycle ordering is the first tool for narrowing down where to look:

| Symptom | Points toward |
|---|---|
| Happens for every single request, regardless of route | Middleware |
| Happens only for requests to routes sharing a particular dependency | That dependency, or something *it* depends on |
| A specific exception type behaves oddly across every route that can raise it | An exception handler |
| Only happens around application start/restart, not during normal operation | A lifespan event |

Framing a bug in terms of *which stage of the lifecycle it must be occurring in* is often faster than guessing at the specific mechanism first — e.g. "every route is slow" points at middleware or a shared dependency long before it points at any individual route's own code.

## Key Points to Retain

- The lifecycle's ordering is a practical decision tool for where new logic should live — the same check placed at a different lifecycle stage can have meaningfully different cost and correctness implications, as shown in the banned-IP example.
- Dependency resolution follows the dependency graph, not just source-code order — a dependency's own dependencies resolve first, which is what guarantees `401` always precedes a possible `403` in a `get_current_user` → `require_admin` chain, structurally rather than by convention.
- Exceptions raised anywhere in the dependency/route chain are converted into a response before middleware's "after" code runs, meaning middleware always sees a completed response object, never a raw exception — though it generally cannot distinguish an intentional error response from an unexpected crash.
- Lifespan events exist entirely outside the per-request lifecycle, running once for the application's whole life rather than once per request — a distinct timescale from anything else in this document.
- When debugging unexpected behavior, identifying which lifecycle stage a problem must be occurring at is a faster diagnostic starting point than guessing at specific mechanisms first.