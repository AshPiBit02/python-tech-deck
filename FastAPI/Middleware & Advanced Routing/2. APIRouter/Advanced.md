# FastAPI `APIRouter` — Advanced Guide

This guide assumes you already know the basics of `APIRouter` (creating a router, adding path operations, and including it with `app.include_router()`). It focuses on the advanced patterns used in real, production-sized FastAPI projects.

---

## 1. Router-Level Configuration

When you create or include an `APIRouter`, you can set defaults that apply to **every route** inside it.

```python
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)
```

| Parameter | Purpose |
|---|---|
| `prefix` | Prepended to every path in the router. Must **not** end with `/`. |
| `tags` | Groups endpoints in the OpenAPI docs (Swagger UI sidebar). |
| `dependencies` | Run for *every* route in the router, even if the route doesn't use the result. |
| `responses` | Extra documented response codes merged into every route's OpenAPI schema. |
| `default_response_class` | Overrides the default `Response` class for all routes. |
| `deprecated` | Marks all routes in the router as deprecated in the docs. |
| `include_in_schema` | If `False`, hides every route in this router from the generated OpenAPI schema. |
| `route_class` | Custom `APIRoute` subclass used for every route (see §6). |
| `generate_unique_id_function` | Custom function to generate `operationId` for OpenAPI. |

You can set these **either** when creating the `APIRouter(...)`, **or** when calling `app.include_router(router, ...)` — the two are merged, with `include_router()` arguments effectively stacking on top.

```python
app.include_router(
    router,
    prefix="/v1",          # stacks with router's own prefix, if any
    tags=["v1"],           # merged with router's own tags
    dependencies=[Depends(check_rate_limit)],
)
```

⚠️ **Important gotcha:** dependencies passed at `include_router()` are *appended* to the router's own dependencies — they don't replace them. Both run.

---

## 2. Nested / Composed Routers

Large APIs are usually built from many small routers combined into bigger ones, then finally into the app. This is the standard way to structure a FastAPI project.

```python
# routers/items.py
router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
def list_items(): ...
```

```python
# routers/users.py
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users(): ...
```

```python
# routers/api_v1.py
from fastapi import APIRouter
from .items import router as items_router
from .users import router as users_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(items_router)
api_router.include_router(users_router)
```

```python
# main.py
from fastapi import FastAPI
from .routers.api_v1 import api_router

app = FastAPI()
app.include_router(api_router)
```

Result: `/v1/items/`, `/v1/users/` — prefixes accumulate as you climb the tree, and tags/dependencies accumulate too. This is how you build clean **API versioning** (`/v1`, `/v2` routers mounted side by side) and **domain-based module separation**.

---

## 3. Router-Level Dependencies (Auth, Permissions, etc.)

Dependencies declared on the router run before *every* endpoint in it — ideal for authentication/authorization boundaries.

```python
def verify_admin(token: str = Depends(oauth2_scheme)):
    if not is_admin(token):
        raise HTTPException(status_code=403, detail="Admins only")

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
)

@admin_router.get("/stats")
def get_stats():
    # verify_admin already ran, no need to redeclare it
    ...
```

You can layer this: a project-wide `verify_token` dependency on the top-level router, plus a stricter `verify_admin` dependency on a nested admin sub-router — both execute, top-down.

---

## 4. Per-Route Overrides

Router defaults are just that — defaults. Individual routes can override or extend them.

```python
@router.get(
    "/{item_id}",
    tags=["items", "special"],          # extends router tags
    responses={200: {"content": {"image/png": {}}}},
    deprecated=True,
    include_in_schema=False,            # hide just this one route
    response_model=ItemOut,
    response_model_exclude_unset=True,
    status_code=201,
)
def read_item(item_id: int):
    ...
```

Common per-route overrides:
- `response_model`, `response_model_exclude`, `response_model_by_alias`
- `status_code`
- `summary`, `description`, `response_description`
- `operation_id` (explicit OpenAPI operation id)
- `deprecated`
- `include_in_schema`

---

## 5. Path Convention: Trailing Slashes & Redirects

FastAPI (via Starlette) will issue a 307 redirect between `/items` and `/items/` depending on how the route was declared and `redirect_slashes` on the `FastAPI`/router config. In larger APIs, pick **one convention** (usually no trailing slash) and apply it consistently across all routers to avoid confusing 307 redirects in clients, especially with `POST`/`PUT` where redirects can drop the body in some HTTP clients.

```python
app = FastAPI(redirect_slashes=False)
```

---

## 6. Custom `APIRoute` Classes

You can subclass `APIRoute` to customize behavior for *every* route in a router — e.g., custom logging, timing, exception normalization, or request-body validation tweaks.

```python
import time
from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute
from typing import Callable

class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            start = time.time()
            response = await original_handler(request)
            duration = time.time() - start
            response.headers["X-Response-Time"] = str(duration)
            return response

        return custom_handler

router = APIRouter(route_class=TimedRoute)
```

Use cases:
- Adding response timing / tracing headers
- Wrapping unhandled exceptions into a consistent JSON error schema
- Injecting request-scoped context (e.g., request ID) before validation
- Custom body-parsing logic shared across a whole router

---

## 7. `callbacks` and `openapi_extra`

For webhook-style APIs, you can document callback endpoints that *your* API will call on the client.

