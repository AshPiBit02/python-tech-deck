from core.config import settings
from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User,Role
from services.user import get_user_by_id
from core.security import decode_access_token

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db))->User:
    payload=decode_access_token(token)
    if not payload or payload.get("type")!="access":
        raise HTTPException(status_code=401,detail="Invalid or expired token")
    user_id=payload.get("sub")
    db_user=get_user_by_id(db,int(user_id))
    if not db_user:
        raise HTTPException(status_code=401,detail="User not found")
    return db_user

def require_admin(current_user:User=Depends(get_current_user))->User:
    if current_user.role!=Role.admin:
        raise HTTPException(status_code=403,detail="Access Denied")
    return current_user

def verify_admin_key(admin_key:str)->None:
    if admin_key!=settings.admin_secret_key:
        raise ValueError("Invalid admin key!")
    return None



