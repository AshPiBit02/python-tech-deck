"""
PROBLEM: You have 15 admin endpoints. Repeating 'Depends(verify_admin_token)'
on every single one is error-prone. One day someone adds endpoint #16 and forgets
it, leaving an unprotected admin route in production.

SOLUTION: Attach the auth check once, at the router level, so it's structurally
impossible to add a route to this router without it being protected.
"""
from fastapi import FastAPI,APIRouter,Header,Depends,HTTPException,status

app=FastAPI(title="Protected Admin Router Demo")
ADMIN_KEY="secret587"

def verify_admin_token(x_admin_key:str|None=Header(default=None)):
    if x_admin_key!=ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Bad or missing admin key")

admin_router=APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin_token)],
)

@admin_router.get("/dashboard")
def dashboard():
    return {"active_users":863,"revenue_today":8692.36}

@admin_router.get("/users")
def list_all_users():
    return [
        {"id":1,"name":"banana"},
        {"id":2,"name":"big tie"},
        {"id":3,"name":"choyie"}
    ]

@admin_router.delete("/{user_id}")
def delete_user(user_id:int):
    return {"message":f"User with id {user_id} deleted."}

app.include_router(admin_router)