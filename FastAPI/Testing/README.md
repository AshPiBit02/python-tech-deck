# Phase 10 — Testing FastAPI Applications

> **Mini project:** Test suite for the Phase 5 Contact Book API
> **Done when:** `pytest --cov` shows **80%+ coverage**, all tests pass, and every run starts from a **fresh test database**.
> **Time:** 3–4 days

Companion files: [`TEST_PLAN.md`](TEST_PLAN.md) (what to test, checklist) · [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) (common errors, command cheatsheet)

---

## 1. Why test at all?

| Without tests | With tests |
|---|---|
| Every refactor (Phase 11) is a gamble | Refactor, run `pytest`, know in seconds |
| Auth bugs ship silently | Protected routes are verified with/without token |
| Manual testing in `/docs` per change | One command re-checks everything |

**Test pyramid for APIs** (what you'll write in this phase):

```
        /\        Few  : end-to-end flows (register -> login -> create -> delete)
       /  \
      /----\      Many : API/integration tests (client -> route -> DB)   <- main focus
     /------\
    /--------\    Some : unit tests (pure functions: password hashing, validators)
```

For FastAPI, the highest-value tests are **API tests with `TestClient`** — they exercise routing, validation, dependencies, and DB in one shot.

---

## 2. Setup

```bash
pip install pytest httpx pytest-cov
# only if you test async code:
pip install pytest-asyncio
```

`requirements-dev.txt`:
```
pytest
httpx
pytest-cov
pytest-asyncio
```

> `TestClient` is built on `httpx` — it will not import without it.

### Recommended layout

```
contact_book/
├── main.py
├── db/database.py          # engine, SessionLocal, Base, get_db
├── models/
├── schemas/
├── routers/
├── tests/
│   ├── __init__.py         # (empty) keeps imports predictable
│   ├── conftest.py         # shared fixtures: db, client, auth
│   ├── factories.py        # test-data builders
│   ├── test_contacts.py    # CRUD + search + validation
│   ├── test_auth.py        # login, protected routes
│   └── test_admin.py       # role-based routes
├── pytest.ini
└── requirements-dev.txt
```

`pytest.ini`:
```ini
[pytest]
testpaths = tests
addopts = -ra --strict-markers
asyncio_mode = auto
```

> Remove `asyncio_mode` if you did not install `pytest-asyncio`.

---

## 3. Core concepts

### 3.1 pytest basics
- Files `test_*.py`, functions `test_*`. Plain `assert` — no `assertEqual` needed (unlike Java JUnit).
- Test **one behavior per test**; name it like a sentence: `test_duplicate_email_rejected`.
- Structure each test as **Arrange -> Act -> Assert**.

```python
def test_get_nonexistent_contact(client):
    response = client.get("/contacts/9999")      # Act
    assert response.status_code == 404            # Assert
```

### 3.2 `TestClient` (sync)
Calls your app **in-process** — no server, no network, no port.

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
r = client.get("/contacts")
assert r.status_code == 200
```

### 3.3 `AsyncClient` (async tests)
Use only when the **test itself** must `await` (async DB engine, async helpers). Otherwise `TestClient` works fine even for `async def` routes.

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_list_contacts_async():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/contacts")
    assert r.status_code == 200
```

> `AsyncClient(app=app)` is the old syntax — removed in newer httpx. Use `ASGITransport`.

### 3.4 Fixtures
Reusable setup/teardown, injected by **parameter name**. `yield` splits setup from teardown.

| Scope | Runs | Use for |
|---|---|---|
| `function` (default) | once per test | DB session, client (isolation) |
| `module` / `session` | once per file / run | expensive, read-only setup |

### 3.5 Dependency overrides — *the key FastAPI testing feature*
Your routes use `Depends(get_db)`. In tests you swap it for a test DB:

```python
app.dependency_overrides[get_db] = override_get_db
...
app.dependency_overrides.clear()   # ALWAYS clean up
```

The same trick replaces `get_current_user` to skip auth.

### 3.6 Test database strategy

| Option | Pros | Cons |
|---|---|---|
| **SQLite in-memory** (default below) | Fast, zero setup, fresh every test | Not MySQL: differences in types, collation, constraint behavior |
| **Separate MySQL test DB** (`contactbook_test`) | Matches production | Slower, needs running server |

Start with SQLite to learn the pattern. Later, point `TEST_DATABASE_URL` to a MySQL test database to catch dialect-specific bugs. **Never run tests against your real database** — tests create/drop tables.

---

## 4. `tests/conftest.py` (core of the whole suite)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db.database import Base, get_db

# In-memory SQLite. StaticPool keeps ONE connection so all sessions
# see the same in-memory DB (otherwise each connection gets an empty DB).
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db():
    """Fresh schema for every test -> full isolation."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """TestClient wired to the test DB."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

> Use `TestClient(app)` **without** `with` unless you need startup/shutdown events. If your app calls `Base.metadata.create_all(engine)` on startup against MySQL, the `with` form would hit your real DB.

---

## 5. Factory pattern for test data

Avoid copy-pasting dicts. A factory builds valid data with sensible defaults; tests override only what matters.

`tests/factories.py`:
```python
from itertools import count
from models.contact import Contact   # adjust to your model path

_seq = count(1)

def contact_payload(**overrides) -> dict:
    """Dict for POST/PUT bodies. Unique email each call."""
    n = next(_seq)
    data = {
        "name": f"User {n}",
        "email": f"user{n}@test.com",
        "phone": "1234567890",
        "city": "London",
    }
    data.update(overrides)
    return data

def create_contact(db, **overrides) -> Contact:
    """Insert directly into DB (bypasses the API) for arrange-phase seeding."""
    contact = Contact(**contact_payload(**overrides))
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact
```

Usage:
```python
from tests.factories import contact_payload, create_contact

def test_search_by_city(client, db):
    create_contact(db, name="Alice", city="London")
    create_contact(db, name="Bob", city="Paris")

    r = client.get("/contacts/search", params={"q": "london"})

    assert r.status_code == 200
    assert [c["name"] for c in r.json()] == ["Alice"]
```

> Seed via `db` (fast, independent of the POST route). Use the API for seeding only when testing that flow.

---

## 6. Example tests (from the roadmap, completed)

```python
# tests/test_contacts.py
from tests.factories import contact_payload, create_contact


def test_create_contact(client, db):
    r = client.post("/contacts", json=contact_payload(name="Alice", email="alice@test.com"))
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Alice"
    assert "id" in body


def test_get_nonexistent_contact(client):
    assert client.get("/contacts/9999").status_code == 404


def test_duplicate_email_rejected(client, db):
    client.post("/contacts", json=contact_payload(email="bob@test.com"))
    r = client.post("/contacts", json=contact_payload(email="bob@test.com"))
    assert r.status_code in (400, 409, 422)   # pin to your app's real choice


def test_invalid_email_rejected(client):
    r = client.post("/contacts", json=contact_payload(email="not-an-email"))
    assert r.status_code == 422               # Pydantic validation


def test_pagination(client, db):
    for _ in range(5):
        create_contact(db)
    r = client.get("/contacts", params={"skip": 2, "limit": 2})
    assert len(r.json()) == 2
```

**Parametrize** to avoid repetition:
```python
import pytest

@pytest.mark.parametrize("bad", [
    {"name": ""},                       # empty name
    {"email": "nope"},                  # bad email
    {"name": "x" * 101},                # over max length
])
def test_create_invalid(client, bad):
    r = client.post("/contacts", json=contact_payload(**bad))
    assert r.status_code == 422
```

---

## 7. Testing auth-protected routes (Phase 6)

Two approaches — know both.

### A. Real tokens (tests the whole auth chain) — preferred for a few core tests
```python
# tests/conftest.py (append)
from auth.security import create_access_token, hash_password   # adjust to your code
from models.user import User

@pytest.fixture
def make_user(db):
    def _make(username="alice", password="secret123", role="user"):
        user = User(username=username, hashed_password=hash_password(password), role=role)
        db.add(user); db.commit(); db.refresh(user)
        return user
    return _make

@pytest.fixture
def auth_headers(make_user):
    user = make_user()
    token = create_access_token({"sub": user.username})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(make_user):
    admin = make_user(username="admin", role="admin")
    token = create_access_token({"sub": admin.username})
    return {"Authorization": f"Bearer {token}"}
```

```python
# tests/test_auth.py
def test_protected_route_without_token(client):
    assert client.delete("/contacts/1").status_code == 401

def test_protected_route_with_token(client, db, auth_headers):
    c = create_contact(db)
    assert client.delete(f"/contacts/{c.id}", headers=auth_headers).status_code in (200, 204)

def test_invalid_token_rejected(client):
    r = client.get("/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401

# tests/test_admin.py
def test_admin_route_forbidden_for_normal_user(client, auth_headers):
    assert client.get("/admin/users", headers=auth_headers).status_code == 403

def test_admin_route_allowed_for_admin(client, admin_headers):
    assert client.get("/admin/users", headers=admin_headers).status_code == 200
```

### B. Override the auth dependency (fast, skips token logic)
```python
from auth.deps import get_current_user

def test_with_fake_user(client):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(role="admin")
    ...
    app.dependency_overrides.pop(get_current_user)   # or rely on client fixture cleanup
```

> Use B for route logic tests, A for auth tests. Always test **both** the unauthenticated (401) and unauthorized (403) paths.

---

## 8. Coverage

```bash
pytest --cov=. --cov-report=term-missing           # shows uncovered line numbers
pytest --cov=. --cov-report=html                   # open htmlcov/index.html
pytest --cov=. --cov-fail-under=80                 # fail if below target
```

`.coveragerc` (exclude noise):
```ini
[run]
omit =
    tests/*
    alembic/*
    */__init__.py
```

> **80% is a floor, not the goal.** Coverage shows what code *ran*, not whether assertions are meaningful. Read the `Missing` column and test the uncovered branches (error paths first).

---

## 9. Best practices

1. **Isolation:** each test gets a fresh DB; no test depends on another's data or order.
2. **Assert more than status code:** also check body fields and, for writes, the DB state.
3. **Test failure paths:** 404, 422, 401, 403, duplicates — these are where bugs live.
4. **No real external calls:** mock email, payment, HTTP APIs (`unittest.mock.patch`, or override a dependency).
5. **Keep tests fast:** whole suite should run in seconds.
6. **Deterministic data:** no random values without a seed; no reliance on current time without freezing/overriding it.
7. **Commit tests with the feature**, not afterwards.

---

## 10. Workflow for the mini project

1. Install tools, create `tests/` layout, write `conftest.py`, run one smoke test.
2. Write CRUD tests (happy path) -> run `pytest`.
3. Add failure/validation tests.
4. Add search + pagination tests.
5. Add auth + admin tests.
6. Run `pytest --cov=. --cov-report=term-missing`, fill gaps until 80%+.
7. Verify freshness: run the suite twice — results must be identical.

Track progress in [`TEST_PLAN.md`](TEST_PLAN.md).

---

## 11. Assumptions in this guide (adjust to your code)

- Flat layout with `main.py`, `db/database.py` exposing `Base` and `get_db`.
- Sync SQLAlchemy sessions (`pymysql`). If you used the async engine (`aiomysql`), tests need an async engine, `AsyncSession`, and `AsyncClient`.
- Import paths (`models.contact`, `auth.security`, `auth.deps`) are placeholders.
- Auth route names (`/me`, `/admin/users`) are examples.