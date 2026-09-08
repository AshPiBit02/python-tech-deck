# OAuth2 — From Basics to Production

Covers: what OAuth2 actually is, the Password flow used by FastAPI tutorials,
`OAuth2PasswordBearer`/`OAuth2PasswordRequestForm` in depth, scopes, RBAC,
and the gaps between a learning project and a production-ready system.

---

## Part 1 — Basics

### 1.1 What OAuth2 Actually Is

OAuth2 is an **authorization framework** — a standardized specification describing how a client can obtain and use a token to act on behalf of a user, without the user's raw password being handled beyond the initial exchange. It is not a library and not FastAPI-specific — it is a spec implemented by many systems (Google login, GitHub login, a custom API).

**Important distinction:** OAuth2 is technically about **authorization** (what an actor is allowed to do), but in practice — and in the login systems built earlier in this project — it is used as the mechanism for **authentication** (proving identity) too, since a valid access token implies identity was already proven to obtain it.

### 1.2 Why FastAPI's OAuth2 Conventions Matter, Even for a Simple Login System

A working login system can be built without any OAuth2-specific tooling — plain Pydantic bodies, `Header()`, JWT functions, exactly as done in the Simple Login API project. So the OAuth2-specific classes are not strictly required for functionality.

**The reason to use them anyway: tooling compatibility.** `/docs` (Swagger UI) has a built-in "Authorize" button, a padlock icon on protected routes, and a login form — all of this only activates correctly when routes use FastAPI's OAuth2-flavored classes (`OAuth2PasswordBearer`, `OAuth2PasswordRequestForm`). A plain `Header()` approach works functionally, but loses that built-in UI convenience, and other tools/clients expecting standard OAuth2 shapes will not recognize a custom header pattern like `x-token`.

### 1.3 OAuth2 "Flows" — Several Exist, Only One Is Relevant Here

OAuth2 defines multiple **flows** (grant types) for different scenarios:

| Flow | Used when |
|---|---|
| **Password** (Resource Owner Password Credentials) | The client is trusted and collects username/password directly — the pattern used in this project |
| **Authorization Code** | Third-party login (e.g. "Sign in with Google") — the user is redirected to the provider, never gives the app their provider password directly |
| **Client Credentials** | Machine-to-machine — no human user involved, a service authenticating as itself |
| **Implicit** | Older, largely deprecated flow for browser-based apps — avoided in new work |

