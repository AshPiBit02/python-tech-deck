from fastapi import FastAPI,Depends,HTTPException,Security
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm,SecurityScopes
from jose import jwt,JWTError
from datetime import datetime,timedelta,timezone

app=FastAPI()
SECRET_KEY="dummy"
ALGORITHM="HS256"

oauth2_scheme=OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "notes:read":"View notes",
        "notes:write":"Create notes",
        "notes:delete":"Delete notes",
        "notes:admin":"Full control over notes",
    },
    )

SCOPE_HIERARCHY={
    "notes:admin":["notes:read","notes:write","notes:delete"],
}

FAKE_USERS={
    "viewer":{"password":"pass","allowed_scopes":["notes:read"]},
    "boss":{"password":"pass","allowed_scopes":["notes:admin"]},
}

NOTES={
    "1":"Buy electronics",
    "2":"Practice NM",
}

def expand_scopes(scopes:list[str])->list[str]:
    expanded=set(scopes)
    for scope in scopes:
        expanded.update(SCOPE_HIERARCHY.get(scope,[]))
    return list(expanded)

def create_token(username:str,scopes:list[str]):
    payload={"sub":username,"scopes":expand_scopes(scopes),"exp":datetime.now(timezone.utc)+timedelta(minutes=30)}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

