# HTTPS & CORS in FastAPI

HTTPS and CORS are two separate security mechanisms that are frequently mentioned together in backend learning material, but they solve entirely different problems, are enforced by different parties, and operate at different layers of the stack. This document treats each in depth, then clarifies precisely how they relate — and don't relate — to one another.

---

# Part 1 — HTTPS

## The Problem It Solves

Plain HTTP transmits data as unencrypted text over the network. Any intermediary positioned between a client and a server — a public Wi-Fi access point, an ISP, a compromised router, a malicious proxy — can read every byte passing through, including login credentials submitted in a form, JWT access and refresh tokens sent in an `Authorization` header, and the full contents of every request and response body.

**HTTPS** is HTTP layered on top of **TLS** (Transport Layer Security, the modern successor to SSL). It provides three guarantees:

1. **Confidentiality** — traffic is encrypted, so an eavesdropper sees only ciphertext, not the actual request/response content
2. **Integrity** — traffic cannot be silently modified in transit without detection
3. **Authentication** — the client can verify the server is actually who it claims to be, via a certificate issued by a trusted Certificate Authority (CA)

## Why It Matters for Token-Based Authentication Specifically

A bearer token — the kind produced by JWT-based login flows — grants access to whoever physically possesses the token string, with no additional proof required. If such a token travels over plain HTTP, it is exposed in full to anyone intercepting the connection. Every layer of access control built around that token — scope checks, role checks, expiry checks — becomes irrelevant once the token itself has been intercepted and can be replayed by an attacker. HTTPS is what protects a token *in transit*, before it ever reaches server-side validation logic.

## Where HTTPS Termination Actually Happens

A common misconception is that a FastAPI application itself must be configured with TLS certificates in production. In practice, most deployments follow this structure:

```
Client  →  HTTPS  →  Reverse Proxy (Nginx, Caddy, or a cloud load balancer)  →  HTTP  →  Uvicorn / FastAPI
```

The reverse proxy holds the TLS certificate and performs encryption and decryption. Traffic between the proxy and the application server, occurring inside a private network boundary, is frequently plain HTTP, since it never travels across an untrusted network. This is why application code rarely contains explicit certificate-handling logic — HTTPS termination is treated as an infrastructure and deployment concern rather than an application-layer concern.

For local development and testing, Uvicorn can serve HTTPS directly:
```bash
uvicorn main:app --ssl-keyfile ./key.pem --ssl-certfile ./cert.pem
```
A self-signed certificate generated for this purpose will cause browsers to display a "not trusted" warning — this is expected, since self-signed certificates are not backed by a recognized CA, and is not a concern for local testing.

## Obtaining a Production Certificate

- **Let's Encrypt** is a free, widely used, automated certificate authority; tools such as Certbot handle issuance and renewal (Let's Encrypt certificates expire every 90 days and require automated renewal).
- Most cloud hosting platforms (Render, Railway, AWS, GCP, and similar) provision HTTPS automatically once a custom domain is attached, removing the need to manage certificates manually in most cases.

## Key Points to Retain

- HTTPS protects data **in transit only**. It does not protect data at rest (an unencrypted database still exposes plaintext data if compromised directly) and does not protect the client environment itself (a compromised browser extension can still read tokens after decryption has already occurred on the client side).
- Cookies and headers can be marked as `Secure`, meaning a browser will refuse to transmit them over plain HTTP under any circumstances, sending them only over HTTPS. This becomes relevant if authentication tokens are ever moved from `Authorization` headers into cookies.
- HTTPS setup is largely a deployment decision rather than an extensive coding task, but understanding why it matters for any system carrying credentials or tokens — and how to test it locally — remains an essential skill.

---

# Part 2 — CORS

## The Problem It Solves

**CORS (Cross-Origin Resource Sharing)** is a browser-enforced security mechanism, not a server-side defense against attackers directly. It exists because browsers, by default, prevent JavaScript running on one website from making requests to a different website's API. This default restriction exists to stop a malicious website from silently using a user's active session on another site (for example, a bank or email provider) without the user's knowledge.

