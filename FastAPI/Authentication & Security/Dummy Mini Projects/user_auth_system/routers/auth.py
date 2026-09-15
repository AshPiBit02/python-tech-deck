from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from dependencies.db_dependency import database_dependency
from schemas.user import UserRegistration,UserOut,Token,RefreshRequest
from services.user import get_user_by_email,create_user
from services.refresh_token import store_refresh_token,get_valid_refresh_token,revoke_refresh_token
from core.security import verify_password,create_access_token,create_refresh_token,decode_access_token

router=APIRouter(tags=["auth"])

@router.post("/register",response_model=UserOut)
def register(db:database_dependency,user_in: UserRegistration):
    if get_user_by_email(db,user_in.email):
        raise HTTPException(status_code=400,detail="Email already registered")

    if user_in.password!=user_in.confirm_password:
        raise HTTPException(status_code=400,detail="Password do not match")
    
    db_user=create_user(db,user_in)
    return db_user

@router.post("/token",response_model=Token)
def login(db:database_dependency,form_data:OAuth2PasswordRequestForm=Depends()):
    db_user=get_user_by_email(db,form_data.username)
    if not db_user or not verify_password(form_data.password,db_user.hashed_password):
        raise HTTPException(status_code=401,detail="Invalid email or password")

    access_token=create_access_token({"sub":str(db_user.id),"role":db_user.role.value})
    refresh_token=create_refresh_token({"sub":str(db_user.id),"role":db_user.role.value})
    store_refresh_token(db,refresh_token,db_user.id)

    return {"access_token":access_token,"refresh_token":refresh_token,"token_type":"bearer"}

@router.post("/token/refresh",response_model=Token)
def refresh_token_endpoint(body:RefreshRequest,db:database_dependency):
    payload=decode_access_token(body.refresh_token)
    if not payload or payload.get("type")!="refresh":
        raise HTTPException(status_code=401,detail="Invalid or expired token")

    db_token=get_valid_refresh_token(db,body.refresh_token)
    if not db_token:
        raise HTTPException(status_code=401,detail="Refresh token has been revoked or is unknown")

    new_access_token=create_refresh_token({"sub":payload["sub"],"role":payload["role"],"type":"access"})
    return {"access_token":new_access_token,"refresh_token":body.refresh_token,"token_type":"bearer"}

@router.post("/logout")
def logout(body:RefreshRequest,db:database_dependency):
    revoked=revoke_refresh_token(db,body.refresh_token)
    if not revoked:
        raise HTTPException(status_code=404,detail="Refresh token not found")
    return{"message":"Logged out"}