**The Password flow is the appropriate choice here** — the client and the API are owned by the same project (a banking app's own login, not "log in with a third party"). The Authorization Code flow becomes relevant only if third-party login (Google/GitHub) is added later — a separate, more involved topic not covered in this document.

---

## Part 2 — `OAuth2PasswordBearer` in Depth

### 2.1 What It Actually Does

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

`oauth2_scheme` is a **dependency** (the same `Depends()` mechanism covered in Phase 4). Used on a route:

```python
@app.get("/me")
def get_me(token: str = Depends(oauth2_scheme)):
    ...
```

it does exactly one job: **extract the token from the `Authorization: Bearer <token>` header**, raising `401` automatically if that header is missing or malformed. It does **not** verify the token's signature or expiry — that remains a separate step, using `decode_access_token` or equivalent, same as the manual `Header()` version built earlier.

### 2.2 `tokenUrl` — What It's Actually For

```python
OAuth2PasswordBearer(tokenUrl="token")
```

This is **not** a URL the code calls internally. It is metadata telling Swagger UI: *"if a user clicks 'Authorize,' send their login form to this path."* Swagger reads this value to wire up its own UI — it has no effect on the route's runtime behavior otherwise.

### 2.3 Comparison — Manual Header Extraction vs. This Class

| | Manual `Header(...)` | `OAuth2PasswordBearer` |
|---|---|---|
| Extracts token from `Authorization` header | Handled manually (or worked around via an `x-token` header, due to Swagger's special-casing of a header literally named `authorization`) | Automatic |
| Missing header handling | Checked and raised manually | Automatic `401` |
| Swagger "Authorize" button | Does not integrate | Works out of the box |
| Actual verification (signature/expiry) | Manual, same either way | Still manual — this tool only extracts, never verifies |

**Key point:** `OAuth2PasswordBearer` does not replace `decode_access_token` at all — it only replaces the *extraction* step. Verification logic stays exactly as built before.

### 2.4 Rebuilding `/me` With It

```python
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token!")
    return payload


@app.get("/me")
def get_me(payload: dict = Depends(get_current_user)):
    return {"email": payload.get("sub")}
```

This is a **nested dependency** (Phase 4 concept, reused directly) — `get_me` depends on `get_current_user`, which depends on `oauth2_scheme`. Same chain-resolution mechanics covered earlier, no new concept.

---

## Part 3 — `OAuth2PasswordRequestForm` in Depth

### 3.1 What It Actually Does

```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    ...
```

Reads **form-encoded** POST data (not JSON) into a structured object with these fields:
- `form_data.username` — holds the email in this project's case (OAuth2 spec names it "username" generically)
- `form_data.password`
- `form_data.grant_type`, `form_data.scope`, `form_data.client_id`, `form_data.client_secret` — OAuth2-standard extras, mostly unused in a simple password-flow setup

### 3.2 Why Form Data, Not JSON

This is dictated by the OAuth2 spec itself, not a FastAPI preference — the Password flow standard specifies form-encoded submission. This exact shape is what Swagger's "Authorize" login popup submits, which is why using this class (rather than a custom Pydantic body) makes that built-in UI function correctly.

### 3.3 Rebuilding the Login Route With It

```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    if email not in USERS:
        raise HTTPException(status_code=401, detail="Invalid username, register first")
    if not verify_password(form_data.password, USERS[email]["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect password!")
    access_token = create_access_token({"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}
```

**Route path convention:** `/token` (rather than `/login`) is the conventional name, matching `tokenUrl="token"` from `OAuth2PasswordBearer` — both should point at the same path.

### 3.4 The Swagger UI "Authorize" Button, Once Both Pieces Are in Place

With both classes wired up, `/docs` shows a padlock icon on protected routes and an "Authorize" button at the top. Clicking it opens a login form (username/password); submitting it calls `/token`, stores the returned access token internally, and **automatically attaches it** to every subsequent request made from within `/docs`. No manual copy/paste of a token into each request is needed — the concrete payoff of adopting these classes.

---

## Part 4 — Scopes (Introduction)

### 4.1 What Scopes Are

Scopes let a token carry **fine-grained permissions**, beyond just identity. Example:

```python
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"read": "Read access", "write": "Write access", "admin": "Admin access"}
)
```

A token can be issued with specific scopes (`["read", "write"]`), and individual routes can require specific scopes to be present:

```python
from fastapi.security import SecurityScopes

def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
) -> dict:
    payload = decode_access_token(token)
    token_scopes = payload.get("scopes", [])
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    return payload
```

**Assessment:** scopes offer a more granular, standards-compliant approach to permissions than a simple `role` claim, but add real complexity. For a project like the Mobile Banking API, a simpler `role` claim (`"customer"`, `"admin"`) checked via a plain dependency (covered next, RBAC) is usually sufficient and easier to reason about. Scopes are more valuable in larger systems with many independently-grantable permissions (e.g. a public API where third-party apps request specific access levels).

---

## Part 5 — Role-Based Access Control (RBAC) — The Practical Approach

### 5.1 A Simpler Alternative to Scopes — a `role` Claim

```python
access_token = create_access_token({"sub": customer.email, "role": customer.role})
```

### 5.2 Building Role-Checking Dependencies (Direct Application of Nested Dependencies)

```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token!")
    return payload


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

```python
@app.get("/admin/all_customers")
def list_all_customers(admin: dict = Depends(require_admin)):
    ...
```

This mirrors the nested-dependency pattern from Phase 4 (`get_current_admin` built on top of `get_current_user`) — no new concept, now backed by a real JWT-verified identity instead of a fake in-memory session dict.

---

## Part 6 — Moving Toward Production

Everything above is functionally correct but has real gaps a production system must close.

### 6.1 `SECRET_KEY` Generation

```python
import secrets
print(secrets.token_hex(32))   # generates a real, cryptographically random secret
```
A memorable placeholder string is unsuitable for production — the real secret should be generated once, stored in `.env`, and never regenerated casually (regenerating invalidates every issued token).

### 6.2 Token Revocation — The Biggest Gap in Pure Stateless JWT

A stateless JWT, once issued, remains valid until it **naturally expires** — no built-in mechanism exists to invalidate it early (on logout, or if a token is stolen). Production systems typically add one of:
- **A token blocklist** — a fast lookup (Redis, or a DB table) of revoked token IDs, checked on every request
- **Short-lived access tokens + revocable refresh tokens** — the pattern covered earlier; revoking the refresh token in the DB keeps the damage window for a stolen access token naturally small

### 6.3 HTTPS Only

JWTs sent over plain HTTP are trivially interceptable — anyone on the network path can read the `Authorization` header. Production APIs must run behind HTTPS, often handled by a reverse proxy (Nginx) or the hosting platform rather than FastAPI itself — a hard requirement, not optional.

### 6.4 Rate Limiting Login Attempts

Without it, a login endpoint is vulnerable to brute-force password guessing. Production systems add rate limiting (e.g. `slowapi`, per the project roadmap's Phase 13) specifically on login/auth endpoints.

### 6.5 Password Reset Flow

Not yet covered — a real system needs a "forgot password" flow: generate a short-lived, single-use reset token, email it to the user, allow setting a new password. Same JWT mechanics, applied to a different purpose (a `type: "password_reset"` claim, very short expiry).

### 6.6 Account Lockout / Suspicious Activity Detection

Repeated failed login attempts on one account, or a refresh token used from two different locations in quick succession, are signals worth detecting and acting on (temporary lockout, forced re-verification) — genuinely advanced, but a real-world consideration.

### 6.7 No Custom Cryptography Beyond This Point

Everything covered here (bcrypt hashing, `python-jose` for JWT) uses well-vetted, standard libraries. The production gaps above concern **system design** (revocation, rate limiting, HTTPS), not custom cryptographic code. Any requirement that seems to need custom crypto is a signal to research existing solutions further, not to implement one from scratch.

---

## Notes — Cross-Language Parallels

- OAuth2 flows parallel different authentication strategies in Java Spring Security (`AuthenticationProvider` implementations) — same idea, different spec/ecosystem
- Scopes parallel Java's fine-grained permission annotations, or AWS IAM policy scoping — narrow, composable grants of access
- A token blocklist for revocation parallels a server-side session invalidation table — the stateful compromise layered on top of otherwise-stateless JWTs

---

## Quick Self-Check
- [ ] OAuth2 is a spec/framework, not a library
- [ ] Which OAuth2 flow applies to a self-owned client+API project, and why
- [ ] What `OAuth2PasswordBearer` does and does not do (extraction only, not verification)
- [ ] Why `OAuth2PasswordRequestForm` uses form data instead of JSON
- [ ] What makes Swagger's "Authorize" button work, concretely
- [ ] The tradeoff between scopes and a simple role claim, and when each fits
- [ ] At least three real gaps between a learning-project auth system and a production-ready one
- [ ] Why a pure stateless JWT cannot be revoked early, and the two common fixes