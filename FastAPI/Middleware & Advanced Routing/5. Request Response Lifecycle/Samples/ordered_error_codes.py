"""
PROBLEM: A frontend team wants to know: if a request gets a 403, does that
guarantee the token was valid? They want different UI behavior for "invalid
token" (401, ask to log in again) vs "valid token, wrong role" (403, show a
permission-denied message) -- and want that distinction to be reliable, not
just usually-true.

SOLUTION: Make require_admin DEPEND on get_current_user, so FastAPI's own
dependency resolution gurantees get_current_user always runs (and can raise
401) before require_admin's role check can ever raise 403.
"""

from fastapi import FastAPI,Depends,HTTPException,Header

app=FastAPI(title="Ordered Error Codes Demo")

FAKE_TOKENS={
    "user-token":{"username":"alice","role":"user"},
    "admin-token":{"username":"alita","role":"admin"},
}

def get_current_user(authorization: str=Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401,detail="Invalid or expired token")

    token=authorization.removeprefix("Bearer ").strip()
    user=FAKE_TOKENS.get(token)
    if not user:
        raise HTTPException(status_code=401,detail="Invalid or expired token")

    return user

