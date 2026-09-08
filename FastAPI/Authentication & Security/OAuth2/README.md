# OAuth2 — From Basics to Production

Covers: what OAuth2 actually is, the Password flow used by FastAPI tutorials,
`OAuth2PasswordBearer`/`OAuth2PasswordRequestForm` in depth, scopes, RBAC,
and what changes moving from a learning project to production.

---

## Part 1 — Basics

### 1.1 What OAuth2 Actually Is

OAuth2 is an **authorization framework** — a standardized specification describing how a client can obtain and use a token to act on behalf of a user, without ever handling the user's raw password beyond the initial exchange. It's not a library, not FastAPI-specific — it's a spec that many systems (Google login, GitHub login, your own API) implement.

**Important distinction:** OAuth2 is technically about **authorization** (what you're allowed to do), but in practice — and in everything you've built so far — it's used as the *mechanism* for **authentication** (proving who you are) too, since a valid access token implies you successfully proved your identity to get it.

### 1.2 Why FastAPI Uses OAuth2 Conventions, Even for a Simple Login System

You already built a working login system without any OAuth2-specific tooling — plain Pydantic bodies, `Header()`, JWT functions. That works. So why bother with OAuth2's specific shapes at all?

**The answer: tooling compatibility.** `/docs` (Swagger UI) has a built-in "Authorize" button, a padlock icon on protected routes, and a login form — all of this only activates correctly if your routes use FastAPI's OAuth2-flavored classes (`OAuth2PasswordBearer`, `OAuth2PasswordRequestForm`). Using plain `Header()` works functionally, but you lose that built-in UI convenience, and any other tool/client expecting standard OAuth2 shapes won't recognize your custom `x-token` header pattern.

### 1.3 OAuth2 "Flows" — There Are Several, You're Using One

OAuth2 defines multiple **flows** (also called "grant types") for different scenarios:

| Flow | Used when |
|---|---|
| **Password** (Resource Owner Password Credentials) | The client (your own frontend) is trusted, collects username/password directly — what you're building |
| **Authorization Code** | Third-party login (e.g. "Sign in with Google") — the user is redirected to Google, never gives your app their Google password directly |
| **Client Credentials** | Machine-to-machine — no human user involved at all, a service authenticating as itself |
| **Implicit** | Older, largely deprecated flow for browser-based apps — avoid in new work |

**You are using the Password flow** — appropriate because you own both the client and the API (a banking app's own login, not "log in with a third party"). The Authorization Code flow becomes relevant if you ever add "Sign in with Google/GitHub" — a different, more involved topic not covered here.

---

## Part 2 — `OAuth2PasswordBearer` in Depth

### 2.1 What It Actually Does

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

`oauth2_scheme` is a **dependency** (same `Depends()` mechanism from Phase 4). When used on a route:

```python
@app.get("/me")
def get_me(token: str = Depends(oauth2_scheme)):
    ...
```

it does exactly one job: **extract the token from the `Authorization: Bearer <token>` header**, or raise `401` automatically if that header is missing or malformed. It does **not** verify the token's signature or expiry — that's still your job, using `decode_access_token` (or equivalent), same as your manual `Header()` version.

### 2.2 `tokenUrl` — What It's Actually For

```python
OAuth2PasswordBearer(tokenUrl="token")
```

This is **not** a URL your code calls internally. It's metadata that tells Swagger UI: *"if the user clicks 'Authorize,' send their login form to this path."* Swagger reads this value to wire up its own UI — it has zero effect on your route's runtime behavior otherwise.

### 2.3 Direct Comparison — Your Manual Version vs. This

| | Manual `Header(...)` | `OAuth2PasswordBearer` |
|---|---|---|
| Extracts token from `Authorization` header | You do it (or worked around the header-naming quirk with `x-token`) | Automatic |
| Missing header handling | You check `None`/raise manually | Automatic `401` |
| Swagger "Authorize" button | Doesn't work with this | Works out of the box |
| Actual verification (signature/expiry) | Manual, your code | Still manual, your code — this tool ONLY extracts, never verifies |

**The key realization:** `OAuth2PasswordBearer` doesn't replace your `decode_access_token` function at all — it only replaces the *extraction* step. You still need your own verification logic exactly as before.

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

Notice this is a **nested dependency** (Phase 4 concept, reused directly) — `get_me` depends on `get_current_user`, which depends on `oauth2_scheme`. Same chain-resolution mechanics you already know.

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
- `form_data.username` — despite the name, this holds the **email** in your case (OAuth2 spec calls it "username" generically)
- `form_data.password`
- `form_data.grant_type`, `form_data.scope`, `form_data.client_id`, `form_data.client_secret` — OAuth2-standard extras, mostly ignorable for a simple password-flow setup

### 3.2 Why Form Data, Not JSON

This is dictated by the OAuth2 spec itself, not a FastAPI preference — the Password flow standard specifies form-encoded submission. This exact shape is what Swagger's "Authorize" login popup submits to, which is why using this class (rather than a custom Pydantic body) makes that built-in UI work correctly.

### 3.3 Rebuilding `/login` (renamed `/token`, matching convention) With It

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

**Route path convention:** `/token` (not `/login`) is the conventional name, matching `tokenUrl="token"` from `OAuth2PasswordBearer` — they should point at the same path.

### 3.4 Now the Swagger UI "Authorize" Button Actually Works

Once both pieces are in place, `/docs` shows a padlock icon on protected routes and an "Authorize" button at the top. Clicking it opens a login form (username/password) — submitting it calls `/token`, stores the returned access token internally, and **automatically attaches it** to every subsequent request from within `/docs`. You no longer need to manually copy/paste a token into each request — this is the actual, tangible payoff of switching to these classes.

---

## Part 4 — Scopes (Introduction)

### 4.1 What Scopes Are

Scopes let a token carry **fine-grained permissions**, beyond just "who is this." Example:

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

**Honest assessment for your use case:** scopes are a genuinely more granular, standards-compliant approach to permissions than a simple `role` claim — but they add real complexity. For a project like Banking, a simpler `role` claim (`"customer"`, `"admin"`) checked via a plain dependency (covered next, RBAC) is usually sufficient and much easier to reason about. Scopes shine in larger systems with many independently-grantable permissions (e.g. a public API where third-party apps request specific access levels) — worth knowing they exist, not necessarily worth adopting for every project.

---

## Part 5 — Role-Based Access Control (RBAC) — The Practical Approach

### 5.1 The Simpler Alternative to Scopes — a `role` Claim

```python
access_token = create_access_token({"sub": customer.email, "role": customer.role})
```

### 5.2 Building Role-Checking Dependencies (Direct Application of Phase 4 — Nested Dependencies)

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

This is **exactly** the nested-dependency pattern from Phase 4 (`get_current_admin` built on top of `get_current_user`) — nothing new conceptually, just now backed by a real JWT-verified identity instead of a fake in-memory session dict.

---

## Part 6 — Moving Toward Production

Everything above is functionally correct but has real gaps a production system must close. Being honest about each:

### 6.1 `SECRET_KEY` Generation

```python
import secrets
print(secrets.token_hex(32))   # generates a real, cryptographically random secret
```
Never use a memorable string like `"dev-secret-change-this"` in production — generate this once, store it in `.env`, never regenerate casually (regenerating invalidates every issued token).

### 6.2 Token Revocation — The Biggest Gap in Pure Stateless JWT

A stateless JWT, once issued, is valid until it **naturally expires** — there's no built-in way to invalidate it early (e.g. on logout, or if a token is stolen). Production systems typically add one of:
- **A token blocklist** — a fast lookup (Redis, or a DB table) of revoked token IDs, checked on every request
- **Short-lived access tokens + revocable refresh tokens** — the pattern from your earlier notes; revoke the refresh token in the DB, and the damage window for a stolen access token is naturally small (since it expires soon anyway)

### 6.3 HTTPS Only

JWTs sent over plain HTTP are trivially interceptable (anyone on the network path can read the `Authorization` header). Production APIs must run behind HTTPS — this is often handled by a reverse proxy (Nginx) or the hosting platform, not FastAPI itself, but it's a hard requirement, not optional.

### 6.4 Rate Limiting Login Attempts

Without it, `/token` is vulnerable to brute-force password guessing. Production systems add rate limiting (e.g. `slowapi`, mentioned in your own roadmap's Phase 13) specifically on login/auth endpoints.

### 6.5 Password Reset Flow

Not covered in what you've built — a real system needs a "forgot password" flow: generate a short-lived, single-use reset token, email it to the user, let them set a new password. Same JWT mechanics, applied to a different purpose (a `type: "password_reset"` claim, very short expiry).

### 6.6 Account Lockout / Suspicious Activity Detection

Repeated failed login attempts for one account, or a refresh token being used from two different locations in quick succession, are signals worth detecting and acting on (temporary lockout, forced re-verification) — genuinely advanced, but worth knowing real systems do this.

### 6.7 Don't Roll Your Own Crypto Beyond This Point

Everything covered here (bcrypt hashing, `python-jose` for JWT) uses well-vetted, standard libraries — correct. The production gaps above are about **system design** (revocation, rate limiting, HTTPS), not about needing to write custom cryptographic code. If a requirement ever seems to need custom crypto, that's a signal to research existing solutions harder, not to implement it yourself.

---

## 📌 Notes for Background
- OAuth2 flows ≈ different authentication strategies in Java Spring Security (`AuthenticationProvider` implementations) — same idea, different spec/ecosystem
- Scopes ≈ conceptually similar to Java's fine-grained permission annotations, or AWS IAM policy scoping — narrow, composable grants of access
- Token blocklist for revocation ≈ a server-side session invalidation table, the "stateful" compromise layered on top of otherwise-stateless JWTs

---