An **origin** consists of scheme, domain, and port together. The following are all considered distinct origins from one another:
```
https://example.com
https://example.com:8000        (different port)
http://example.com              (different scheme)
https://api.example.com         (different subdomain)
```

## A Concrete Illustration

Consider a frontend hosted at `https://example.com` and a backend API hosted at `https://api.example.com`. When a browser loads the frontend and its JavaScript attempts:
```js
fetch("https://api.example.com/notes", { headers: { Authorization: `Bearer ${token}` } })
```
the browser treats this as a cross-origin request, since `example.com` and `api.example.com` are different origins — even though both belong to the same organization. Unless the backend explicitly permits requests from `https://example.com`, the browser will block the response from reaching the frontend's JavaScript entirely.

## How the Preflight Negotiation Works

For requests considered "non-simple" (such as those carrying custom headers like `Authorization`, or using methods beyond basic `GET`/`POST`), the browser automatically sends a **preflight** request before the real one:
```
OPTIONS /notes
Origin: https://example.com
Access-Control-Request-Method: GET
Access-Control-Request-Headers: authorization
```
The server must respond with headers indicating which origins, methods, and headers are permitted. Only if this preflight succeeds does the browser proceed to send the actual request. This entire exchange is handled transparently by FastAPI's CORS middleware — route handlers never need to implement an `OPTIONS` method manually.

## Configuring CORS in FastAPI

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
```

- **`allow_origins`** — the exact list of origins permitted to call the API. Using `["*"]` permits any website whatsoever to call the API, which is acceptable for a fully public, unauthenticated API but is dangerous for an API that relies on cookies or session state, since it removes the very protection CORS is designed to provide.
- **`allow_methods` / `allow_headers`** — which HTTP methods and custom headers a browser is permitted to send cross-origin. Wildcards (`["*"]`) are possible for either, though many teams prefer listing values explicitly for clarity and auditability.
- **`allow_credentials=True`** — required whenever a frontend sends cookies or relies on `Authorization` headers cross-origin. A critical restriction applies here: when this is set to `True`, `allow_origins` **cannot** simultaneously be `["*"]`; browsers reject that combination outright, since "any origin combined with credentials" is precisely the scenario CORS exists to prevent. Specific origins must be listed instead.

## Key Points to Retain

- CORS is enforced **by browsers**, not by the server itself, and not by tools such as `curl` or Postman. This is why a request blocked in a browser's developer console frequently succeeds without issue when tested through curl or Postman — the restriction never applied outside a browser context in the first place. This distinction accounts for a very common source of confusion: an API that "works in Postman but not from the frontend" is almost always a CORS misconfiguration rather than a defect in the API itself.
- CORS provides **no protection against non-browser clients**. A script executed outside a browser environment (a Python script using `requests` or `httpx`, for instance) simply ignores CORS headers entirely, since no browser is present to enforce the restriction. CORS protects specifically against browser-based cross-origin misuse; genuine access control still depends on server-side authentication and authorization (JWT validation, scope checks, role checks).
- A frequent mistake involves setting `allow_origins=["*"]` during development for convenience, then failing to restrict it before production deployment. This leaves the API callable from any website's JavaScript — a more significant concern for systems relying on cookie-based session state than for pure Bearer-token APIs (since a malicious site still cannot read another site's stored token), but tightening this deliberately before production remains good practice regardless.

---

# How HTTPS and CORS Relate

- **HTTPS** protects data in transit between any client and server, regardless of whether that client is a browser, a mobile app, or a server-to-server integration.
- **CORS** governs which websites' JavaScript, running inside a user's browser, is permitted to call a given API.

The two are independent and can exist without one another: an HTTP-only API with strict CORS configuration is possible (though insecure, since traffic remains unencrypted), as is an HTTPS-secured API with a wildcard CORS policy (functional, but permissive). In production systems, both are typically configured deliberately and independently, since each addresses a distinct category of risk.