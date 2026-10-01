# Custom Exception Handlers — Advanced Usage

Briefly, as groundwork: `@app.exception_handler(SomeExceptionType)` registers a function that intercepts a specific exception type whenever it's raised anywhere in the application, converting it into a consistently formatted response — rather than every route needing its own `try/except` for the same failure. This document goes past that basic mechanic into how exception handlers are structured for real applications with many distinct failure types, and how they interact with FastAPI's own built-in error handling.

## The Core Mechanism, Restated Precisely

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class InsufficientFundsError(Exception):
    def __init__(self, account_id: str, shortfall: float):
        self.account_id = account_id
        self.shortfall = shortfall

app = FastAPI()

@app.exception_handler(InsufficientFundsError)
async def handle_insufficient_funds(request: Request, exc: InsufficientFundsError):
    return JSONResponse(
        status_code=402,
        content={"detail": f"Account {exc.account_id} is short by {exc.shortfall}"},
    )
```

The handler function always receives exactly two arguments — the `Request` that triggered the exception, and the exception instance itself — regardless of where in the call stack (a route body, a dependency, a dependency-of-a-dependency) the exception was raised. FastAPI matches the *type* of whatever was raised against every registered handler, dispatching to the most specific match.

## Custom Exceptions as a Domain Vocabulary, Not Just Error Codes

The most valuable use of this mechanism in a real application isn't simply "a shortcut to avoid repeating `raise HTTPException(...)`" — it's building a set of exception classes that represent genuine *business concepts* specific to the application's domain, each carrying whatever structured data is relevant to that specific failure:

```python
class InsufficientFundsError(Exception):
    def __init__(self, account_id: str, shortfall: float):
        self.account_id = account_id
        self.shortfall = shortfall

class AccountFrozenError(Exception):
    def __init__(self, account_id: str, reason: str):
        self.account_id = account_id
        self.reason = reason

class DailyLimitExceededError(Exception):
    def __init__(self, limit: float, attempted: float):
        self.limit = limit
        self.attempted = attempted
```

Code deep inside the application — a service function several layers removed from any route — can raise `InsufficientFundsError(account_id, shortfall)` directly, without that function needing any awareness of HTTP at all (no status codes, no `JSONResponse`, no knowledge of how this will eventually be presented to a client). The translation from "this domain-specific thing went wrong" to "here's the HTTP response for that" happens in exactly one place — the registered handler — regardless of how many different functions, at how many different depths, might end up raising that same exception.

## One Handler Per Exception Type — Matching Behavior

FastAPI matches the *most specific* registered type for whatever was actually raised, respecting Python's normal exception inheritance:

```python
class PaymentError(Exception):
    """Base class for anything payment-related going wrong."""
    pass

class InsufficientFundsError(PaymentError):
    def __init__(self, account_id: str):
        self.account_id = account_id

class CardExpiredError(PaymentError):
    def __init__(self, card_last_four: str):
        self.card_last_four = card_last_four


@app.exception_handler(PaymentError)
async def handle_generic_payment_error(request: Request, exc: PaymentError):
    return JSONResponse(status_code=402, content={"detail": "Payment failed"})

@app.exception_handler(InsufficientFundsError)
async def handle_insufficient_funds(request: Request, exc: InsufficientFundsError):
    return JSONResponse(status_code=402, content={"detail": f"Account {exc.account_id} has insufficient funds"})
```

Here, raising `InsufficientFundsError` matches the more specific handler registered for exactly that type, not the broader `PaymentError` handler — even though `InsufficientFundsError` is also a `PaymentError` by inheritance. Raising `CardExpiredError`, which has no handler registered specifically for it, falls back to the broader `PaymentError` handler instead, since that's the closest matching registered ancestor type. This mirrors ordinary Python exception-catching behavior (`except MoreSpecific` before `except MoreGeneral`), applied to how FastAPI resolves which handler to invoke.

## Overriding FastAPI's Own Default Exception Handling

FastAPI has built-in default handling for a few cases — `RequestValidationError` (when Pydantic validation fails on a request body/query/path parameter) and `HTTPException` itself both have default handlers already registered by FastAPI before an application adds any of its own. These defaults can be overridden by registering a handler for the same type:

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def custom_validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Please check your input", "errors": exc.errors()},
    )
```

A real reason to do this: FastAPI's default validation error response includes a fairly verbose, technically-detailed `errors()` structure meant for developers — a public-facing API might want a simplified, more user-friendly error shape instead, without losing the underlying validation detail entirely (still accessible via `exc.errors()` inside the custom handler, just reshaped before being sent to the client).

## Handlers and the Lifecycle — Where They Actually Sit

As established in the Request/Response Lifecycle document, an exception handler intercepts its matching exception type regardless of which layer raised it, and produces a complete response *before* that response reaches any middleware's "after" section. This means middleware and exception handlers compose cleanly — a timing middleware wrapping the whole application correctly logs a duration and status code even for a request that failed deep inside a dependency via a custom exception, without any awareness of that exception type needing to exist in the middleware itself.

## A Common Mistake — Catching Too Broadly

```python
@app.exception_handler(Exception)
async def catch_everything(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Something went wrong"})
```

Registering a handler for the bare `Exception` class catches *every* exception in the entire application, including genuine bugs that should probably crash loudly during development (an `AttributeError` from a typo, a `KeyError` from missing dictionary access) rather than being silently converted into a generic `500` response. This can make debugging significantly harder, since the real underlying error gets hidden behind a generic message instead of surfacing clearly. A narrower, deliberate set of specific exception types — each representing a genuine, anticipated domain failure — is generally a better pattern than one broad catch-all, reserving truly unexpected crashes to surface through FastAPI's own default (unhandled) behavior, which typically still logs the full traceback server-side even while returning a generic response to the client.

## Key Points to Retain

- A handler is matched by exception type, following normal Python inheritance rules — the most specific registered type wins, falling back to a broader registered ancestor type if no exact match exists.
- Custom exceptions work best as a genuine domain vocabulary — code deep in the application can raise them with zero awareness of HTTP, leaving the HTTP translation entirely to the registered handler.
- FastAPI's own default handlers (for `RequestValidationError`, `HTTPException`) can be overridden by registering a handler for the same type, useful for reshaping error responses for a specific audience.
- Exception handlers compose cleanly with middleware, since middleware always receives a fully-formed response regardless of which layer an exception was raised at or which handler processed it.
- Registering an overly broad handler (for the bare `Exception` class) risks silently swallowing genuine bugs that would otherwise surface clearly — prefer specific, deliberate exception types over one catch-all.