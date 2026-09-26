"""
PROBLEM: You add a route like GET /users/me, but it's registered after Get /users/{user_id}.
Now requests to /users/me never reach your "me" handler - FastAPI matches /users/{user_id} 
first and tries to treat "me" as a user_id, usually crashing with a 422(int parsing error)
or returning the wrong data.

SOLUTION: Register specific/static path before dynamic/parameterized paths on the same router.
This file shows the bug and the fix side-by-side on two routers so both behavior can be compared 
directly.
"""

from fastapi import FastAPI,APIRouter
app=FastAPI(title="Route Ordering Demo")

buggy_router=APIRouter(prefix="/buggy/users",tags=["Buggy"])

@buggy_router.get("/{user_id}")
def get_user_buggy(user_id:int):
    return {"user_id":user_id,"type":"Naive"}

@buggy_router.get("/me")
def get_current_user_buggy():
    return {"user_id":277,"type":"Admin"}

fixed_router=APIRouter(prefix="/fixed/users",tags=["Fixed"])

@fixed_router.get("/me")
def get_current_user_fixed():
    return {"user_id":277,"type":"Admin"}

@fixed_router.get("/{user_id}")
def get_user_buggy(user_id:int):
    return {"user_id":user_id,"type":"Naive"}

app.include_router(buggy_router)
app.include_router(fixed_router)
