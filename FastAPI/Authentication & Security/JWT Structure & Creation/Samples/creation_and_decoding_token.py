from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone
import time

SECRET_KEY="dummy_secret_key"
ALGORITHM="HS256"

def create_access_token(data:dict,expries_delta:timedelta=timedelta(seconds=4))->str:
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+expries_delta
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def decode_access_token(token:str)->dict|None:
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"Invalid or expired token: {e}")

def tamper_access_token(token:str)->str:
    return token[:-5]+"xxxxx"

data={"sub":"dummymail23@gmail.com","user_id":"568KL"}
token=create_access_token(data)
print(token)

tampered_token=tamper_access_token(token)
# time.sleep(5)
payload=decode_access_token(tampered_token)
payload=decode_access_token(token)
print(payload)