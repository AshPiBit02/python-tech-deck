from jose import jwt,JWTError
from datetime import timedelta,datetime,timezone
import time

SECRET_KEY="doss-ross-teli"
ALOGORITHM="HS256"

def create_token(data:dict,expires_delts:timedelta,token_type=str)->str:
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+expires_delts
    to_encode.update({"exp":expire,"type":token_type})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALOGORITHM)

def create_access_token(data:dict)->dict:
    return create_token(data,timedelta(seconds=2),"access")

def create_refresh_token(data:dict)->dict:
    return create_token(data,timedelta(days=7),"refresh")

def decode_token(token:str)->dict:
    try:
        return jwt.decode(token,SECRET_KEY,algorithms=[ALOGORITHM])
    except JWTError:
        raise ValueError("Invalid or expired token")

def get_current_user_from_access_token(token:str)->dict:
    payload=decode_token(token)
    if payload.get("type")!="access":
        raise ValueError("This endpoint requires an access token, not a refresh token")
    return payload

def login(email:str)->dict:
    access=create_access_token({"sub":email})
    refresh=create_refresh_token({"sub":email})
    return {"access_token":access,"refresh_token":refresh,"token_type":"brearer"}

def call_protected_route(access_token:str)->str:
    payload=decode_token(access_token)
    if payload.get("type")!="access":
        raise ValueError("Wrong token type for this route")
    return f"Hello, {payload['sub']}! Access granted."

def refresh_access_token(refresh_token:str)->str:
    payload=decode_token(refresh_token)
    if payload.get("type")!="refresh":
        raise ValueError("Wrong token type for refresh")
    return create_access_token({"sub":payload["sub"]})

tokens=login("aegonVsnow@gmail.com")
print(call_protected_route(tokens["access_token"]))
time.sleep(3)

new_access_token=refresh_access_token(tokens["refresh_token"])
print(call_protected_route(new_access_token))


