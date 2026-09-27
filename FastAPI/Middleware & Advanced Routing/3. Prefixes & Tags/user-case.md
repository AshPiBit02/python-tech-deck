# Real-World Case Samples

## Case 1 — Prefix Composition for a Growing Admin Section

**Problem:** An application starts with a flat `/admin/users` route. Over time, more admin functionality is needed — `/admin/reports`, `/admin/settings`, `/admin/audit-logs` — each with its own file for maintainability. Without a shared structure, every new admin router needs to remember to manually prefix every single route with `/admin/...`, and it's easy for one router to forget the prefix and accidentally expose a route at the wrong path.

**Solution:**
```python
# routers/admin/__init__.py
from fastapi import APIRouter
from routers.admin import users, reports, settings

admin_router = APIRouter(prefix="/admin", tags=["Admin"])
admin_router.include_router(users.router)       # prefix="/users" on this router
admin_router.include_router(reports.router)     # prefix="/reports" on this router
admin_router.include_router(settings.router)    # prefix="/settings" on this router
```
```python
# main.py
app.include_router(admin_router)
```
Every admin sub-router only needs to know its own small piece (`/users`, `/reports`, `/settings`) — the shared `/admin` prefix and `Admin` tag are declared exactly once, at the umbrella level, and automatically apply to everything nested inside. Adding a fourth admin area later means writing one new small router file and one `include_router` line — no risk of forgetting the `/admin` prefix, since it isn't repeated anywhere.

## Case 2 — Tags Driving Auto-Generated Client SDKs

**Problem:** A company's mobile team consumes the backend API by running an OpenAPI-schema-based code generator to produce a typed API client automatically, rather than hand-writing HTTP calls. The generator organizes the generated client code into classes/modules based on tags (e.g. an `AuthenticationClient` class, a `UsersClient` class). If routes are left untagged, or tagged inconsistently, the generated client ends up with poorly organized or duplicated method groupings, which the mobile team then has to work around manually.

**Solution:**
```python
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])
```
By tagging consistently and deliberately at the router level, the generated OpenAPI schema cleanly separates routes into exactly the groupings the client generator will turn into distinct, well-named classes — `client.authentication.login()`, `client.users.get_profile()`, `client.admin.list_users()`. The tag choice here isn't a documentation nicety; it directly shapes what the consuming team's generated code looks like.

## Case 3 — Auditing Tags to Catch a Security Gap Programmatically

**Problem:** A team has a policy: every route considered "admin-only" must have the `require_admin` dependency attached. As the codebase grows across many router files, it becomes realistic that a new admin route gets added by a developer who forgets to attach the dependency — a genuine, easy-to-miss security bug, since the route would otherwise work and look correct in casual testing (if the developer testing it happens to already be an admin).

**Solution:**
```python
def audit_admin_routes(app):
    problems = []
    for route in app.routes:
        tags = getattr(route, "tags", [])
        dependencies = getattr(route, "dependencies", [])
        if "Admin" in tags:
            dependency_names = [str(dep.dependency) for dep in dependencies]
            if not any("require_admin" in name for name in dependency_names):
                problems.append(route.path)
    return problems
```
Run as part of a CI check or a startup-time assertion, this script inspects the actual registered routes and their tags, flagging any route tagged `Admin` that doesn't also carry the expected dependency — turning a manual "please remember to do this" policy into an automatically enforced one. This is only possible because tags are inspectable metadata on the route object itself, not merely a string used for Swagger's visual display.