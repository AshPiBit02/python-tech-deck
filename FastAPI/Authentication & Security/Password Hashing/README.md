# Password Hashing — Detailed Reference

Covers: why hashing (not encryption), `passlib`'s `CryptContext` piece by piece,
the salt mechanism, cost factor, alternative approaches, and common mistakes.

---

## 1. Why Hashing, Not Encryption

| | Encryption | Hashing |
|---|---|---|
| Direction | Two-way — can be decrypted back to original | One-way — cannot be reversed |
| Use case | Data you need to read back later | Data you only ever need to *verify*, never retrieve |
| Password fit | Wrong tool — original would be recoverable | Correct tool — original is never recoverable, even by you |

A password should be **hashed**, never encrypted. Even the developer/database admin should be mathematically unable to recover a user's original password from what's stored — this is the entire point.

---

## 2. `passlib.context.CryptContext` — Piece by Piece

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### `passlib.context` — the module
`passlib` is the whole hashing library; `context` is the specific sub-module providing `CryptContext`, the main tool actually used day-to-day.

### `CryptContext` — a configured hashing manager
Not a hash or a password itself — it's an object you configure **once** and reuse everywhere, similar in spirit to how `SessionLocal` is a configured factory reused across your app rather than reconfigured per call.

### `schemes=["bcrypt"]` — which algorithm(s) are allowed
A **list**, deliberately — supports multiple hashing schemes at once:
```python
schemes=["bcrypt", "sha256_crypt"]
```
Why list more than one? **Migration scenarios.** If an app previously used a weaker/older algorithm and later switched to `bcrypt`, listing both lets `CryptContext` still **verify** old hashes while only ever **creating new hashes** with the preferred (first-listed) scheme — no need to force-rehash every user overnight.

For a new project, `["bcrypt"]` alone is correct — no legacy scheme to support.

### `deprecated="auto"` — marking older schemes as due for upgrade
Only meaningful once **multiple** schemes are listed. `"auto"` means: treat every scheme except the first-listed one as deprecated. With only `bcrypt` listed, this has no visible effect today — but it means the code is already correctly future-proofed for the day a second scheme gets added, without needing to remember to set this later.

`pwd_context.needs_update(old_hash)` — checks whether a given hash was made with a deprecated scheme; typically used to silently rehash a user's password with the new scheme the next time they log in successfully.

### `.hash(password)` — produces a new hash
```python
pwd_context.hash(password)
```
Takes a plain string, returns the full hash string (salt embedded inside it). Always uses the **first** scheme in the list.

### `.verify(plain, hashed)` — checks a password against a stored hash
```python
pwd_context.verify(plain_password, hashed_password)
```
Extracts the salt embedded in `hashed_password`, recomputes using the same salt + whichever scheme that hash was made with, and compares. Returns `True`/`False`. This is the **only** correct way to check a password — never manually re-hash and compare with `==`.

---

## 3. The Salt — Why Identical Passwords Produce Different Hashes

```python
h1 = hash_password("mypassword")
h2 = hash_password("mypassword")
# h1 != h2, even though the input is identical
```

`bcrypt` generates a random **salt** each time it hashes, mixing it into the computation before hashing. The salt is embedded directly in the output string:

```
$2b$12$KIXQ4z9F8vN3.../hash
 │   │  └────┬────┘└──┬──┘
 │   │       │         └── the actual hash output
 │   │       └── the salt, embedded in the string itself
 │   └── cost factor (rounds)
 └── bcrypt version identifier
```

Because the salt is stored *inside* the hash string, `verify_password` never needs the salt supplied separately — `.verify()` extracts it automatically and recomputes to check for a match.

### Why the salt matters — the actual security payoff

**Without a salt:** two users with the same password get the *identical* stored hash. An attacker who steals the database could precompute one giant lookup table ("rainbow table") mapping common passwords → hashes, and instantly crack every user who reused a common password.

**With a salt:** identical passwords produce completely different stored hashes. A precomputed rainbow table becomes useless — the attacker would need a separate table per possible salt value, which is computationally infeasible.

---

## 4. Cost Factor (Rounds) — The Speed/Security Tradeoff

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
```

Controls how many times the hashing computation repeats internally.
- **Higher rounds** → slower to compute → harder to brute-force, but also slower for your server to verify logins
- **Lower rounds** → faster, but weaker against brute-force attacks

`12` is a widely-used, reasonable default as of now. This is a deliberate, tunable security-vs-performance decision, not an arbitrary number.

---

## 5. Alternative Approach — Raw `bcrypt`, Without `passlib`

```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

**When to use `passlib` (recommended):** higher-level wrapper, supports multiple schemes through one consistent interface, handles `str`↔`bytes` encoding automatically — less room for mistakes.

**When to use raw `bcrypt` directly:** only if you specifically want one fewer dependency and are comfortable managing `.encode()`/`.decode()` calls yourself — a common source of subtle bugs for newcomers (forgetting `.encode("utf-8")` raises a `TypeError`, since `bcrypt` expects `bytes`, not `str`).

**Recommendation:** stick with `passlib` — it's the more common convention in FastAPI projects, and the abstraction genuinely reduces error surface.

---

## 6. Common Mistakes to Avoid

1. **Truncation limit** — `bcrypt` silently ignores any characters beyond **72 bytes** of input. Rarely an issue in practice, but it's a real limit of the algorithm, not a bug in your code.
2. **Never compare hashes with `==`** — always use `.verify()`. Since salts differ per hash, `stored_hash == hash_password(input)` is almost always `False` even for the *correct* password.
3. **Never log or print a plaintext password**, even temporarily for debugging — once a password touches a log file, treat it as compromised if that log is ever exposed.

---
