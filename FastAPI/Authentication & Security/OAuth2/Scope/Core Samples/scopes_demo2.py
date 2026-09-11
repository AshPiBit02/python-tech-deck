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
    "viewer":{"password":"pass","allowed_scopes":["notes:read"]}
}

NOTES={
    "1":"Buy electronics",
    "2":"Practice NM",
}
