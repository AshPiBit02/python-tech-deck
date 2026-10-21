# Testing FastAPI Applications

Testing is what turns a working application into a maintainable one. Every earlier phase produced code that was verified manually — through Swagger UI, Postman, or curl. Manual verification has a hard limit: it only proves the application worked *at the moment someone checked*, for the specific inputs they happened to try. An automated test suite re-proves, in seconds and on every change, that behavior which used to work still works. This phase covers how FastAPI applications are tested with `pytest`, how test isolation is achieved, and how to measure and improve coverage.

## Why Testing Matters More for APIs Than It First Appears

An API is a contract with its consumers. A frontend, a mobile app, or another service depends on specific routes returning specific status codes and response shapes. A change that silently alters a response field name, or accidentally loosens an authorization check, may not crash anything — it simply breaks a consumer, or opens a security hole, without any visible error on the server. Real examples of bugs that a test suite catches immediately and manual testing routinely misses:

- A refactor that removes the `"type": "access"` claim from a JWT, causing every protected route to reject valid tokens.
- A dependency change that lets a regular user reach an admin-only route.
- A schema edit that starts returning `hashed_password` in a response body.
- A validator that stops rejecting weak passwords.

Each of these is a single assertion in a test, and each is easy to introduce accidentally during unrelated work.

## The Testing Toolkit

| Tool | Purpose |
|---|---|
| `pytest` | Test runner — discovers test functions, runs them, reports results |
| `TestClient` (from `fastapi.testclient`) | Calls the app in-process without starting a real server; synchronous API |
| `httpx.AsyncClient` | Async alternative, required when the test itself must `await` things |
| `pytest-cov` | Measures which lines of the application the tests actually executed |
| `dependency_overrides` | FastAPI's built-in mechanism for swapping real dependencies with test versions |

```bash
pip install pytest httpx pytest-cov
```

## `TestClient` — The Everyday Tool

`TestClient` wraps the application so requests can be made as plain function calls, with no network, no server process, and no ports involved:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_about_route():
    response = client.get("/about")
    assert response.status_code == 200
    assert "description" in response.json()
```

The client exposes the familiar HTTP verbs (`get`, `post`, `put`, `patch`, `delete`) and accepts `json=`, `data=` (form-encoded), `headers=`, `params=`, and `files=`. The distinction between `json=` and `data=` is the same one that matters in Postman — `/token` expects form data (`data=`), while Pydantic-model routes expect JSON (`json=`).

### Using `TestClient` as a Context Manager

```python
def test_with_lifespan():
    with TestClient(app) as client:
        response = client.get("/quote")
        assert response.status_code == 200
```

The `with` form is required whenever the application defines a `lifespan` — only the context-manager form runs lifespan startup and shutdown. Without it, anything created during lifespan (a shared HTTP client, a loaded model, `app.state` values) simply does not exist, and tests fail with confusing `AttributeError`s. This is why the auth system's `conftest.py` creates its client inside a `with` block.

## Test Isolation — The Central Problem

A test is only trustworthy if its result does not depend on what ran before it. Shared mutable state — a database table, an in-memory dict, a file on disk — is the usual source of tests that pass alone but fail together (or the reverse). Several isolation strategies exist, with different tradeoffs:

| Strategy | How it works | Tradeoff |
|---|---|---|
| Transaction rollback per test | Each test runs inside a transaction that is rolled back afterward | Fast, real database behavior; requires the code under test not to commit outside the test's connection |
| Recreate tables per test | `create_all` before, `drop_all` after each test | Simple and thorough, but slow with many tests |
| Separate test database | A dedicated database that is never the development one | Essential baseline — protects real data regardless of other strategy |
| In-memory SQLite | Throwaway database in RAM | Very fast, but SQL dialect differences (e.g. Postgres native `ENUM`) can hide or create bugs |

The auth system's approach — a separate Postgres test database, tables created once per session, each test wrapped in a rolled-back transaction — combines the first and third strategies and avoids the SQLite dialect gap entirely.

## Fixtures — Reusable Setup and Teardown

A fixture is a function that prepares something tests need, handed to tests by parameter name:

```python
import pytest

@pytest.fixture
def sample_user():
    return {"email": "alice@example.com", "password": "strongpass123"}

def test_register(client, sample_user):
    response = client.post("/register", json={**sample_user, "confirm_password": sample_user["password"]})
    assert response.status_code == 200
```

Key fixture properties:

- **`yield` fixtures** run setup before the `yield` and teardown after the test finishes, whether it passed or failed.
- **`scope`** controls how often a fixture re-runs: `function` (default, every test), `module`, or `session` (once for the entire run). Expensive setup such as creating tables belongs at `session` scope; anything holding per-test state must stay at `function` scope.
- **`conftest.py`** is a special file pytest loads automatically; fixtures defined there are available to every test in that directory and below, with no import needed.
- **Fixtures can depend on other fixtures** by listing them as parameters, forming a dependency chain resolved automatically — `auth_headers` depends on `client` and `registered_user`, which depends on `db_session`.

## Overriding Dependencies — FastAPI's Key Testing Feature

Because FastAPI routes receive their collaborators through `Depends()`, a test can substitute any of them without touching application code:

```python
from main import app
from db.database import get_db
from dependencies.auth import get_current_user

