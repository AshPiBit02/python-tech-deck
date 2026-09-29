# The `Request` Object — Advanced Usage

Briefly, as groundwork: `Request` is the object representing raw, incoming HTTP data — headers, client info, the URL, the body — before FastAPI has parsed any of it into typed parameters. Routes normally never need it directly, since FastAPI's parameter system (path params, query params, Pydantic body models, `Header(...)`) already extracts everything a route typically needs. This document focuses on *why* and *when* reaching for `Request` directly is actually necessary, since overusing it defeats the type-safety and auto-documentation that make FastAPI's normal parameter system valuable in the first place.

## Why `Request` Exists Separately From Normal Parameters

FastAPI's usual parameter declarations (`user_id: int`, `email: EmailStr = Header(...)`, a Pydantic body model) are all built *on top of* the underlying `Request` object — they are FastAPI parsing, validating, and extracting specific pieces of it for convenience. `Request` itself is the unprocessed layer beneath all of that, and reaching for it directly means opting out of that convenience — no automatic validation, no automatic OpenAPI documentation generation for whatever's read from it, no automatic type coercion.

```python
from fastapi import Request

@app.get("/debug")
async def debug_route(request: Request):
    return {
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host,
        "headers": dict(request.headers),
    }
```

This is the same object already used inside middleware throughout this phase (`async def dispatch(self, request, call_next)`), but it is equally accessible as a route parameter directly, simply by type-hinting a parameter as `Request`.

## When Reaching for `Request` Directly Is Actually Justified

Since FastAPI's structured parameter system covers the overwhelming majority of real needs, deliberately reaching for `Request` should be a considered choice, not a default habit. It's genuinely needed in a few recurring situations:

### 1. Inspecting headers whose names aren't known in advance

`Header(...)` requires declaring a specific, fixed header name ahead of time. Some scenarios require iterating over *all* headers a client sent, without knowing which ones in advance — for instance, forwarding every header from an incoming request to a downstream service in a proxy-like route:

```python
@app.api_route("/proxy/{path:path}", methods=["GET", "POST"])
async def proxy_request(request: Request, path: str):
    headers = dict(request.headers)
    body = await request.body()
    # forward `headers` and `body` to another service...
```

### 2. Verifying a raw, unparsed request body — signature verification

Some integrations (webhook providers, payment gateways) sign the *exact raw bytes* of a request body and expect the receiving server to verify that signature before trusting the payload. If FastAPI parses the body into a Pydantic model first, the original raw bytes (whitespace, key ordering, exact formatting) may no longer be recoverable in the exact form the sender signed — verification requires the untouched raw body:

```python
import hmac
import hashlib

@app.post("/webhooks/payment")
async def payment_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("x-signature", "")

    expected = hmac.new(WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()   # safe to parse AFTER verifying the raw bytes
    ...
```

This is a case where reaching for `Request` isn't a shortcut — it's the *only* correct way to get access to the exact bytes needed for the security check.

### 3. Logic that genuinely applies across many/all routes, inside middleware

As already covered throughout this phase, middleware receives `request` directly because it operates before any route-specific parameter parsing has happened — this is `Request`'s most natural home, not an edge case.

### 4. Accessing values placed on `request.state` earlier in the pipeline

`request.state` is a general-purpose, per-request storage location — anything set on it by middleware or an early dependency becomes readable by anything later in that same request's lifecycle, including inside the eventual route function:

```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    return await call_next(request)

@app.get("/orders")
def list_orders(request: Request):
    # reading back what middleware attached earlier in this SAME request's lifecycle
    return {"request_id": request.state.request_id, "orders": [...]}
```

## The Cost of Reaching for `Request` Too Often

Every time a value is read manually off `Request` instead of through a normal typed parameter, three things are lost simultaneously: automatic validation (a missing or malformed value fails silently or requires manual checking, rather than FastAPI rejecting it with a clear `422` automatically), automatic OpenAPI documentation (Swagger's docs won't show that this route expects a particular header or field, since FastAPI only documents what it recognizes through its own parameter system), and IDE/type-checker support (`request.headers.get("x-custom-header")` returns an untyped, possibly-`None` string, versus a properly typed, validated parameter). Reaching for `Request` should be reserved for the situations above, where the normal parameter system genuinely cannot express what's needed — not used as a general-purpose shortcut to avoid declaring parameters properly.

## `Request` vs the Objects Built From It

| | What it gives access to | When it's the right tool |
|---|---|---|
| Typed parameters (path/query/`Header`/Pydantic body) | A specific, named, validated piece of the request | The overwhelming majority of normal route needs |
| `Request` | Everything, raw and unparsed | Dynamic/unknown headers, raw-body signature checks, middleware, reading `request.state` |
| `request.state` | Custom values attached earlier in the same request's lifecycle | Passing data forward from middleware/early dependencies to later code, within one request |

## Key Points to Retain

- `Request` is the unprocessed layer beneath FastAPI's normal parameter system — reaching for it directly means opting out of automatic validation, documentation, and typing that the normal system provides.
- Legitimate reasons to use `Request` directly include inspecting headers not known in advance, verifying a raw request body's signature before parsing it, middleware (which receives it natively), and reading values placed on `request.state` earlier in the same request's lifecycle.
- Raw-body signature verification is a case where `Request` isn't a convenience shortcut but the only correct approach, since parsing the body first can lose the exact byte sequence a sender originally signed.
- Defaulting to `Request` out of habit, rather than declaring specific typed parameters, discards the validation, documentation, and type-safety benefits that are otherwise automatic in FastAPI.