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

    return {"acccess_token":access_token,"refresh_token":refresh_token,"token_type":"bearer"}
