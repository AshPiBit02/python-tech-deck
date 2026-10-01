# Custom Exception Handlers in FastAPI

> **Phase:** Middleware & Advanced Routing
> **Topic:** Custom (centralized) exception handling
> **Stack:** Python 3.10+, FastAPI, Starlette, Pydantic v2

---

## Table of Contents

1. [What & Why](#1-what--why)
2. [How FastAPI Handles Errors by Default](#2-how-fastapi-handles-errors-by-default)
3. [Where Exception Handlers Sit in the Stack](#3-where-exception-handlers-sit-in-the-stack)
4. [Project Structure](#4-project-structure)
5. [Step 1: Define a Standard Error Schema](#5-step-1-define-a-standard-error-schema)
6. [Step 2: Create Custom Exception Classes](#6-step-2-create-custom-exception-classes)
7. [Step 3: Write the Handlers](#7-step-3-write-the-handlers)
8. [Step 4: Register Handlers](#8-step-4-register-handlers)
9. [Step 5: Raise Exceptions in Routes](#9-step-5-raise-exceptions-in-routes)
10. [Overriding Built-in Handlers](#10-overriding-built-in-handlers)
11. [Catch-All Handler (500)](#11-catch-all-handler-500)
12. [Request ID Middleware](#12-request-id-middleware)
13. [Testing](#13-testing)
14. [Common Pitfalls](#14-common-pitfalls)
15. [Best Practices](#15-best-practices)
16. [Practice Exercises](#16-practice-exercises)
17. [Quick Reference](#17-quick-reference)

---

## 1. What & Why

A **custom exception handler** is a function that intercepts a specific exception type raised anywhere in your app and converts it into a well-formed HTTP response.

**Without it:**
- Error responses are inconsistent (`{"detail": "..."}` here, a stack trace there).
- Business errors leak into route code as repeated `try/except` blocks.
- Clients can't reliably parse errors.

**With it:**
- One consistent error format across the whole API.
- Route code stays clean: just `raise NotFoundError(...)`.
- Logging, monitoring, and error mapping live in one place.

---

## 2. How FastAPI Handles Errors by Default

| Situation | Exception | Default status | Default body |
|---|---|---|---|
| `raise HTTPException(404, "x")` | `HTTPException` | as given | `{"detail": "x"}` |
| Invalid request body/query/path | `RequestValidationError` | 422 | `{"detail": [ {loc, msg, type, ...} ]}` |
| Unknown route / wrong method | Starlette `HTTPException` | 404 / 405 | `{"detail": "Not Found"}` |
| Any other uncaught exception | `Exception` | 500 | Plain text `Internal Server Error` |

Goal: make all of these return **the same shape**.

---

## 3. Where Exception Handlers Sit in the Stack

```
Request
  │
  ▼
ServerErrorMiddleware        ← handles `Exception` / 500 handler (outermost)
  │
  ▼
Your middleware (CORS, @app.middleware("http"), ...)
  │
  ▼
ExceptionMiddleware          ← handles HTTPException + your custom handlers
  │
  ▼
Router → Route → Dependencies → Endpoint
```

Consequences you must know:

- Exceptions raised **inside your middleware** are **not** caught by your custom `AppException` handlers. Return a `JSONResponse` directly from middleware instead.
- The generic `Exception` (500) handler runs in the **outermost** layer, so its response **bypasses your middleware**. That means no CORS headers and no custom response headers (e.g. `X-Request-ID`) on 500s unless you add them manually.
- Handlers are matched by **class hierarchy (MRO)**: a handler for a parent class catches subclasses unless a more specific handler is registered.

---

## 4. Project Structure

```
app/
├── main.py
├── core/
│   ├── exceptions.py      # custom exception classes
│   └── handlers.py        # handler functions + register function
├── schemas/
│   └── error.py           # error response models
├── routers/
│   └── items.py
└── tests/
    └── test_exceptions.py
```

---

## 5. Step 1: Define a Standard Error Schema

`app/schemas/error.py`

```python
from typing import Any
from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str                       # machine-readable, e.g. "item_not_found"
    message: str                    # human-readable
    details: Any | None = None      # validation errors, extra context
    request_id: str | None = None   # for log correlation


class ErrorResponse(BaseModel):
    error: ErrorBody
```

Every error will look like:

```json
{
  "error": {
    "code": "item_not_found",
    "message": "Item 42 not found",
    "details": null,
    "request_id": "9f1c6a52-..."
  }
}
```

---

## 6. Step 2: Create Custom Exception Classes

`app/core/exceptions.py`

```python
from typing import Any


class AppException(Exception):
    """Base class for all expected (business/domain) errors."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "Something went wrong"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        self.headers = headers
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"
    message = "Resource not found"


class ConflictError(AppException):
    status_code = 409
    code = "conflict"
    message = "Resource already exists"


class UnauthorizedError(AppException):
    status_code = 401
    code = "unauthorized"
    message = "Authentication required"

    def __init__(self, message: str | None = None, **kwargs):
        kwargs.setdefault("headers", {"WWW-Authenticate": "Bearer"})
        super().__init__(message, **kwargs)


class ForbiddenError(AppException):
    status_code = 403
    code = "forbidden"
    message = "You do not have permission to perform this action"


class BusinessRuleError(AppException):
    status_code = 400
    code = "business_rule_violation"
    message = "Operation not allowed"
```

**Design rule:** one base class (`AppException`) so a single handler covers all domain errors.

---

## 7. Step 3: Write the Handlers

`app/core/handlers.py`

```python
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def _build_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


# ---- 1. Your domain exceptions -------------------------------------------
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "AppException %s on %s %s: %s",
        exc.code, request.method, request.url.path, exc.message,
    )
    return _build_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


# ---- 2. Built-in HTTPException (including 404/405 from routing) ----------
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return _build_response(
        request,
        status_code=exc.status_code,
        code=f"http_{exc.status_code}",
        message=str(exc.detail),
        headers=getattr(exc, "headers", None),
    )


# ---- 3. Pydantic / request validation (422) ------------------------------
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # jsonable_encoder is REQUIRED: exc.errors() can contain non-serializable
    # objects (e.g. a ValueError instance inside "ctx").
    details = [
        {
            "field": ".".join(str(p) for p in err["loc"] if p != "body"),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in jsonable_encoder(exc.errors())
    ]
    return _build_response(
        request,
        status_code=422,
        code="validation_error",
        message="Request validation failed",
        details=details,
    )


# ---- 4. Catch-all (unexpected bugs) --------------------------------------
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception on %s %s",
        request.method, request.url.path,
        exc_info=exc,
    )
    # Never expose str(exc) or tracebacks to clients.
    return _build_response(
        request,
        status_code=500,
        code="internal_server_error",
        message="An unexpected error occurred",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
```

> **Why `StarletteHTTPException` and not `fastapi.HTTPException`?**
> FastAPI's `HTTPException` subclasses Starlette's. Router-level errors (404 for unknown paths, 405) raise the **Starlette** one. Registering on the parent catches both.

---

## 8. Step 4: Register Handlers

`app/main.py`

```python
from fastapi import FastAPI

from app.core.handlers import register_exception_handlers
from app.routers import items

app = FastAPI(title="Exception Handling Demo")

register_exception_handlers(app)
app.include_router(items.router)
```

Alternative decorator style (fine for small apps):

```python
@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException):
    ...
```

---

## 9. Step 5: Raise Exceptions in Routes

`app/routers/items.py`

```python
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.exceptions import ConflictError, NotFoundError, BusinessRuleError
from app.schemas.error import ErrorResponse

router = APIRouter(prefix="/items", tags=["items"])

FAKE_DB: dict[int, dict] = {1: {"id": 1, "name": "Keyboard", "stock": 5}}


class ItemCreate(BaseModel):
    name: str = Field(min_length=2)
    stock: int = Field(ge=0)


@router.get(
    "/{item_id}",
    responses={404: {"model": ErrorResponse}},   # documents the error in OpenAPI
)
async def get_item(item_id: int):
    item = FAKE_DB.get(item_id)
    if item is None:
        raise NotFoundError(f"Item {item_id} not found", code="item_not_found")
    return item


@router.post("/", status_code=201, responses={409: {"model": ErrorResponse}})
async def create_item(payload: ItemCreate):
    if any(i["name"] == payload.name for i in FAKE_DB.values()):
        raise ConflictError("Item with this name already exists", code="item_duplicate")
    new_id = max(FAKE_DB, default=0) + 1
    FAKE_DB[new_id] = {"id": new_id, **payload.model_dump()}
    return FAKE_DB[new_id]


@router.post("/{item_id}/purchase")
async def purchase(item_id: int, qty: int = 1):
    item = FAKE_DB.get(item_id)
    if item is None:
        raise NotFoundError(f"Item {item_id} not found", code="item_not_found")
    if item["stock"] < qty:
        raise BusinessRuleError(
            "Insufficient stock",
            code="insufficient_stock",
            details={"available": item["stock"], "requested": qty},
        )
    item["stock"] -= qty
    return item
```

Test it:

```bash
uvicorn app.main:app --reload

curl -i localhost:8000/items/999        # 404, custom shape
curl -i localhost:8000/nope             # 404 from router, same shape
curl -i -X POST localhost:8000/items/ \
     -H "Content-Type: application/json" -d '{"name":"x","stock":-1}'   # 422
```

---

## 10. Overriding Built-in Handlers

You already did in Section 7 (`RequestValidationError`, `StarletteHTTPException`). 

### Reusing the default behavior

If you only want to *add* logging and keep the default response:

```python
from fastapi.exception_handlers import (
    http_exception_handler as default_http_handler,
    request_validation_exception_handler as default_validation_handler,
)

async def logged_http_handler(request, exc):
    logger.warning("HTTP %s: %s", exc.status_code, exc.detail)
    return await default_http_handler(request, exc)
```

### Other related exceptions

| Exception | When | Status |
|---|---|---|
| `RequestValidationError` | Incoming request invalid | 422 |
| `ResponseValidationError` | Your endpoint returned data violating `response_model` (a server bug) | 500 |
| `WebSocketRequestValidationError` | Invalid WebSocket params | n/a |

---

## 11. Catch-All Handler (500)

```python
app.add_exception_handler(Exception, unhandled_exception_handler)
```

Important behaviors:

- Starlette runs this in `ServerErrorMiddleware`, **sends your response, then re-raises** the exception so the server (uvicorn) can log it as well. You'll see the traceback in the console even though the client got a clean JSON.
- Response **bypasses your middleware** → no CORS headers. Browsers will report a CORS error instead of your JSON on 500s. Fix by adding CORS headers manually in this handler, or handle by placing a reverse proxy in front.
- Never return `str(exc)` or traceback to the client in production.

---

## 12. Request ID Middleware

Adds a correlation ID so a client-reported error can be matched to server logs.

```python
import uuid
from fastapi import Request

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response
```

Notes:
- Works for normal and handled errors (`AppException`, 422, etc.).
- For unhandled 500s the header is **not** added by this middleware (see Section 3), but the `request_id` in the JSON body still is, because `request.state` was set before the failure.
- `@app.middleware("http")` uses `BaseHTTPMiddleware`; for high-throughput apps prefer a pure ASGI middleware.

---

## 13. Testing

`app/tests/test_exceptions.py`

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app

# raise_server_exceptions=False lets you assert on the 500 response
# instead of the TestClient re-raising the exception.
client = TestClient(app, raise_server_exceptions=False)


def test_not_found_custom_error():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()["error"]
    assert body["code"] == "item_not_found"
    assert "999" in body["message"]


def test_unknown_route_uses_same_shape():
    r = client.get("/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "http_404"


def test_validation_error_shape():
    r = client.post("/items/", json={"name": "x", "stock": -1})
    assert r.status_code == 422
    body = r.json()["error"]
    assert body["code"] == "validation_error"
    assert {d["field"] for d in body["details"]} == {"name", "stock"}


def test_unhandled_exception_returns_generic_500():
    @app.get("/boom")
    async def boom():
        raise RuntimeError("secret internal detail")

    r = client.get("/boom")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_server_error"
    assert "secret" not in r.text
```

Run: `pytest -v`

---

## 14. Common Pitfalls

| Pitfall | Why it happens | Fix |
|---|---|---|
| Custom handler never fires for 404 on unknown routes | Registered on `fastapi.HTTPException` | Register on `starlette.exceptions.HTTPException` |
| `TypeError: Object of type ValueError is not JSON serializable` in 422 handler | `exc.errors()` contains raw exception objects in `ctx` | Wrap with `jsonable_encoder(exc.errors())` |
| Exception raised in middleware isn't handled | Middleware wraps `ExceptionMiddleware` | Return a `JSONResponse` directly in middleware |
| 500 response missing CORS headers | `ServerErrorMiddleware` is outermost | Add headers in the 500 handler or use a proxy |
| Tests crash instead of returning 500 | `TestClient` re-raises by default | `TestClient(app, raise_server_exceptions=False)` |
| Handler per `APIRouter` doesn't work | `APIRouter` has no `exception_handler` | Register on `app` (or on a sub-application via `app.mount`) |
| Errors in `BackgroundTasks` not handled | Response already sent | Log/handle inside the task itself |
| Handler returns a dict | Handlers must return a `Response` | Return `JSONResponse(...)` |
| `HTTPException` swallowed `headers` | Forgot to forward them | Pass `headers=exc.headers` in the handler |
| `except Exception` in route hides errors | Catches your `AppException` too | Don't blanket-catch; let it bubble |

---

## 15. Best Practices

1. **One base exception** (`AppException`) for expected errors; everything else is a bug (500).
2. **Stable machine-readable `code`** values; clients switch on `code`, not on `message`.
3. **Log levels:** 4xx → `warning`/`info`; 5xx → `error` with traceback.
4. **Never leak internals** (SQL errors, stack traces, file paths) in responses.
5. **Document errors in OpenAPI** with `responses={404: {"model": ErrorResponse}}`.
6. **Keep domain layer framework-free**: services raise `AppException`, not `HTTPException`; the handler maps to HTTP.
7. **Include a request ID** for traceability.
8. **Use correct status codes:** 401 (not authenticated) vs 403 (not allowed), 409 (conflict), 422 (validation).
9. **Test every handler**, including the 500 path.
10. **Convert third-party/DB exceptions** (e.g., `IntegrityError` → `ConflictError`) at the boundary, or register handlers for them.

---

## 16. Practice Exercises

1. **Basic:** Add `RateLimitError` (429) with a `Retry-After` header, and raise it from a route.
2. **Mapping:** Register a handler for SQLAlchemy `IntegrityError` that returns 409.
3. **Validation formatting:** Change the 422 response to `{"errors": {"field": ["msg", ...]}}` grouping by field.
4. **Environment-aware:** In `DEBUG=true`, include the exception type and message in the 500 response; never in production.
5. **Middleware error:** Write an API-key middleware that rejects requests with a 401 using the same error shape (remember: return a response, don't raise).
6. **Sub-app:** Mount a `/admin` sub-application with its own handlers different from the main app.
7. **Observability:** Send unhandled exceptions to Sentry (or a mock) from the 500 handler.

---

## 17. Quick Reference

```python
# Register
app.add_exception_handler(MyError, handler)         # or @app.exception_handler(MyError)

# Handler signature
async def handler(request: Request, exc: MyError) -> Response: ...

# Key imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
```

| Want to... | Do this |
|---|---|
| Handle all domain errors | Handler on base `AppException` |
| Handle 404 for unknown routes | Handler on `StarletteHTTPException` |
| Reshape 422 | Handler on `RequestValidationError` |
| Catch bugs | Handler on `Exception` |
| Reject inside middleware | `return JSONResponse(...)` |
| Test 500 | `TestClient(..., raise_server_exceptions=False)` |

---

## Further Reading

- FastAPI docs: *Handling Errors* (https://fastapi.tiangolo.com/tutorial/handling-errors/)
- Starlette docs: *Exceptions* (https://www.starlette.io/exceptions/)
- RFC 9457: *Problem Details for HTTP APIs* (a standard alternative error format worth considering)