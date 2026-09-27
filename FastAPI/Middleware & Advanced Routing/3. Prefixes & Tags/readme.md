# Route Prefixes and Tags — Advanced Usage

Briefly, as groundwork: `prefix` automatically prepends a path segment to every route on a router (`prefix="/auth"` turns `/register` into `/auth/register`), and `tags` groups routes together under a heading in the Swagger docs UI. This document skips further basics and goes directly into the patterns that matter once an application has more than a couple of routers.

## Prefix Composition — Nesting Prefixed Routers Inside Prefixed Routers

A router that already has its own `prefix` can itself be included into another router that also has a `prefix` — the two compose, rather than one overriding the other:

```python
# routers/admin/users.py
admin_users_router = APIRouter(prefix="/users")

@admin_users_router.get("/")
def list_admin_users():
    ...
```

```python
# routers/admin/__init__.py
admin_router = APIRouter(prefix="/admin")
admin_router.include_router(admin_users_router)
```

```python
# main.py
app.include_router(admin_router)
```

The final resolved path is `/admin/users/` — each layer's prefix stacks onto the next. This matters once an application groups related routers under a shared umbrella (all admin-related routers under `/admin`, all v1 routers under `/v1`), rather than every router being included directly on `app` with a single flat prefix each.

## Tags as an API Contract Signal, Not Just Docs Grouping

Tags are often introduced as "just for Swagger's grouping," but in a real API consumed by external developers, tags become part of the practical contract — API documentation generators, client SDK generators (e.g. `openapi-generator`, which many companies use to auto-generate client libraries from an OpenAPI schema), and internal API catalogs frequently group and name things based on tags. A tag isn't purely cosmetic once external tooling depends on the generated OpenAPI schema.

```python
router = APIRouter(prefix="/auth", tags=["Authentication"])
```

A route can also carry multiple tags, causing it to appear under more than one grouping simultaneously — useful when a route genuinely serves two purposes from a consumer's perspective:

```python
@router.post("/register", tags=["Authentication", "Onboarding"])
def register():
    ...
```

## Router-Level `tags` vs Per-Route `tags` — Overriding Behavior

Tags set at the router level apply to every route in that router by default, but an individual route can still specify its own `tags`, which **adds to** (not replaces) the router-level tags rather than overriding them entirely — a route ends up carrying the union of both.

## Dynamic Prefixes Based on Environment or Configuration

A prefix doesn't have to be a hardcoded string — it can be built from configuration, which becomes useful for supporting multiple API versions or environment-specific routing without duplicating route logic:

```python
from core.config import settings

router = APIRouter(prefix=f"/api/{settings.api_version}")
```

This allows the same router code to serve under `/api/v1` in one deployment and `/api/v2` in another, purely by changing a config value — though for genuinely different behavior between versions (not just a different path), separate router files per version (as covered in `api_versioning.py`) remains the correct approach; a dynamic prefix alone doesn't change what a route *does*, only where it's reachable.

## Tags for Internal API Organization Beyond Swagger

In a larger application, tags are sometimes used as a lightweight internal categorization system independent of Swagger's visual grouping — for example, a custom script that audits "every route tagged `Admin` must also have the `require_admin` dependency attached" can programmatically inspect the app's routes and their tags to catch a security oversight before it ships, rather than relying on a developer to remember it manually.

## Key Points to Retain

- Prefixes compose when routers are nested inside other routers — each layer's prefix stacks onto the next, rather than the innermost or outermost one alone taking effect.
- Tags carry real, non-cosmetic weight once external tooling (client SDK generators, API catalogs) consumes the generated OpenAPI schema.
- Router-level and route-level tags combine (union), they don't override one another.
- A prefix can be built dynamically from configuration for path-level environment/version differences, though genuinely different route *behavior* between versions still requires separate router code, not just a different prefix string.

---