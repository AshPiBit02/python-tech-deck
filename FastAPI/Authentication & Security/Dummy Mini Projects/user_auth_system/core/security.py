from passlib.context import CryptContext
from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone
from core.config import settings
from fastapi import HTTPException

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_paasword:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_paasword,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta=timedelta(minutes=5)):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+expires_delta
    to_encode.update({"exp":expire,"type":"access"})
    return jwt.encode(to_encode,settings.secret_key,algorithm=settings.algorithm)

def decode_access_token(token:str)->dict:
    try:
        return jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm])
    except JWTError:
        return None

def create_refresh_token(data:dict,expires_delta:timedelta=timedelta(days=7)):
    to_encode=data.copy()
    expires=datetime.now(timezone.utc)+expires_delta
    to_encode.update({"exp":expires,"type":"refresh"})
    return jwt.encode(to_encode,settings.secret_key,algorithm=settings.algorithm)

def verify_admin_key(admin_key:str)->None:
    if admin_key!=settings.admin_secret_key:
        raise ValueError("Invalid admin key!")
    return None

def verify_pin(pin:str)->None:
    if pin!=settings.pin:
        raise ValueError("Invalid PIN!")
    return None

