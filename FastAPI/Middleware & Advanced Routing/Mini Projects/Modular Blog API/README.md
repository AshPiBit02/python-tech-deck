# Modular Blog API

A small blogging platform API split into independent resource
routers, with global middleware for logging, request tracing, and a
basic bot/empty-client gate.

## Structure

```
modular_blog_api/
├── main.py                  # entrypoint: middleware + router wiring
├── middleware.py             # logging, User-Agent gate, X-Request-ID
├── models.py                  # shared Pydantic schemas
└── routers/
    ├── users.py               # /users        (no dependencies)
    ├── posts.py                # /posts        (depends on users)
    └── comments.py               # /posts/{id}/comments (depends on posts + users)
```

## Middleware behavior (`middleware.py`)

Every request passes through `RequestLoggingMiddleware` before
reaching any route:

1. **User-Agent gate** — requests with no `User-Agent` header are
   rejected immediately with `400 {"detail": "User-Agent header is required"}`,
   before any route logic runs.
2. **Timing + logging** — successful requests are timed and logged as:
   ```
   GET /posts -> 200 (3.42ms)
   POST /posts -> 201 (5.10ms)
   ```
3. **`X-Request-ID` header** — every response (including the 400 from
   step 1's downstream handlers, but not the blocked ones themselves)
   gets a unique UUID in `X-Request-ID`, useful for correlating a
   client-reported issue with a specific server log line.

## Running it

```bash
pip install fastapi uvicorn pydantic[email]
uvicorn main:app --reload
```

Docs: `http://localhost:8000/docs`

## Try it out

```bash
# Missing User-Agent -> blocked by middleware (curl sets one by default,
# so force it off to see the 400):
curl -A "" http://localhost:8000/posts
# {"detail":"User-Agent header is required"}

# Create a user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com"}'
# {"id":1,"username":"alice","email":"alice@example.com"}

# Create a post by that user
curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello World", "content": "First post!", "author_id": 1}'
# {"id":1,"title":"Hello World","content":"First post!","author_id":1,"created_at":"..."}

# Comment on the post
curl -X POST http://localhost:8000/posts/1/comments/ \
  -H "Content-Type: application/json" \
  -d '{"content": "Nice post!", "author_id": 1}'
# {"id":1,"content":"Nice post!","author_id":1,"post_id":1,"created_at":"..."}

# List comments on the post
curl http://localhost:8000/posts/1/comments/

# Inspect response headers for X-Request-ID
curl -i http://localhost:8000/posts | grep -i x-request-id
```

## Notes

- Data is stored in in-memory dicts per router (`_users_db`,
  `_posts_db`, `_comments_db`) — restart clears everything. Swap for a
  real database (SQLAlchemy, etc.) without changing the router shape.
- `posts.py` and `comments.py` import the in-memory store from the
  router they depend on (`users.py`, `posts.py`) to validate foreign
  keys (`author_id`, `post_id`) at request time — a lightweight stand-in
  for the DB foreign-key checks a real persistence layer would do.
- Comments are nested under posts (`/posts/{post_id}/comments`)
  rather than flat (`/comments`), since a comment never makes sense
  outside the context of its post.