```python
callback_router = APIRouter()

@callback_router.post("{$callback_url}/invoices/{$request.body.id}", name="invoice_notification")
def invoice_notification(body: InvoiceEvent):
    ...

@router.post("/invoices/", callbacks=callback_router.routes)
def create_invoice(invoice: Invoice):
    ...
```

`openapi_extra` lets you inject arbitrary raw OpenAPI fields into a route's schema (e.g., custom `x-` extensions, alternative request bodies) that FastAPI's normal parameters don't expose:

```python
@router.post("/items/", openapi_extra={"x-internal-only": True})
def create_item(item: Item):
    ...
```

---

## 8. `generate_unique_id_function`

By default, FastAPI generates OpenAPI `operationId`s from function name + route. In large projects with many routers, name collisions or ugly auto-generated client SDK method names are common. You can control this per router:

```python
def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)
```

This matters a lot when you generate a TypeScript/Python client SDK from the OpenAPI schema — clean `operationId`s become clean method names.

---

## 9. Conditional / Dynamic Route Registration

Since `APIRouter` objects are just Python objects until included, you can build routers conditionally — e.g., feature flags, environment-based routes, or plugin systems.

```python
router = APIRouter(prefix="/feature-x")

if settings.FEATURE_X_ENABLED:
    @router.get("/")
    def feature_x_endpoint():
        ...

app.include_router(router)
```

Or dynamically attach routers from a plugin registry:

```python
for plugin in discovered_plugins:
    app.include_router(plugin.router, prefix=f"/plugins/{plugin.name}")
```

---

## 10. Testing Routers in Isolation

Because a router is independent of the app, you can mount it on a throwaway `FastAPI()` instance for focused unit tests without booting your whole app (DB connections, middleware, etc.):

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from myapp.routers.items import router

test_app = FastAPI()
test_app.include_router(router)
client = TestClient(test_app)

def test_list_items():
    response = client.get("/items/")
    assert response.status_code == 200
```

Combine with `app.dependency_overrides` to swap real dependencies (DB sessions, auth) for fakes/mocks at test time:

```python
test_app.dependency_overrides[get_db] = lambda: fake_db_session
```

---

## 11. Mixing `APIRouter` with Sub-Applications

`APIRouter` composes routes *within* one ASGI app and shares its OpenAPI schema. If you instead need **fully isolated** apps (separate docs, separate middleware stack, separate OpenAPI schema) mounted at a path, use `app.mount()` with a second `FastAPI()` instance instead of `include_router()`:

```python
sub_app = FastAPI(title="Internal API")
sub_app.include_router(internal_router)

app.mount("/internal", sub_app)
```

Rule of thumb:
- **Same app, shared docs/middleware, just organizing code** → `APIRouter` + `include_router()`
- **Truly separate app (different auth stack, different docs page, different lifespan)** → `mount()` a second `FastAPI()`

---

## 12. Class-Based Endpoint Grouping (CBV-style)

FastAPI doesn't ship class-based views natively, but a common advanced pattern groups related endpoints as methods on a class, registered onto a router in `__init__`, giving you shared state/dependencies without external libraries:

```python
class ItemsAPI:
    def __init__(self, router: APIRouter):
        router.add_api_route("/", self.list_items, methods=["GET"])
        router.add_api_route("/{item_id}", self.get_item, methods=["GET"])

    def list_items(self):
        ...

    def get_item(self, item_id: int):
        ...

router = APIRouter(prefix="/items", tags=["items"])
ItemsAPI(router)
```

Note `add_api_route()` is the imperative equivalent of the `@router.get(...)` decorator — useful for building routes programmatically.

---

## 13. Route Ordering & Path Conflicts

Routes are matched in the order they're registered — **first match wins**. This becomes a real bug source once routers are nested and combined.

```python
# WRONG ORDER — "/items/latest" will never be reached,
# because "/items/{item_id}" matches first.
@router.get("/{item_id}")
def get_item(item_id: str): ...

@router.get("/latest")
def get_latest_item(): ...
```

```python
# CORRECT — put static/specific paths before dynamic ones
@router.get("/latest")
def get_latest_item(): ...

@router.get("/{item_id}")
def get_item(item_id: str): ...
```

When combining many routers via `include_router()`, keep this ordering rule in mind across router boundaries too — the router included first has its matching routes tried first.

---

## 14. Quick Reference: `include_router()` Signature

```python
app.include_router(
    router: APIRouter,
    *,
    prefix: str = "",
    tags: list[str] | None = None,
    dependencies: Sequence[Depends] | None = None,
    responses: dict | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    default_response_class: type[Response] = Default(JSONResponse),
    callbacks: list[BaseRoute] | None = None,
    generate_unique_id_function: Callable[[APIRoute], str] = Default(generate_unique_id),
)
```

---

## 15. Common Pitfalls Checklist

- ❌ Forgetting `prefix` can't end with a trailing `/` (raises an assertion error).
- ❌ Declaring dependencies both on the router *and* redundantly on every route (they'll run twice if you also add them as `Depends()` in the function signature params intentionally — usually unintended).
- ❌ Dynamic paths declared before static ones, shadowing them.
- ❌ Mixing `include_router()` for logically separate services instead of `mount()`, leading to one giant shared OpenAPI schema.
- ❌ Relying on default `operationId` generation in large multi-router apps — collisions produce awkward generated client method names.
- ❌ Not setting `redirect_slashes` consistently, causing surprise 307s on `POST` from strict HTTP clients.