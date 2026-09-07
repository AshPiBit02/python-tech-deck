from jose import jwt,JWTError
from datetime import timedelta,datetime,timezone

SECRET_KEY="doss-ross-teli"
ALOGORITHM="HS256"

def create_token(data:dict,expires_delts:timedelta,token_type=str)->str:
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+expires_delts
    to_encode.update({"exp":expire,"type":token_type})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALOGORITHM)

def create_access_token(data:dict)->dict:
    return create_token(data,timedelta(minutes=15),"access")

def create_refresh_token(data:dict)->dict:
    return create_token(data,timedelta(days=7),"refresh")

def decode_token(token:str)->dict:
    try:
        return jwt.decode(token,SECRET_KEY,algorithms=[ALOGORITHM])
    except JWTError:
        raise ValueError("Invalid or expired token")

