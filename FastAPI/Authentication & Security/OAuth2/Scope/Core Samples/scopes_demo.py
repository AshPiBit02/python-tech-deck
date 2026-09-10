from fastapi import FastAPI,Depends,HTTPException,Security
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm,SecurityScopes
from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone

app=FastAPI()
SECRET_KEY="dummy"
ALGORITHM="HS256"

oauth2_scheme=OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"notes:read":"View notes","notes:write":"Create notes"},
)

FAKE_USERS={
    "viewer":{"password":"pass","allowed_scopes":["notes:read"]},
    "editor":{"password":"pass","allowed_scopes":["notes:read","notes:write"]},
}

NOTES={"1":"Buy phone"}

def create_token(username:str,scopes:list[str]):
    payload={"sub":username,"scopes":scopes,"exp":datetime.now(timezone.utc)+timedelta(minutes=30)}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

@app.post("/token")
def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user=FAKE_USERS.get(form_data.username)
    if not user or user["password"]!=form_data.password:
        raise HTTPException(status_code=401,detail="Invalid credentials")

    granted=[s for s in form_data.scopes if s in user["allowed_scopes"]]
    token=create_token(form_data.username,granted)
    return {"access_token":token,"token_type":"bearer"}

def get_current_user(security_scopes:SecurityScopes,token:str=Depends(oauth2_scheme)):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401,detail="Invalid or expired token")

    token_scopes=payload.get("scopes",[])
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(status_code=403,detail=F"Missing scope: {scope}")

    return payload["sub"]

