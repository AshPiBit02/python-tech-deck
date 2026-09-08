# Phase 6 — Authentication & Security: Basics

Reference notes for JWT-based auth: password hashing, token structure, creation/
verification, and the FastAPI-specific pieces that wire it all together.

---

## 1. The Two Questions Auth Answers

Keep these conceptually separate from the start — most confusion in this phase comes from blending them:

- **Authentication** — "who are you?" — proving identity, typically via password
- **Authorization** — "what are you allowed to do?" — permissions, once identity is known (e.g. admin vs. regular customer, RBAC in Phase 6.3)

Everything in this file is about **authentication**. Authorization (role checks) builds on top of it later.

---

## 2. Why Existing `key_validation` Pattern Isn't Real Auth

Across Enterprise, Wallet, and Banking projects, "secure" routes have used a single shared secret header:
```python
def key_validation(key: str = Header(...)):
    if key != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid secret key!")
```
This proves **"you know a secret"**, not **"you are a specific person"**. Anyone holding that one string can act as anyone. Real auth needs each user to have their **own** provable identity — that's what the rest of this file builds.

---

## 3. Password Hashing — Never Store Passwords Directly

### Why hashing, not encryption
- **Encryption** is reversible (two-way) — meant for data you need to read back later
- **Hashing** is one-way — meant for data you only ever need to *verify*, never retrieve

A password should be **hashed**, never encrypted — even you, the developer, should be mathematically unable to recover the original password from what's stored in the database.

### `passlib` + `bcrypt`

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

```python
hashed = hash_password("mysecret123")
print(hashed)
# '$2b$12$KIXQ4z9F8...' — long, irreversible string; different every time you hash
# the SAME password (bcrypt includes a random "salt")

verify_password("mysecret123", hashed)   # True
verify_password("wrongpass", hashed)      # False
```

### Why `bcrypt` specifically

`bcrypt` is deliberately **slow** — this is a feature, not a flaw. If someone steals your database's hashed passwords, `bcrypt`'s slowness makes brute-forcing millions of guesses per second computationally impractical. Fast hash algorithms (like plain SHA-256) are actually a poor choice for passwords specifically, because their speed helps an attacker, not you.

### The "salt" — why identical passwords produce different hashes

Two users with the same password `"password123"` will get **different** stored hashes — `bcrypt` automatically mixes in a random value (the "salt") before hashing, so identical passwords never produce identical stored hashes. This defeats precomputed "rainbow table" attacks. `passlib` handles this for you automatically; `verify_password` still works correctly because the salt is stored alongside the hash itself.

---

## 4. JWT Structure — What a Token Actually Is

A JWT (JSON Web Token) is three base64-encoded segments joined by dots:

```
header.payload.signature
```

Example (decoded conceptually):
```
Header:    {"alg": "HS256", "typ": "JWT"}
Payload:   {"sub": "alice@example.com", "exp": 1735689600}
Signature: <cryptographic signature over header+payload, using your SECRET_KEY>
```

### What each part does

- **Header** — states which signing algorithm was used (commonly `HS256`)
- **Payload (claims)** — the actual data: `sub` (subject — usually a user identifier), `exp` (expiry, as a Unix timestamp), and anything else you choose to add
- **Signature** — proves the token wasn't tampered with. Computed using your server's `SECRET_KEY`. If anyone alters the header or payload, the signature no longer matches, and verification fails

### Critical: the payload is NOT encrypted, only signed

