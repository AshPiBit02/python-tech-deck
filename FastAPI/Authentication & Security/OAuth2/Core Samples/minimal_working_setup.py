from fastapi import FastAPI,Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from root_auth import hash_password,verify_password,decode_access_token,create_access_token
app=FastAPI()
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

FAKE_USERS={"dummy@gmail.com":{"hashed_password":hash_password("secret123")}}

@app.post("/token")
def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user=FAKE_USERS.get(form_data.username)
    if user is None or not verify_password(form_data.password,user["hashed_password"]):
        raise HTTPException(status_code=401,detail="Incorrect email or password")
    access_token=create_access_token({"sub":form_data.username})
    return {"access_token":access_token,"token_type":"bearer"}

@app.get("/me")
def get_me(token:str=Depends(oauth2_scheme)):
    payload=decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401,detail="Invalid or expired token")
    return {"email":payload.get("sub")}
