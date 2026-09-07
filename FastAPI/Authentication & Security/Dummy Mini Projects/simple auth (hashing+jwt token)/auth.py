from passlib.context import CryptContext
from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone

SECRET_KEY="dummy_secret_key"
ALGORITHM="HS256"

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_paasword:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_paasword,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta=timedelta(seconds=60)):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+expires_delta
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def decode_access_token(token:str)->dict:
    try:
        return jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except JWTError:
        return None

