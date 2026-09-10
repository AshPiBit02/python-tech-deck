# OAuth2 Scopes in FastAPI

## The Problem Scopes Solve

A basic JWT auth setup answers one question: **"Is this a valid, logged-in user, and what's their role?"** You typically check something like `role == "admin"` — binary-ish, coarse-grained. Every route an admin can access, *every* admin token can access. There's no way to issue a token that says "admin, but only allowed to do this one specific thing."

**Scopes answer a different question: "What is *this particular token* allowed to do?"** — separate from who the user fundamentally is.

## The Core Idea

Scope is a **list of permission strings attached to the token itself**, not to the user record in the database.

The user still has a role/identity in the `USERS` table — that doesn't change. But when a token is issued, it's additionally stamped with something like:

```json
"scopes": ["notes:read", "notes:write"]
```

Every protected route then declares: *"to call me, your token must carry scope X."* The check isn't "is this user an admin" — it's "does this specific token have this specific permission."

## Why Not Just Use `role` for Everything?

1. **Same user, different tokens, different power.**
   A user could log in from a "read-only dashboard" client and get a token with only `notes:read`, while logging in from the main app gets full scopes. Same person, same role, deliberately weaker token for a specific context.

2. **Delegated / third-party access.**
   If another app ever needs to act on behalf of a user (OAuth-style "Login with X"), you'd want to hand it a token limited to exactly what it needs — never the user's full role power. This is literally what OAuth2 scopes were designed for.

3. **Fine granularity without exploding the role list.**
   Instead of inventing `admin`, `super_admin`, `read_only_admin`, `notes_admin`... keep one role and combine flags: `["notes:read", "notes:write"]` vs `["notes:read", "notes:write", "notes:delete"]`.

## Two Moments Where Scope Matters

- **At login / token-issue time** — the server decides which scopes to actually embed in the token (usually derived from the user's role, but the server has final say — never trust client-requested scopes blindly).
- **At request time** — each route declares "I require scope Y"; the check is: *is Y present in the list embedded in this token's payload?*

## Where It Lives Technically

Since tokens are JWTs, scope is just another field in the payload dict — sits alongside `sub`, `role`, `exp`, `type`. No new infrastructure, no new library. It's a **convention for what goes into the token and how it's checked**, not a new mechanism.

## Key Building Blocks (FastAPI)

| Component | Purpose |
|---|---|
| `OAuth2PasswordBearer(tokenUrl="token", scopes={...})` | Declares available scopes; renders as checkboxes in Swagger's 🔒 modal |
| `SecurityScopes` | Injected into a dependency to access the scopes *required* by the calling route |
| `Security(dependency, scopes=["..."])` | Like `Depends()`, but also passes required scopes into the dependency for checking. A `Depends` subclass — if the dependency doesn't accept a `SecurityScopes` param, scopes are simply ignored |
| `form_data.scopes` | Scopes *requested* by the client at login — must be filtered against what the user is actually allowed before granting |

## Essential Things to Remember

- **Scope requested ≠ scope granted.** The client asks; the server decides what to actually issue based on real user permissions.
- **Role = who the user is. Scope = what this particular token is allowed to do right now.** They're related (scopes are usually derived from role) but not the same thing.
- Scope checks happen **per route**, via whatever list is embedded in that specific token — not by re-checking the user's role in the database each time.