Anyone can base64-**decode** a JWT and read its payload in plain text — try pasting any JWT into [jwt.io](https://jwt.io) to see this directly. The signature only prevents **tampering**, not **reading**.

**Rule: never put sensitive data (passwords, secrets) in a JWT payload.** Only put things that are safe to be publicly readable — a user ID, an email, a role, an expiry time.

---

## 5. Creating and Verifying Tokens — `python-jose`

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = settings.secret_key   # from .env — never hardcode this
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

```python
token = create_access_token({"sub": "alice@example.com"})
print(token)
# eyJhbGciOiJIUzI1NiIs...

payload = decode_access_token(token)
print(payload)
# {'sub': 'alice@example.com', 'exp': 1735689600}
```

### Expiry is handled automatically

`jwt.decode` checks the `exp` claim internally — if the token has expired, it raises `JWTError` on its own. You never need to manually compare timestamps yourself.

### Why `SECRET_KEY` must stay secret

Anyone who has your `SECRET_KEY` can forge a **valid** signature for *any* payload they want — including impersonating any user. This is exactly why it lives in `.env`, never hardcoded, never committed to git — same handling as your database password.

---

## 6. `OAuth2PasswordBearer` — Telling FastAPI Where the Token Lives

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

This isn't magic — it's a small, declarative piece telling FastAPI: *"expect an `Authorization: Bearer <token>` header on protected routes, and extract just the token substring for me."* `tokenUrl="token"` tells Swagger UI's "Authorize" button which route to actually call to *get* a token in the first place.

### Using it as a dependency to identify the current user

```python
def get_current_customer(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Customer:
    payload = decode_access_token(token)
    email = payload.get("sub")
    customer = get_customer_by_email(db, email)
    if customer is None:
        raise HTTPException(status_code=401, detail="Customer not found")
    return customer
```

This is the direct, real replacement for `key_validation` — except now it identifies **which** specific user is making the request, not just "someone who knows a shared secret."

### Why this avoids the earlier Swagger `authorization` header bug

Recall the earlier `422` bug where a header literally named `authorization` was mishandled by Swagger's reserved-field special-casing. `OAuth2PasswordBearer` is specifically built to integrate correctly with that exact Swagger mechanism — it's the intended, proper way to use the `Authorization` header, not a workaround.

---

## 7. The Login Flow — `OAuth2PasswordRequestForm`

```python
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

@router.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_email(db, form_data.username)   # "username" field holds the email
    if customer is None or not verify_password(form_data.password, customer.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": customer.email})
    return {"access_token": access_token, "token_type": "bearer"}
```

### Why `OAuth2PasswordRequestForm`, not a Pydantic body

This class expects **form-encoded** data (`username`/`password` fields) rather than JSON — matching the OAuth2 spec exactly. This specific shape is what makes Swagger's built-in "Authorize" button work seamlessly: clicking it presents a login form that submits directly in this expected format, no custom JSON body needed.

### The response shape is a convention, not arbitrary

```json
{"access_token": "eyJhbGc...", "token_type": "bearer"}
```
`token_type: "bearer"` tells the client how to use the token on subsequent requests: `Authorization: Bearer <access_token>`. This exact key name/value is expected by OAuth2-compliant clients (including Swagger UI itself).

---

## 8. Putting It Together — The Full Request Lifecycle

1. **Register** — client sends email + password → server hashes the password (`hash_password`) → stores the hash in `Customer.hashed_password`
2. **Login** (`POST /token`) — client sends email + password (form-encoded) → server verifies password against the stored hash (`verify_password`) → server issues a signed JWT (`create_access_token`) → client receives and stores this token
3. **Authenticated request** — client sends `Authorization: Bearer <token>` on every subsequent request → `oauth2_scheme` extracts the token → `decode_access_token` verifies the signature and expiry → `get_current_customer` looks up and returns the actual `Customer` object → route logic runs, now knowing exactly who's asking

---

## 📌 Notes for Background

- JWT signature verification ≈ digital signatures in general cryptography, or how HTTPS certificates establish trust — same underlying trust model, applied to a token instead of a website
- `bcrypt` password hashing ≈ conceptually the same as Java Spring Security's `BCryptPasswordEncoder` — same algorithm family, different language binding
- Stateless JWT auth ≈ a signed session cookie in any modern web framework — the token itself carries proof of identity; no server-side session table lookup is needed to verify a request
- `OAuth2PasswordBearer`/`OAuth2PasswordRequestForm` ≈ standardized "shapes" the OAuth2 spec defines, similar to how a fixed protocol format works in networking — using the spec's shape is what makes Swagger's tooling work out of the box, rather than something you built by hand

---
