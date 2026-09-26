# `APIRouter` Basics

As a FastAPI application grows, keeping every route in a single `main.py` file becomes unmanageable — this was already addressed in practice while building the auth system, where routes were split into `routers/auth.py` and `routers/users.py`. This document explains, from first principles, what `APIRouter` actually is, how it works, and why it's structured the way it is.

## The Problem Without `APIRouter`

Without any splitting mechanism, every single route in an application has to be defined directly on the one `FastAPI()` instance:

```python
# main.py — everything in one file
from fastapi import FastAPI
app = FastAPI()

@app.post("/register")
def register(): ...

@app.post("/token")
def login(): ...

@app.get("/me")
def get_me(): ...

@app.get("/admin/users")
def list_users(): ...

# ...and every other route the application will ever have, all in this one file
```

For a handful of routes this is fine. For a real application — the auth system alone already has eight or more routes — this file becomes long, and unrelated concerns (authentication routes, user-profile routes, admin routes) all sit mixed together with no structural separation.

## What `APIRouter` Actually Is

`APIRouter` is a class that behaves almost identically to the `FastAPI` application object itself, but represents a smaller, standalone collection of routes rather than the whole application. It supports the same decorators (`@router.get(...)`, `@router.post(...)`, `@router.put(...)`, `@router.delete(...)`, `@router.patch(...)`) that `@app.get(...)` and friends provide — the only difference is which object those decorators are attached to.

```python
# routers/auth.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
def register():
    return {"message": "registered"}

@router.post("/token")
def login():
    return {"access_token": "..."}
```

At this point, `router` is a self-contained bundle of routes that exists independently — it is not yet part of any running application. Nothing happens if this file is imported on its own; the routes defined on `router` are inert until they're explicitly connected to a real `FastAPI` app.

## Connecting a Router to the Application — `include_router`

```python
# main.py
from fastapi import FastAPI
from routers import auth

app = FastAPI()
app.include_router(auth.router)
```

`app.include_router(auth.router)` takes every route defined on `auth.router` and effectively merges them into the main application, as if they had been defined directly on `app` all along. After this line runs, `POST /register` and `POST /token` work exactly as if they'd been written straight into `main.py` — clients calling them have no way to tell the difference; the split exists purely for organizing the source code, not for changing runtime behavior.

## Multiple Routers, Combined in One Application

This is exactly the pattern already used for the auth system:

```python
# main.py
from fastapi import FastAPI
from routers import auth, users

app = FastAPI()
app.include_router(auth.router)
app.include_router(users.router)
```

Each router file stays focused on one area of responsibility — `auth.py` for registration/login/tokens, `users.py` for profile and admin routes — while `main.py` itself stays short, doing nothing but assembling the pieces together. This is the concrete payoff of the split: `main.py` becomes a high-level table of contents for the application, rather than a place where actual route logic lives.

## A Router File Needs Its Own Imports

A common early mistake is forgetting that each router file is its own Python module, and needs to import everything it uses directly — a router file cannot silently borrow imports from `main.py` or from another router file just because they'll eventually be combined:

```python
# routers/users.py — this file needs its OWN imports for everything it uses
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from dependencies.auth import get_current_user

router = APIRouter()

@router.get("/me")
def get_me(current_user = Depends(get_current_user)):
    return current_user
```

Even though `main.py` also imports things like `FastAPI`, none of that is automatically available inside `routers/users.py` — Python's import system treats each file as independent unless it explicitly imports what it needs.

## Where `APIRouter()` Is Created — One Instance Per File, Typically

The conventional pattern, already followed in the auth system, is one `router = APIRouter()` instance per file, with every route in that file attached to that same instance:

```python
# routers/auth.py
router = APIRouter()

@router.post("/register")
def register(): ...

@router.post("/token")
def login(): ...

@router.post("/token/refresh")
def refresh_token(): ...
```

All three routes share the one `router` object defined at the top of the file. `main.py` then only needs one `include_router(auth.router)` call to bring in every route from that file at once — there's no need to include each route individually.

## What `APIRouter` Does *Not* Do

It's worth being precise about the boundaries of this tool, to avoid confusion with other mechanisms covered elsewhere in this phase:

- `APIRouter` does not create a separate "sub-application" with its own middleware or exception handling by default — those are configured on the main `FastAPI()` app, and apply across all included routers uniformly, unless deliberately customized further (a more advanced pattern than this basic introduction covers).
- `APIRouter` does not automatically add a path prefix or grouping tag — those require explicitly passing `prefix=` and `tags=` when creating the router or calling `include_router`, which is the next topic in this phase.
- `APIRouter` does not change how a client interacts with the API in any way — its effect is entirely about organizing the codebase, not about runtime behavior or the URLs clients actually call.

## Key Points to Retain

- `APIRouter` is a standalone, self-contained collection of routes, using the same route decorators as the main `FastAPI` app.
- Routes defined on an `APIRouter` do nothing on their own until explicitly connected to the main application via `app.include_router(...)`.
- Multiple routers can be included in one application, each typically corresponding to one file/one area of responsibility.
- Each router file needs its own imports — nothing is automatically shared between router files or with `main.py` just because they'll later be combined.
- The split is purely organizational; it has no effect on how the API behaves from a client's perspective.