from fastapi import FastAPI,Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm

app=FastAPI()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

FAKE_USERS={"dummy@email.com":{"hashed_password":hash_password("secret123")}}
