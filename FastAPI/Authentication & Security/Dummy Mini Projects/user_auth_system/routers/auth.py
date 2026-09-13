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