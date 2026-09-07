from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone

SECRET_KEY="dummy_secret_key"
ALGORITHM="HS256"

def create_access_token(data:dict,expries_delta:timedelta=timedelta(seconds=10))->str:
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+expries_delta
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def decode_access_token(token:str)->dict:
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {e}")

data={"sub":"dummymail23@gmail.com","user_id":"568KL"}
token=create_access_token(data)
print(token)

payload=decode_access_token(token)
print(payload)