def override_get_db():
    yield test_session

def override_get_current_user():
    return FakeUser(id=1, role="admin")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user
```

This enables two distinct styles of test:

- **Integration-style** — override only the database so everything else (real auth, real validation, real routes) runs for real against a test database. Catches wiring bugs.
- **Isolated/unit-style** — override `get_current_user` so a route can be tested without generating real tokens at all, focusing purely on that route's own logic.

`app.dependency_overrides` is global state on the app object, so it **must be cleared** after each test (`app.dependency_overrides.clear()`), ideally inside a fixture's teardown. Leaked overrides are a classic cause of tests affecting each other.

## Testing Authenticated Routes

Protected routes need a valid token. Two approaches, used for different purposes:

```python
@pytest.fixture
def auth_headers(client, registered_user):
    response = client.post("/token", data={"username": registered_user.email, "password": "strongpass"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

def test_get_me(client, auth_headers):
    response = client.get("/me", headers=auth_headers)
    assert response.status_code == 200
```

- **Real login flow** (above) — exercises the true authentication path end to end. Preferred for the small number of tests that verify authentication itself.
- **Overriding `get_current_user`** — bypasses tokens entirely. Preferred for the many tests of business logic behind authentication, where re-running the login flow each time adds no information and slows the suite.

A thorough suite also tests the **negative cases**: no token (401), garbage token (401), expired token (401), wrong token type such as a refresh token used as an access token (401), valid token with insufficient role (403). The ordering guarantee from the lifecycle phase — `401` before `403` — is itself something worth asserting.

## Async Tests — `httpx.AsyncClient`

When a test itself needs to `await` something (calling an async helper, using an async database session directly), the synchronous `TestClient` is not enough. The current pattern uses `httpx.AsyncClient` with an explicit ASGI transport:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.anyio
async def test_async_route():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/about")
    assert response.status_code == 200
```

Two details are current-practice specifics: the transport is passed explicitly via `ASGITransport(app=app)` (the older `AsyncClient(app=app)` shortcut has been removed from recent `httpx` versions), and async test functions need a plugin — either `pytest-asyncio` or `anyio`'s pytest plugin (`@pytest.mark.anyio`, which also requires an `anyio_backend` fixture returning `"asyncio"` if trio is not wanted). For applications whose routes are plain `def` with a synchronous database layer, like the auth system, `TestClient` alone is sufficient and simpler.

## Parametrized Tests — One Test, Many Cases

```python
@pytest.mark.parametrize("password", ["short", "1234567", ""])
def test_register_rejects_weak_passwords(client, password):
    response = client.post("/register", json={
        "email": "x@example.com", "password": password, "confirm_password": password,
    })
    assert response.status_code == 422
```

`parametrize` runs the same test body once per input, reporting each as a separate pass/fail. It replaces copy-pasted near-identical tests, and makes boundary cases (empty string, exactly-at-limit, one-below-limit) cheap to add.

## Factories — Generating Test Data

When tests need many users, orders, or products with slightly different attributes, hand-writing each is tedious and noisy. A small factory function supplies sensible defaults and lets each test override only what it cares about:

```python
def make_user_payload(**overrides):
    payload = {
        "email": "user@example.com",
        "password": "strongpass123",
        "confirm_password": "strongpass123",
    }
    payload.update(overrides)
    return payload

def test_duplicate_email(client):
    client.post("/register", json=make_user_payload())
    response = client.post("/register", json=make_user_payload())
    assert response.status_code == 400

def test_admin_without_key(client):
    response = client.post("/register", json=make_user_payload(role="Admin"))
    assert response.status_code == 422
```

Each test now states only what makes it *different* from the baseline, which makes the intent obvious at a glance.

## Mocking External Dependencies

Routes that call third-party services (weather APIs, payment gateways, email providers) must not hit the real service during tests — it makes tests slow, flaky, dependent on the network, and sometimes costly. Two common approaches:

```python
# 1. Override the dependency that provides the HTTP client
def override_http_client():
    return FakeHttpClient(canned_response={"temp_C": "20"})

app.dependency_overrides[get_http_client] = override_http_client
```

```python
# 2. unittest.mock.patch on the function that makes the call
from unittest.mock import patch, AsyncMock

def test_weather_route(client):
    with patch("routers.weather.fetch_weather", new=AsyncMock(return_value={"temp_C": "20"})):
        response = client.get("/weather/London")
    assert response.json()["temp_C"] == "20"
```

Overriding a dependency is cleaner when the application was already designed with the collaborator injected via `Depends()` — another practical payoff of the dependency-injection style used throughout this roadmap.

## Testing Other Phase Features

- **Middleware** — tested implicitly through any request; assert on the headers it adds (`X-Request-ID`, `X-Process-Time`) or the early-rejection response it produces.
- **Custom exception handlers** — trigger the condition and assert the handler's exact status code and body shape.
- **Background tasks** — `TestClient` runs them to completion before returning, so their side effects (a log entry, a written file) can be asserted immediately after the request.
- **File uploads** — `client.post("/upload", files={"file": ("test.png", file_bytes, "image/png")})`; test oversized files, wrong magic bytes, and path-traversal filenames explicitly.
- **Lifespan** — use `with TestClient(app) as client:` so startup/shutdown actually run.

## Coverage — Measuring What Tests Actually Touch

```bash
pytest --cov=. --cov-report=term-missing
```

`pytest-cov` reports, per file, what percentage of lines executed during the test run, and with `term-missing` lists the exact line numbers that never ran. Those unexecuted lines are a to-do list of untested behavior — typically error branches and edge cases.

```bash
pytest --cov=. --cov-fail-under=80
```

`--cov-fail-under` makes the run fail if overall coverage drops below a threshold, which is how a coverage standard is enforced automatically in CI.

Coverage has an important limit: it proves a line *ran*, not that anything meaningful was *asserted* about it. A test that calls a route and asserts nothing still produces coverage. High coverage is a necessary signal of thoroughness, never a sufficient one — assertion quality matters as much as the percentage.

## Organizing a Test Suite

```
project/
├── tests/
│   ├── conftest.py          # shared fixtures: db_session, client, auth_headers
│   ├── test_register.py
│   ├── test_login.py
│   ├── test_me.py
│   └── test_admin.py
├── pytest.ini               # test configuration
```

A typical `pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = -v
```

One test file per router or feature area keeps failures easy to locate. Test names should read as sentences describing behavior (`test_login_wrong_password`), so that a failing test name alone explains what broke.

## Common Pitfalls

- **Forgetting `with TestClient(app)`** when the app uses `lifespan` — resources never initialize.
- **Leaking `dependency_overrides`** between tests — always clear them in fixture teardown.
- **Tests that depend on execution order** — each test must set up everything it needs; relying on a previous test having created a user makes the suite fragile.
- **Running tests against the development database** — a single missing environment flag can wipe real data. The `TESTING` environment variable set at the very top of `conftest.py`, before any app import, exists specifically to prevent this.
- **Asserting only status codes** — a `200` with a wrong body is still a bug; assert on response content and, where relevant, on database state afterwards.
- **Over-mocking** — mocking so much that a test only verifies the mocks proves nothing about real behavior. Mock external boundaries, not the code under test.
- **Hardcoded secrets or expiry-dependent tokens** — tests relying on a fixed token that later expires fail mysteriously months afterward; generate tokens fresh inside fixtures.

## Key Points to Retain

- Automated tests re-prove behavior on every change; for APIs, they guard the contract with consumers and the correctness of authorization rules that manual checking easily misses.
- `TestClient` covers most needs for synchronous apps; `httpx.AsyncClient` with `ASGITransport` is used when the test itself must be async. Use `with TestClient(app)` whenever lifespan matters.
- Test isolation is the central design problem — separate test database plus per-test rollback is a robust, realistic combination.
- Fixtures, `conftest.py`, and `parametrize` keep setup reusable and cases compact; factories keep test data readable by stating only what differs.
- `dependency_overrides` is FastAPI's built-in seam for testing: override the database for integration-style tests, or the current-user dependency for isolated ones — and always clear overrides afterward.
- Coverage measures execution, not verification; use `term-missing` to find untested branches, and treat the percentage as a floor rather than a goal.

---

# Practice Exercises

1. **Parametrize a validator** — convert the weak-password test in `test_register.py` into one `parametrize`d test with at least five boundary cases (empty, 1 char, 7 chars, exactly 8, whitespace-only).
2. **Negative-path auth tests** — add tests for an expired token, a refresh token used as an access token, and a malformed `Authorization` header, asserting `401` for each.
3. **Assert the 401-before-403 ordering** — write a test showing a garbage token on an admin route returns `401`, while a valid non-admin token returns `403`.
4. **Add a factory** — introduce `make_user_payload(**overrides)` and refactor the registration tests to use it.
5. **Isolated route test** — test `GET /me` by overriding `get_current_user` with a fake user, with no database fixture involved, and compare its speed and setup against the integration-style version.
6. **Measure coverage** — run `pytest --cov=. --cov-report=term-missing`, pick the file with the lowest coverage, and write tests for its missing lines.
7. **Mock an external call** — take the Weather Aggregator project, mock `fetch_weather` so the tests never touch the network, and assert the partial-failure behavior with one city made to fail.