# JWT Structure & Creation — Detailed Reference

Covers: token anatomy, `python-jose`'s create/decode functions piece by piece,
attack vectors the library guards against, and refresh tokens.

---

## 1. What a JWT Actually Is

A JSON Web Token is three base64url-encoded segments joined by dots:

```
header.payload.signature
```

Example (decoded conceptually):
```
Header:    {"alg": "HS256", "typ": "JWT"}
Payload:   {"sub": "alice@example.com", "exp": 1735689600}
Signature: <computed over header + payload, using SECRET_KEY>
```

| Part | Purpose |
|---|---|
| Header | States the signing algorithm used (e.g. `HS256`) |
| Payload (claims) | The actual data — `sub` (subject/identity), `exp` (expiry), and any custom claims you add |
| Signature | Proves the token wasn't tampered with — computed from header+payload using a secret only the server knows |

### Critical: the payload is encoded, not encrypted

Anyone can base64-**decode** a JWT and read its payload — paste any JWT into [jwt.io](https://jwt.io) to see this directly, no key required. The signature only prevents **tampering**; it does not hide the contents.

**Rule: never put sensitive data (passwords, secrets, credit card numbers) inside a JWT payload.** Only put data that's safe to be publicly readable — a user ID, an email, a role, an expiry timestamp.

---

## 2. Creating a Token

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### `data.copy()` — why copy instead of mutating directly

```python
to_encode = data.copy()   # NOT: to_encode = data
```
Without copying, `to_encode.update({"exp": expire})` would mutate the **caller's original dict** too — the same class of surprise as Python's mutable-default-argument pitfall. Copying keeps the caller's original claims dict untouched.

**Note:** `.copy()` is a **shallow** copy — if `data` ever contained nested mutable structures (a list/dict inside it), those inner objects wouldn't be protected from mutation. For flat claims like `{"sub": email}`, this doesn't matter.

### `jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)`

Builds the header, encodes the payload, computes the signature, and joins all three into the final token string. The signing math is handled entirely by the library — never hand-build a JWT string yourself.

---

## 3. Decoding and Verifying a Token

```python
def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

### `algorithms=[ALGORITHM]` — why a list, and why it matters for security

This is deliberately a list, and deliberately restrictive. It tells `jwt.decode`: *"only accept tokens whose header claims one of these algorithms — reject anything else."*

**The attack this prevents:** a malicious actor could hand-craft a token whose header claims a different (weaker, or even `"none"`) algorithm, hoping a naive verifier skips proper signature checking. By explicitly whitelisting `algorithms=[ALGORITHM]`, `jose` refuses to even attempt verification with anything not on that list, regardless of what the token's own header claims.

### What actually triggers `JWTError`

A single exception type covers all of these:
- Signature doesn't match (token was tampered with, or signed with a different key)
- Token is malformed (not valid JWT structure at all)
- Token has **expired** (`exp` claim is in the past)

One `except JWTError` block correctly handles all three — practically, they all mean the same thing to your application: *this token cannot be trusted, reject the request.*

### Expiry checking is automatic

You never manually compare `payload["exp"]` against the current time — `jwt.decode` does this internally and raises `JWTError` on its own if the token has expired.

---

## 4. `SECRET_KEY` — Why It's the Single Most Important Value

Anyone possessing `SECRET_KEY` can forge a **valid** signature for *any* payload — including impersonating any user by crafting `{"sub": "someone_else@example.com"}` and signing it themselves. This is why:
- It lives in `.env`, never hardcoded, never committed to git
- It should be a long, random string — not a memorable word or phrase
- If it ever leaks, every issued token must be considered compromised, and the key must be rotated (which also invalidates *every* currently valid token, forcing all users to re-login — a real operational cost, worth keeping in mind)

---

## 5. Refresh Tokens — Why Access Tokens Alone Aren't Enough

### The problem access tokens alone create

Access tokens are typically **short-lived** (15–30 minutes is common) — this is deliberate: if one leaks (stolen, intercepted), the damage window is small. But short expiry means users would otherwise have to **re-login constantly**, which is a poor experience.

### The solution: two tokens, two different lifetimes

| Token | Lifetime | Purpose |
|---|---|---|
| **Access token** | Short (minutes) | Sent on every API request, proves identity for that request |
| **Refresh token** | Long (days/weeks) | Used *only* to obtain a new access token, never sent on regular API calls |

### The flow

1. Login → server issues **both** an access token and a refresh token
2. Client uses the access token normally for API requests
3. When the access token **expires**, instead of forcing a full re-login, the client sends its refresh token to a dedicated `/refresh` endpoint
4. Server verifies the refresh token, and if valid, issues a **new** access token (and often a new refresh token too)
5. This repeats until the refresh token itself expires (or is revoked) — at which point the user must log in again for real

### Why not just make the access token long-lived instead?

A stolen long-lived access token is usable for its entire (long) lifetime with no way to stop it except waiting it out or invalidating your whole secret key (affecting everyone). A **refresh token** system lets you:
- Keep access tokens short (limits blast radius of a leak)
- **Revoke** a specific refresh token (e.g. stored in a DB, checked against a blocklist) without affecting every other user's session — something a pure stateless JWT can't do on its own
- Detect suspicious reuse (if a refresh token is used twice from different locations, that's a strong signal of theft)

### A minimal refresh token implementation, conceptually

```python
def create_refresh_token(data: dict) -> str:
    return create_access_token(data, expires_delta=timedelta(days=7))   # same mechanism, longer expiry


@router.post("/refresh")
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Refresh token invalid or expired")

    email = payload.get("sub")
    new_access_token = create_access_token({"sub": email})
    return {"access_token": new_access_token, "token_type": "bearer"}
```

**Note:** a production-grade refresh token system typically also stores issued refresh tokens in the database (so they can be individually revoked, e.g. on logout or suspected theft) — a pure stateless refresh token (just another JWT, as shown above) can't be revoked early, only allowed to naturally expire. This is a deliberate simplification worth knowing about, not a full production pattern.

---

## 6. Testing Tampering and Expiry 

```python
# tampering
token = create_access_token({"sub": "alice@example.com"})
tampered = token[:-5] + "aaaaa"
decode_access_token(tampered)   # raises — signature no longer matches

# expiry
short_lived = create_access_token({"sub": "alice@example.com"}, expires_delta=timedelta(seconds=1))
import time
time.sleep(2)
decode_access_token(short_lived)   # raises — token expired
```

Both failures surface through the same `JWTError`/`HTTPException` path — worth confirming this yourself rather than taking it on faith.

---

## 📌 Notes for Background
- JWT signature verification ≈ digital signatures in cryptography generally, or how HTTPS certificates establish trust
- Access + refresh token pattern ≈ similar in spirit to how OAuth2 providers (Google, GitHub login) work — short-lived access tokens, longer-lived refresh tokens, standard industry pattern
- The `algorithms=[...]` whitelist restriction ≈ a defensive allowlist pattern, similar to input validation allowlists elsewhere in security-conscious code

---
