from passlib.context import CryptContext
from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone
from core.config import settings

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_paasword:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_paasword,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta=timedelta(minutes=5)):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+expires_delta
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,settings.secret_key,algorithm=settings.algorithm)

def decode_access_token(token:str)->dict:
    try:
        return jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm])
    except JWTError:
        return None

def create_refresh_token(data:dict,expires_delta:timedelta=timedelta(days=7)):
    to_encode=data.copy()
    expires=datetime.now(timezone.utc)+expires_delta
    to_encode.update({"exp":expires})
    return jwt.encode(to_encode,settings.secret_key,algorithm=settings.algorithm)


